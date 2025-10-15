import requests
import time
import datetime
from actstream import action
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db import models
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from dirtyfields import DirtyFieldsMixin
from simo.core.models import Instance, Gateway, Component
from simo.core.utils.helpers import get_random_string
from simo.core.events import GatewayObjectCommand
from .managers import ColonelsManager, ColonelPinsManager, InterfacesManager
# Now imported from utils
from .utils import GPIO_PINS, INTERFACES_PINS_MAP, \
    _sync_interface_address_occupancy, _release_interface_addresses

# -------------------------------------------------------------------------



legacy_colonel_pins_map = {
    1: "R1", 2: "R2", 3: "R3", 4: "R4",
    5: "I1", 6: "I2", 7: "IO3", 8: "IO4",
    9: "IO5", 10: "IO6", 11: "IO7", 12: "IO8",
    13: "IO9", 14: "IO10", 15: "IO11|SCL", 16: "IO12|SDA"
}
legacy_colonel_pins_choices = [(None, '---------')] + [
    (key, val) for key, val in legacy_colonel_pins_map.items()
]


def get_new_secret():
    return get_random_string(12)


class InstanceOptions(models.Model):
    instance = models.OneToOneField(
        Instance, on_delete=models.CASCADE, related_name='fleet_options',
        limit_choices_to={'is_active': True}
    )
    secret_key = models.CharField(max_length=20, default=get_new_secret)


@receiver(post_save, sender=Instance)
def create_instance_options(sender, instance, *args, **kwargs):
    InstanceOptions.objects.get_or_create(instance=instance)


class Colonel(DirtyFieldsMixin, models.Model):
    instance = models.ForeignKey(
        'core.Instance', on_delete=models.CASCADE, related_name='colonels',
        limit_choices_to={'is_active': True}
    )
    uid = models.CharField(
        max_length=100, db_index=True, editable=False, unique=True,
    )
    name = models.CharField(max_length=100, blank=True)
    type = models.CharField(
        max_length=20, default='ample-wall',
        choices=(
            ('4-relays', "4 Relay"),
            ('ample-wall', "Ample Wall"),
            ('game-changer', "Game Changer"),
            ('game-changer-mini', "Game Changer Mini"),
            ('sentinel', "Sentinel")
        )
    )
    firmware_version = models.CharField(
        max_length=50, editable=False, null=True
    )
    minor_upgrade_available = models.CharField(
        max_length=50, editable=False, null=True
    )
    major_upgrade_available = models.CharField(
        max_length=50, editable=False, null=True
    )
    firmware_auto_update = models.BooleanField(
        default=False,
        help_text="Keeps automatically up to date with minor and patch updates. "
                  "Major upgrade requires manual upgrade initiation"
    )
    socket_connected = models.BooleanField(default=False, db_index=True)
    ble_enabled = models.BooleanField('BLE enabled', default=False)
    last_seen = models.DateTimeField(null=True, editable=False, db_index=True)
    enabled = models.BooleanField(default=False)

    components = models.ManyToManyField(Component, editable=False)
    occupied_pins = models.JSONField(default=dict, blank=True)

    logs_stream = models.BooleanField(
        default=False, help_text="ATENTION! Causes serious overhead and "
                                 "significantly degrades the lifespan of a chip "
                                 "due to a lot of writes to the memory. "                       
                                 "It also causes Colonel websocket to run out of memory "
                                 "and reset if a lot of data is being transmitted. "
                                 "Leave this off, unleess you know what you are doing!"
    )
    pwm_frequency = models.IntegerField(default=0, choices=(
        (0, "3kHz"), (1, "22kHz")
    ), help_text="Affects Ample Wall dimmer PWM output (dimmer) frequency")

    # Sentinel voice assistant specific fields
    wake_stats = models.JSONField(
        default=dict, editable=False, db_index=True
    )
    last_wake = models.DateTimeField(null=True, editable=False, db_index=True)
    is_vo_active = models.BooleanField(default=False, db_index=True)

    objects = ColonelsManager()

    def __str__(self):
        return self.name if self.name else self.uid

    def save(self, *args, **kwargs):
        if 'socket_connected' in self.get_dirty_fields() and self.socket_connected:
            for comp in self.components.all():
                comp.alive = True
                comp.save()

        if self.minor_upgrade_available and self.firmware_version == self.minor_upgrade_available:
            self.minor_upgrade_available = None
        if self.major_upgrade_available and self.firmware_version == self.major_upgrade_available:
            self.major_upgrade_available = None

        if self.is_vo_active:
            Colonel.objects.filter(
                instance=self.instance
            ).exclude(id=self.id).update(is_vo_active=False)

        return super().save(*args, **kwargs)

    @property
    def is_connected(self):
        if not self.socket_connected:
            return False
        if not self.last_seen:
            return False
        return True

    def newer_firmware_available(self):
        updates = []
        if self.major_upgrade_available:
            updates.append(self.major_upgrade_available)
        if self.minor_upgrade_available:
            updates.append(self.minor_upgrade_available)
        return ', '.join(updates)

    def check_for_upgrade(self):
        resp = requests.get(
            'https://simo.io/fleet/get-latest-version-available/', params={
                'current': self.firmware_version,
                'type': self.type,
                'instance_uid': self.instance.uid
            }
        )
        if resp.status_code != 200:
            print("Bad resonse! \n", resp.content)
            return
        self.minor_upgrade_available = resp.json().get('minor')
        self.major_upgrade_available = resp.json().get('major')
        self.save()
        return resp.json()

    def update_firmware(self, to_version):
        from .gateways import FleetGatewayHandler
        for gateway in Gateway.objects.filter(type=FleetGatewayHandler.uid):
            GatewayObjectCommand(
                gateway, self,
                command='update_firmware', to_version=to_version
            ).publish()

    def restart(self):
        from .gateways import FleetGatewayHandler
        for gateway in Gateway.objects.filter(type=FleetGatewayHandler.uid):
            GatewayObjectCommand(
                gateway, self, command='restart'
            ).publish()

    def update_config(self):
        from .gateways import FleetGatewayHandler
        for gateway in Gateway.objects.filter(type=FleetGatewayHandler.uid):
            GatewayObjectCommand(
                gateway, self, command='update_config'
            ).publish()

    @transaction.atomic
    def rebuild_occupied_pins(self):
        for pin in ColonelPin.objects.filter(colonel=self):
            pin.occupied_by_id = None
            pin.occupied_by_content_type = None
            pin.save()

        for component in self.components.all():
            try:
                pins = component.controller._get_occupied_pins()
            except:
                pins = []
            for no in pins:
                pin, new = ColonelPin.objects.get_or_create(colonel=self, no=no)
                pin.occupied_by = component
                pin.save()

        for interface in self.interfaces.all():
            if interface.pin_a:
                interface.pin_a.occupied_by = interface
                interface.pin_a.save()
            if interface.pin_b:
                interface.pin_b.occupied_by = interface
                interface.pin_b.save()


    def move_to(self, other_colonel):
        self.restart()
        other_colonel.restart()
        time.sleep(1)
        self.uid = other_colonel.uid
        other_colonel.delete()
        self.save()


class ColonelPin(models.Model):
    colonel = models.ForeignKey(
        Colonel, related_name='pins', on_delete=models.CASCADE
    )
    no = models.PositiveIntegerField(db_index=True)
    label = models.CharField(db_index=True, max_length=200)
    input = models.BooleanField(default=False, db_index=True)
    output = models.BooleanField(default=False, db_index=True)
    capacitive = models.BooleanField(default=False, db_index=True)
    adc = models.BooleanField(default=False)
    native = models.BooleanField(default=True, db_index=True)
    interface = models.PositiveIntegerField(null=True, blank=True)
    default_pull = models.CharField(
        max_length=50, db_index=True, null=True, blank=True,
        choices=(('LOW', "LOW"), ("HIGH", "HIGH"))
    )
    note = models.CharField(max_length=100)
    occupied_by_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True
    )
    occupied_by_id = models.PositiveIntegerField(null=True)
    occupied_by = GenericForeignKey(
        "occupied_by_content_type", "occupied_by_id"
    )

    objects = ColonelPinsManager()

    class Meta:
        unique_together = 'colonel', 'no'
        ordering = 'colonel', 'no'
        indexes = [
            models.Index(
                fields=["occupied_by_content_type", "occupied_by_id"]
            ),
        ]
    def __str__(self):
        if not self.label:
            # Might be created via migration...
            self.save()
        if self.interface:
            interface = Interface.objects.filter(
                colonel=self.colonel, no=self.interface
            ).first()
            if interface and interface.type:
                return f"{self.label} - {interface.get_type_display()}"
        return self.label

    def save(self, *args, **kwargs):
        if self.native:
            self.label = f'GPIO{self.no}'
        else:
            no = self.no - 100
            self.label = f'IO{no}'
        if self.note:
            self.label += ' | %s' % self.note
        return super().save(*args, **kwargs)


@receiver(post_save, sender=Colonel)
def after_colonel_save(sender, instance, created, *args, **kwargs):
    if created:
        for no, data in GPIO_PINS.get(instance.type, {}).items():
            ColonelPin.objects.get_or_create(
                colonel=instance, no=no,
                defaults={
                    'input': data.get('input'), 'output': data.get('output'),
                    'capacitive': data.get('capacitive'), 'adc': data.get('adc'),
                    'native': data.get('native'), 'note': data.get('note'),
                    'interface': data.get('interface')
                }
            )
        fleet_gateway, new = Gateway.objects.get_or_create(
            type='simo.fleet.gateways.FleetGatewayHandler'
        )
        if fleet_gateway.status != 'running':
            fleet_gateway.start()

    if 'socket_connected' in instance.get_dirty_fields():
        if instance.socket_connected:
            verb = 'connected'
        else:
            verb = 'disconnected'
        action.send(
            instance, target=instance, verb=verb,
            instance_id=instance.instance.id,
            action_type='colonel_status', value=verb
        )


@receiver(post_save, sender=Component)
def post_component_save(sender, instance, created, *args, **kwargs):
    if not instance.controller_uid.startswith('simo.fleet'):
        return
    if 'config' not in instance.get_dirty_fields():
        return
    colonel = Colonel.objects.filter(id=instance.config.get('colonel', 0)).first()
    if not colonel:
        return
    colonel.components.add(instance)

    # ------------------------------------------------------------------
    # InterfaceAddress occupancy sync (always run for fleet components)
    # ------------------------------------------------------------------
    try:
        _sync_interface_address_occupancy(instance)
    except ValidationError:
        raise

    from .controllers import (
        TTLock, DALILamp, DALIGearGroup, DALIRelay, DALIOccupancySensor,
        DALILightSensor, DALIButton,
        AirQualitySensor, TempHumSensor, AmbientLightSensor,
        RoomPresenceSensor, RoomZonePresenceSensor
    )
    if instance.controller and instance.controller_cls in (
        TTLock, DALILamp, DALIGearGroup, DALIRelay, DALIOccupancySensor,
        DALILightSensor, DALIButton,
        AirQualitySensor, TempHumSensor, AmbientLightSensor,
        RoomPresenceSensor, RoomZonePresenceSensor
    ):
        return
    colonel.rebuild_occupied_pins()
    colonel.save()
    colonel.update_config()



@receiver(pre_delete, sender=Component)
def post_component_delete(sender, instance, *args, **kwargs):
    if not instance.controller_uid.startswith('simo.fleet'):
        # Still ensure we release any InterfaceAddress occupied by this
        # component to avoid dangling references.
        _release_interface_addresses(instance)
        return

    from .controllers import DALIGearGroup
    if instance.controller_uid == DALIGearGroup.uid:
        for comp in Component.objects.filter(
            id__in=instance.config.get('members', [])
        ):
            instance.controller._modify_member_group(
                comp, instance.config.get('da', 0), remove=True
            )

    elif instance.controller and instance.controller.family == 'dali':
        colonel = Colonel.objects.filter(id=instance.config['colonel']).first()
        if colonel:
            GatewayObjectCommand(
                instance.gateway, colonel, id=instance.id,
                command='call', method='destroy',
            ).publish()

    else:

        affected_colonels = list(Colonel.objects.filter(components=instance))

        def update_colonel():
            for colonel in affected_colonels:
                print("Rebuild occupied pins for :", colonel)
                colonel.rebuild_occupied_pins()
                colonel.update_config()

        transaction.on_commit(update_colonel)

    # Finally release any InterfaceAddress rows occupied by this component
    _release_interface_addresses(instance)


class Interface(models.Model):
    colonel = models.ForeignKey(
        Colonel, on_delete=models.CASCADE, related_name='interfaces'
    )
    no = models.PositiveIntegerField(choices=((1, "1"), (2, "2")))
    type = models.CharField(
        max_length=20, choices=(('i2c', "I2C"), ('dali', "DALI")),
        null=True, blank=True
    )
    pin_a = models.ForeignKey(
        ColonelPin, on_delete=models.CASCADE, limit_choices_to={
            'native': True, 'output': True,
        }, verbose_name="Pin A (scl)", null=True, related_name='interface_a',
        editable=False
    )
    pin_b = models.ForeignKey(
        ColonelPin, on_delete=models.CASCADE, limit_choices_to={
            'native': True, 'output': True,
        }, verbose_name="Pin B (sda)", null=True, related_name='interface_b',
        editable=False
    )

    objects = InterfacesManager()

    class Meta:
        unique_together = 'colonel', 'no'

    def __str__(self):
        return f"{self.no} - {self.get_type_display()}"

    def save(self, *args, **kwargs):
        if not self.pin_a:
            self.pin_a = ColonelPin.objects.get(
                colonel=self.colonel,
                no=INTERFACES_PINS_MAP[self.no][0],
            )
        if not self.pin_b:
            self.pin_b = ColonelPin.objects.get(
                colonel=self.colonel,
                no=INTERFACES_PINS_MAP[self.no][1],
            )

        with transaction.atomic():
            created = self.pk is None
            super_save = super().save  # keep lint happy
            retval = super_save(*args, **kwargs)

            pins = list(
                ColonelPin.objects.select_for_update().filter(
                    colonel=self.colonel,
                    no__in=INTERFACES_PINS_MAP[self.no],
                )
            )

            if self.type:  # claim the pins
                for pin in pins:
                    # If already occupied by another object – abort.
                    if pin.occupied_by and pin.occupied_by != self:
                        raise ValidationError(
                            f"Interface cannot claim {pin}. Currently "
                            f"occupied by {pin.occupied_by}.",
                        )
                    pin.occupied_by = self
                ColonelPin.objects.bulk_update(
                    pins, ["occupied_by_content_type", "occupied_by_id"]
                )
            else:  # release them if *we* were occupying
                for pin in pins:
                    if pin.occupied_by == self:
                        pin.occupied_by = None
                ColonelPin.objects.bulk_update(
                    pins, ["occupied_by_content_type", "occupied_by_id"]
                )

        return retval

    def broadcast_reset(self):
        from .gateways import FleetGatewayHandler
        gw = Gateway.objects.filter(type=FleetGatewayHandler.uid).first()
        if not gw:
            return
        GatewayObjectCommand(
            gw, self.colonel, command='broadcast_reset',
            data={'interface': self.no}
        ).publish()


class InterfaceAddress(models.Model):
    interface = models.ForeignKey(
        Interface, related_name='addresses', on_delete=models.CASCADE
    )
    address_type = models.CharField(
        db_index=True, max_length=100, choices=(
            ('i2c', "I2C"),
            ('dali-gear', "DALI Gear"),
            ('dali-group', "DALI Gear Group"),
            ('dali-device', "DALI Control Device"),
        )
    )
    address = models.JSONField(db_index=True)
    occupied_by_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True
    )
    occupied_by_id = models.PositiveIntegerField(null=True)
    occupied_by = GenericForeignKey(
        "occupied_by_content_type", "occupied_by_id"
    )

    class Meta:
        unique_together = 'interface', 'address_type', 'address'

    def __str__(self):
        addr = self.address
        if self.address_type == 'i2c':
            try:
                addr = hex(int(self.address))
            except:
                pass
        return f"{self.get_address_type_display()}: {addr}"


@receiver(post_save, sender=Interface)
def post_interface_save(sender, instance, created, *args, **kwargs):
    if instance.type == 'i2c':
        InterfaceAddress.objects.filter(
            interface=instance
        ).exclude(address_type='i2c').delete()
        for addr in range(128):
            InterfaceAddress.objects.get_or_create(
                interface=instance, address_type='i2c',
                address=addr,
            )
    elif instance.type == 'dali':
        InterfaceAddress.objects.filter(
            interface=instance
        ).exclude(
            address_type__in=('dali-gear', 'dali-group', 'dali-device')
        ).delete()
        for addr in range(64):
            InterfaceAddress.objects.get_or_create(
                interface=instance, address_type='dali-gear',
                address=addr,
            )
        for addr in range(16):
            InterfaceAddress.objects.get_or_create(
                interface=instance, address_type='dali-group',
                address=addr,
            )
    else:
        InterfaceAddress.objects.filter(interface=instance).delete()

    try:
        instance.colonel.update_config()
    except Exception:
        # Fail silently – configuration push should not prevent saving.
        pass



@receiver(post_delete, sender=Interface)
def post_interface_delete(sender, instance, *args, **kwargs):
    """Release GPIO pins that were occupied by the removed Interface."""
    with transaction.atomic():
        ct = ContentType.objects.get_for_model(instance)
        pins = list(
            ColonelPin.objects.select_for_update().filter(
                occupied_by_content_type=ct,
                occupied_by_id=instance.id,
            )
        )

        for pin in pins:
            pin.occupied_by = None

        if pins:
            ColonelPin.objects.bulk_update(
                pins, ["occupied_by_content_type", "occupied_by_id"]
            )
