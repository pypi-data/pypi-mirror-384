import os
import shutil
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from actstream import action
from simo.users.models import PermissionsRole
from .models import (
    Instance, Gateway, Component, Icon, Zone, Category, PublicFile, PrivateFile
)


@receiver(post_save, sender=Instance)
def create_instance_defaults(sender, instance, created, **kwargs):
    if not created:
        return

    from simo.users.utils import get_current_user
    actor = get_current_user()
    action.send(
        actor, target=instance, verb="instance created",
        instance_id=instance.id,
        action_type='management_event'
    )

    # Create default zones

    for zone_name in (
        'Living Room', 'Kitchen', 'Bathroom', 'Porch', 'Garage', 'Yard',
    ):
        Zone.objects.create(instance=instance, name=zone_name)

    other_zone = Zone.objects.create(instance=instance, name='Other')

    core_dir_path = os.path.dirname(os.path.realpath(__file__))
    imgs_folder = os.path.join(
        core_dir_path, 'static/defaults/category_headers'
    )

    categories_media_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
    if not os.path.exists(categories_media_dir):
        os.makedirs(categories_media_dir)

    # Create default categories
    climate_category = None
    other_category = None
    for i, data in enumerate([
        ("All", 'star'), ("Climate", 'temperature-half'),
        ("Lights", 'lightbulb'), ("Security", 'eye'),
        ("Watering", 'faucet'), ("Other", 'flag-pennant')
    ]):
        shutil.copy(
            os.path.join(imgs_folder, "%s.jpg" % data[0].lower()),
            os.path.join(
                settings.MEDIA_ROOT, 'categories', "%s.jpg" % data[0].lower()
            )
        )
        cat = Category.objects.create(
            instance=instance,
            name=data[0], icon=Icon.objects.get(slug=data[1]),
            all=i == 0, header_image=os.path.join(
                'categories', "%s.jpg" % data[0].lower()
            ), order=i + 10
        )
        if cat.name == 'Climate':
            climate_category = cat
        if cat.name == 'Other':
            other_category = cat

    # Create generic gateway and components

    generic, new = Gateway.objects.get_or_create(
        type='simo.generic.gateways.GenericGatewayHandler'
    )
    dummy, new = Gateway.objects.get_or_create(
        type='simo.generic.gateways.DummyGatewayHandler'
    )
    automation, new = Gateway.objects.get_or_create(
        type='simo.automation.gateways.AutomationsGatewayHandler'
    )
    weather_icon = Icon.objects.get(slug='cloud-bolt-sun')

    from simo.generic.controllers import Weather, MainState
    Component.objects.create(
        name='Weather', icon=weather_icon,
        zone=other_zone,
        category=climate_category,
        gateway=generic, base_type='weather',
        controller_uid=Weather.uid,
        config={'is_main': True}
    )

    Component.objects.create(
        name='Main State', icon=Icon.objects.get(slug='home'),
        zone=other_zone,
        category=other_category,
        gateway=generic, base_type=MainState.base_type,
        controller_uid=MainState.uid,
        value='day',
        config=MainState.default_config
    )

    # Create default User permission roles

    PermissionsRole.objects.create(
        instance=instance, name="Admin", is_owner=True, is_superuser=True,
        can_manage_users = True
    )
    PermissionsRole.objects.create(
        instance=instance, name="Owner",
        is_owner=True, is_default=True, can_manage_users=True
    )
    PermissionsRole.objects.create(
        instance=instance, name="Guest", is_owner=False
    )
    generic.start()
    dummy.start()


@receiver(post_save, sender=Zone)
@receiver(post_save, sender=Category)
def post_save_actions_dispatcher(sender, instance, created, **kwargs):
    from simo.users.utils import get_current_user
    actor = get_current_user()
    if created:
        verb = 'created'
    else:
        verb = 'modified'
    action.send(
        actor, target=instance, verb=verb,
        instance_id=instance.instance.id,
        action_type='management_event'
    )


@receiver(post_save, sender=Component)
@receiver(post_save, sender=Gateway)
def post_save_change_events(sender, instance, created, **kwargs):
    target = instance
    from .events import ObjectChangeEvent
    dirty_fields = target.get_dirty_fields()
    for ignore_field in (
        'change_init_by', 'change_init_date', 'change_init_to', 'last_update'
    ):
        dirty_fields.pop(ignore_field, None)

    def post_update():
        if not dirty_fields:
            return

        if type(target) == Gateway:
            ObjectChangeEvent(
                None, target,
                dirty_fields=dirty_fields,
            ).publish()
        elif type(target) == Component:
            data = {}
            for field_name in (
                'value', 'last_change', 'arm_status',
                'battery_level', 'alive', 'meta'
            ):
                data[field_name] = getattr(target, field_name, None)
            ObjectChangeEvent(
                target.zone.instance, target,
                dirty_fields=dirty_fields,
                actor=getattr(target, 'change_actor', None),
                **data
            ).publish()
            for master in target.masters.all():
                data = {}
                for field_name in (
                    'value', 'last_change', 'arm_status',
                    'battery_level', 'alive', 'meta'
                ):
                    data[field_name] = getattr(master, field_name, None)
                ObjectChangeEvent(
                    master.zone.instance,
                    master, slave_id=target.id,
                    **data
                ).publish()

    transaction.on_commit(post_update)

    if created and isinstance(instance, Component):
        def clear_api_cache():
            cache.delete(f"main-components-{instance.zone.instance.id}")
            from simo.users.models import User
            for user in User.objects.all():
                role_cache_key = f'user-{user.id}_instance-' \
                                 f'{instance.zone.instance.id}_role'
                cache.delete(role_cache_key)
        transaction.on_commit(clear_api_cache)


@receiver(post_save, sender=Gateway)
def gateway_post_save(sender, instance, created, *args, **kwargs):
    def start_gw():
        if created:
            gw = Gateway.objects.get(pk=instance.pk)
            gw.start()

    transaction.on_commit(start_gw)


@receiver(post_delete, sender=Gateway)
def gateway_post_delete(sender, instance, *args, **kwargs):
    instance.stop()


@receiver(post_delete, sender=PublicFile)
@receiver(post_delete, sender=PrivateFile)
def delete_file_itself(sender, instance, *args, **kwargs):
    try:
        os.remove(instance.file.path)
    except:
        pass