import time
import datetime
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import formset_factory
from django.urls.base import get_script_prefix
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from dal import forward
from simo.core.models import Component, Category
from simo.core.forms import (
    BaseComponentForm, ValueLimitForm, NumericSensorForm
)
from simo.core.utils.formsets import FormsetField
from simo.core.utils.converters import input_to_meters
from simo.core.widgets import LogOutputWidget
from simo.core.utils.easing import EASING_CHOICES
from simo.core.utils.validators import validate_slaves
from simo.core.utils.admin import AdminFormActionForm
from simo.core.events import GatewayObjectCommand
from simo.core.middleware import get_current_instance
from simo.core.form_fields import (
    Select2ModelChoiceField, Select2ListChoiceField,
    Select2ModelMultipleChoiceField
)
from simo.core.form_fields import PlainLocationField
from simo.users.models import PermissionsRole
from .models import Colonel, ColonelPin, Interface
from .utils import INTERFACES_PINS_MAP, get_all_control_input_choices


class ColonelPinChoiceField(forms.ModelChoiceField):
    '''
    Required for API, so that SIMO app could properly handle
    fleet components configuration.
    '''
    filter_by = 'colonel'


class ColonelInterfacesChoiceField(forms.ModelChoiceField):
    filter_by = 'colonel'



class ColonelAdminForm(forms.ModelForm):
    log = forms.CharField(
        widget=forms.HiddenInput, required=False
    )

    class Meta:
        model = Colonel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            prefix = get_script_prefix()
            if prefix == '/':
                prefix = ''
            self.fields['log'].widget = LogOutputWidget(
                prefix + '/ws/log/%d/%d/' % (
                    ContentType.objects.get_for_model(Colonel).id,
                    self.instance.id
                )
            )


class MoveColonelForm(AdminFormActionForm):
    colonel = forms.ModelChoiceField(
        label="Move to:", queryset=Colonel.objects.filter(components=None),
    )


class InterfaceAdminForm(forms.ModelForm):

    class Meta:
        model = Interface
        fields = '__all__'

    def clean(self):
        if self.instance.pk:
            return self.cleaned_data

        for pin_no in INTERFACES_PINS_MAP[self.cleaned_data['no']]:
            cpin = ColonelPin.objects.get(
                colonel=self.instance.colonel, no=pin_no
            )
            if cpin.occupied_by:
                raise forms.ValidationError(
                    f"Interface can not be created, because "
                    f"GPIO{cpin} is already occupied by {cpin.occupied_by}."
                )


class ColonelComponentForm(BaseComponentForm):
    colonel = Select2ModelChoiceField(
        label="Colonel", queryset=Colonel.objects.all(),
        url='autocomplete-colonels',
    )

    def clean_colonel(self):
        if not self.instance.pk:
            return self.cleaned_data['colonel']
        colonel = self.cleaned_data.get('colonel')
        if not colonel:
            return
        org = self.instance.config.get('colonel')
        if org and org != colonel.id:
            raise forms.ValidationError(
                "Changing colonel after component is created "
                "it is not allowed!"
            )
        return colonel

    def _clean_pin(self, field_name):
        if self.cleaned_data[field_name].colonel != self.cleaned_data['colonel']:
            self.add_error(
                field_name, "Pin must be from the same Colonel!"
            )
            return
        if self.cleaned_data[field_name].occupied_by \
        and self.cleaned_data[field_name].occupied_by != self.instance:
            self.add_error(
                field_name,
                f"Pin is already occupied by {self.cleaned_data[field_name].occupied_by}!"
            )

    def _clean_controls(self):
        # TODO: Formset factory should return proper field value types instead of str type

        pin_instances = {}
        for i, control in enumerate(self.cleaned_data['controls']):
            updated_vals = {}
            for key, val in control.items():
                updated_vals[key] = val
                if key == 'input':
                    if val.startswith('pin'):
                        pin = ColonelPin.objects.get(
                            id=int(self.cleaned_data['controls'][i]['input'][4:])
                        )
                        pin_instances[i] = pin
                        updated_vals['pin_no'] = pin.no
                    elif val.startswith('button'):
                        updated_vals['button'] = int(
                            self.cleaned_data['controls'][i]['input'][7:]
                        )
                elif key == 'touch_threshold':
                    updated_vals[key] = int(val)
            self.cleaned_data['controls'][i] = updated_vals

        pins_in_use = []
        formset_errors = {}
        for i, control in enumerate(self.cleaned_data['controls']):
            if not control['input'].startswith('pin'):
                continue
            if pin_instances[i].colonel != self.cleaned_data['colonel']:
                formset_errors[i] = {
                    'input': f"{pin_instances[i]} must be from the same Colonel!"
                }
            elif pin_instances[i].occupied_by \
            and pin_instances[i].occupied_by != self.instance:
                formset_errors[i] = {
                    'pin': f"{pin_instances[i]} is already occupied by {pin_instances[i].occupied_by}!"
                }
            elif pin_instances[i].no in pins_in_use:
                formset_errors[i] = {
                    'pin': f"{pin_instances[i].no} is already in use!"
                }
            pins_in_use.append(pin_instances[i].no)

        errors_list = []
        if formset_errors:
            for i, control in enumerate(self.cleaned_data['controls']):
                errors_list.append(formset_errors.get(i, {}))
        if errors_list:
            self._errors['controls'] = errors_list
            if 'controls' in self.cleaned_data:
                del self.cleaned_data['controls']


class ControlForm(forms.Form):
    input = Select2ListChoiceField(
        choices=get_all_control_input_choices,
        url='autocomplete-control_inputs', forward=[
            forward.Self(), forward.Field('colonel'),
            forward.Const({'input': True}, 'pin_filters')
        ]
    )
    method = forms.ChoiceField(
        label="Button type",
        required=True, choices=(
            ('momentary', "Momentary"), ('toggle', "Toggle"),
        ),
    )
    action_method = forms.ChoiceField(
        label="Action method (if Momentary)", initial='down',
        choices=(
            ('down', "DOWN (On GND delivery)"),
            ('up', "UP (On +5V delivery)")
        )
    )

    prefix = 'controls'


class ColonelBinarySensorConfigForm(ColonelComponentForm):
    pin = Select2ModelChoiceField(
        label='Port',
        queryset=ColonelPin.objects.filter(input=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'input': True}, 'filters')
        ]
    )
    inverse = forms.TypedChoiceField(
        choices=((1, "Yes"), (0, "No")), coerce=int, initial=1,
        help_text="Hint: Set inverse to Yes, to get ON signal when "
                  "you deliver GND to the input and OFF when you cut it out."
    )
    debounce = forms.IntegerField(
        min_value=0, max_value=1000 * 60 * 60, required=False, initial=50,
        help_text="Some sensors are unstable and quickly transition "
                  "between ON/OFF states when engaged. <br>"
                  "Set debounce value in milliseconds, to remediate this. "
                  "50ms offers a good starting point!"
    )
    hold_time = forms.TypedChoiceField(
        initial=0, coerce=int, choices=(
            (0, "-----"),
            (1, "10 s"), (2, "20 s"), (3, "30 s"), (4, "40 s"), (5, "50 s"),
            (6, "1 min"), (9, "1.5 min"), (12, "2 min"), (18, "3 min"),
            (30, "5 min"), (60, "10 min"), (120, "20 min"),
        ), required=False,
        help_text="Holds positive value for given amount of time "
                  "after last negative value has been observed. "
                  "Super useful with regular motion detectors for controlling "
                  "lights or other means of automation."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basic_fields.append('hold_time')

    def clean(self):
        super().clean()
        if 'colonel' not in self.cleaned_data:
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data

        self._clean_pin('pin')

        if self.cleaned_data['pin'].no > 100:
            if self.cleaned_data['pin'].no < 126:
                if self.cleaned_data.get('pull') == 'HIGH':
                    self.add_error(
                        'pull',
                        "Sorry, but this pin is already pulled LOW and "
                        "it can not be changed by this setting. "
                        "Please use 5kohm resistor to physically pull it HIGH "
                        "if that's what you want to do."
                    )
            else:
                if self.cleaned_data.get('pull') == 'LOW':
                    self.add_error(
                        'pull',
                        "Sorry, but this pin is already pulled HIGH and "
                        "it can not be changed by this setting. "
                        "Please use 5kohm resistor to physically pull it LOW "
                        "if that's what you want to do."
                    )

        elif self.cleaned_data.get('pull') != 'FLOATING':
            if not self.cleaned_data['pin'].output:
                self.add_error(
                    'pin',
                    f"Sorry, but {self.cleaned_data['pin']} "
                    f"does not have internal pull HIGH/LOW"
                    " resistance capability"
                )

        return self.cleaned_data

    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)


class ColonelButtonConfigForm(ColonelComponentForm):
    pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(input=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'input': True}, 'filters')
        ]
    )
    action_method = forms.ChoiceField(
        label="Action method", initial='down',
        choices=(
            ('down', "DOWN (On GND delivery)"),
            ('up', "UP (On +5V delivery)")
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if 'colonel' not in self.cleaned_data:
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data
        self._clean_pin('pin')
        return self.cleaned_data

    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)


class ColonelNumericSensorConfigForm(ColonelComponentForm, NumericSensorForm):
    pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(adc=True, input=True, native=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const(
                {'adc': True, 'native': True, 'input': True}, 'filters'
            )
        ]
    )
    attenuation = forms.TypedChoiceField(
        initial=0, coerce=int, choices=(
            (0, "Max 1v"), (2, "Max 1.34v"), (6, "Max 2v"), (11, "Max 3.6v")
        )
    )
    read_frequency_s = forms.FloatField(
        initial=60, min_value=1, max_value=60*60*24,
        help_text='read input value every s'
    )
    change_report = forms.FloatField(
        initial=0.2,
        help_text='consider value as changed if it changes this much'
    )

    limits = FormsetField(
        formset_factory(
            ValueLimitForm, can_delete=True, can_order=True, extra=0, max_num=3
        )
    )

    def clean(self):
        super().clean()
        if 'colonel' not in self.cleaned_data:
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data

        self._clean_pin('pin')

        return self.cleaned_data


    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)


class DS18B20SensorConfigForm(ColonelComponentForm, NumericSensorForm):
    pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(input=True, native=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const(
                {'native': True, 'input': True}, 'filters'
            )
        ]
    )
    read_frequency_s = forms.IntegerField(
        initial=60, min_value=1, max_value=60*60*24,
        help_text='read and  report temperature value every s. '
                              'Can not be less than 1s.'
    )


    def clean(self):
        super().clean()
        if 'colonel' not in self.cleaned_data:
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data

        self._clean_pin('pin')

        return self.cleaned_data

    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)



class ColonelDHTSensorConfigForm(ColonelComponentForm):
    pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(input=True, native=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const(
                {'native': True, 'input': True}, 'filters'
            )
        ]
    )
    sensor_type = forms.TypedChoiceField(
        initial=11, coerce=int, choices=(
            (11, "DHT11"), (22, "DHT22"),
        )
    )
    temperature_units = forms.ChoiceField(
        label="Sensor temperature units",
        choices=(('C', "Celsius"), ('F', "Fahrenheit"))
    )
    read_frequency_s = forms.IntegerField(
        initial=60, min_value=1, max_value=60*60*24,
        help_text='read and  report climate value every s. '
                              'Can not be less than 1s.'
    )

    def clean(self):
        super().clean()
        if not self.cleaned_data.get('colonel'):
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data

        self._clean_pin('pin')

        return self.cleaned_data

    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)


class I2CDevice(ColonelComponentForm):
    interface_port = Select2ModelChoiceField(
        label="Interface",
        queryset=ColonelPin.objects.filter(interface__isnull=False),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'interface__isnull': False}, 'filters'),
        ],
    )

    def clean(self):
        cleaned_data = super().clean()
        colonel = cleaned_data.get('colonel')
        port_choice = cleaned_data.get('interface_port')
        if not colonel or not port_choice:
            return cleaned_data

        # Create or fetch the I²C interface
        interface, created = Interface.objects.get_or_create(
            colonel=colonel,
            no=port_choice.interface,
            defaults={'type': 'i2c'},
        )

        # If it already existed as something else, ensure it's free
        if interface.type != 'i2c':
            occupied = interface.addresses.filter(occupied_by__isnull=False).first()
            if occupied:
                self.add_error(
                    'interface_port',
                    f"Port already occupied by {occupied.occupied_by}"
                )
                return cleaned_data
            interface.type = 'i2c'
            interface.save()

        # Check for address collisions on that interface
        other = Component.objects.filter(
            config__colonel=colonel.id,
            config__interface=interface.id,
            config__i2c_address=cleaned_data['i2c_address'],
        ).exclude(id=self.instance.id).first()
        if other:
            self.add_error(
                'i2c_address',
                f"Address already occupied by {other}"
            )

        # stash for save()
        cleaned_data['i2c_interface'] = interface.id
        return cleaned_data

    def save(self, commit=True):
        self.instance.config['i2c_interface'] = self.cleaned_data['i2c_interface']
        return super().save(commit=commit)


class BME680SensorConfigForm(I2CDevice):
    i2c_address = forms.TypedChoiceField(
        coerce=int,
        initial=119,  # match “0x77 – default”
        choices=(
            (119, "0x77 – default"),
            (118, "0x76 – soldered"),
        ),
    )
    read_frequency_s = forms.IntegerField(
        initial=60,
        min_value=1,
        max_value=60 * 60 * 24,
        help_text=(
            "Read and report climate value every second. "
            "Cannot be less than 1 second."
        ),
    )


class MCP9808SensorConfigForm(I2CDevice):
    i2c_address = forms.TypedChoiceField(
        coerce=int, initial=24,
        choices=(
            (24, "Default"),
            (25, "AD0"), (26, "AD1"), (28, "AD2"),
            (27, "AD0 + AD1"), (29, "AD0 + AD2"), (30, "AD1 + AD2"),
            (31, "AD0 + AD1 + AD2")
        ),
    )
    read_frequency_s = forms.IntegerField(
        initial=60, min_value=1, max_value=60 * 60 * 24,
        help_text='read and report temperature value every s. '
                  'Can not be less than 1s.'

    )


class ENS160SensorConfigForm(I2CDevice):
    i2c_address = forms.TypedChoiceField(
        coerce=int, initial=83,
        choices=((82, "0x52"), (83, "0x53")),
    )
    read_frequency_s = forms.IntegerField(
        initial=10, min_value=1, max_value=60 * 60 * 24,
        help_text='read and report air quality values every s. '
                  'Can not be less than 1s.'

    )


class ColonelTouchSensorConfigForm(ColonelComponentForm):
    pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(input=True, capacitive=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'input': True, 'capacitive': True}, 'filters')
        ]
    )
    threshold = forms.IntegerField(
        min_value=0, max_value=999999999, required=False, initial=1000,
        help_text="Used to detect touch events. "
                  "Smaller value means a higher sensitivity. "
                  "1000 offers good starting point."

    )
    inverse = forms.ChoiceField(choices=((0, "No"), (1, "Yes")))

    def clean(self):
        super().clean()
        if 'colonel' not in self.cleaned_data:
            return self.cleaned_data
        if 'pin' not in self.cleaned_data:
            return self.cleaned_data

        self._clean_pin('pin')

        return self.cleaned_data


    def save(self, commit=True):
        if 'pin' in self.cleaned_data:
            self.instance.config['pin_no'] = self.cleaned_data['pin'].no
        return super().save(commit=commit)


class ColonelSwitchConfigForm(ColonelComponentForm):
    output_pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    auto_off = forms.FloatField(
        required=False, min_value=0.01, max_value=1000000000,
        help_text="If provided, switch will be turned off after "
                  "given amount of seconds after every turn on event."
    )
    inverse = forms.BooleanField(required=False)
    slaves = Select2ModelMultipleChoiceField(
        queryset=Component.objects.filter(
            base_type__in=(
                'dimmer', 'switch', 'blinds', 'script'
            )
        ),
        url='autocomplete-component',
        forward=[
            forward.Const(['dimmer', 'switch', 'blinds', 'script'], 'base_type')
        ], required=False
    )

    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=10
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basic_fields.append('auto_off')
        if self.instance.pk and 'slaves' in self.fields:
            self.fields['slaves'].initial = self.instance.slaves.all()

    def clean_slaves(self):
        if 'slaves' not in self.cleaned_data:
            return
        if not self.cleaned_data['slaves'] or not self.instance:
            return self.cleaned_data['slaves']
        return validate_slaves(self.cleaned_data['slaves'], self.instance)

    def clean(self):
        super().clean()

        if self.cleaned_data.get('output_pin'):
            self._clean_pin('output_pin')
        if self.cleaned_data.get('controls'):
            self._clean_controls()

        if self.cleaned_data.get('output_pin') and self.cleaned_data.get('controls'):
            for ctrl in self.cleaned_data['controls']:
                if not ctrl['input'].startswith('pin'):
                    continue
                if int(ctrl['input'][4:]) == self.cleaned_data['output_pin'].id:
                    self.add_error(
                        "output_pin",
                        "Can't be used as control pin at the same time!"
                    )

        return self.cleaned_data

    def save(self, commit=True):
        if 'output_pin' in self.cleaned_data:
            self.instance.config['output_pin_no'] = self.cleaned_data['output_pin'].no
        obj = super().save(commit=commit)
        if commit and 'slaves' in self.cleaned_data:
            obj.slaves.set(self.cleaned_data['slaves'])
        if commit and self.cleaned_data.get('controls'):
            GatewayObjectCommand(
                self.instance.gateway, obj, command='watch_buttons'
            ).publish()
        return obj


class PWMOutputBaseConfig(ColonelComponentForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'value_units' in self.fields:
            self.fields['value_units'].initial = self.controller.default_value_units
        self.basic_fields.extend(
            ['value_units', 'turn_on_time', 'turn_off_time', 'skew']
        )
        if self.instance.pk and 'slaves' in self.fields:
            self.fields['slaves'].initial = self.instance.slaves.all()

    def clean_slaves(self):
        if not self.cleaned_data['slaves'] or not self.instance:
            return self.cleaned_data['slaves']
        return validate_slaves(self.cleaned_data['slaves'], self.instance)

    def clean(self):
        super().clean()
        if 'output_pin' in self.cleaned_data:
            self._clean_pin('output_pin')
        if 'controls' in self.cleaned_data:
            self._clean_controls()

        if self.cleaned_data.get('output_pin') and self.cleaned_data.get('controls'):
            for ctrl in self.cleaned_data['controls']:
                if not ctrl['input'].startswith('pin'):
                    continue
                if int(ctrl['input'][4:]) == self.cleaned_data['output_pin'].id:
                    self.add_error(
                        "output_pin",
                        "Can't be used as control pin at the same time!"
                    )
        return self.cleaned_data


    def save(self, commit=True):
        if 'output_pin' in self.cleaned_data:
            self.instance.config['output_pin_no'] = self.cleaned_data['output_pin'].no

        update_colonel = False
        if not self.instance.pk:
            update_colonel = True
        elif 'output_pin' in self.changed_data:
            update_colonel = True
        elif 'slaves' in self.changed_data:
            update_colonel = True
        if not update_colonel:
            old = Component.objects.get(id=self.instance.id)
            if old.config.get('controls') != self.cleaned_data.get('controls'):
                update_colonel = True

        obj = super().save(commit=commit)
        if commit and 'slaves' in self.cleaned_data:
            obj.slaves.set(self.cleaned_data['slaves'])
        if not update_colonel:
            GatewayObjectCommand(
                obj.gateway, self.cleaned_data['colonel'], id=obj.id,
                command='call', method='update_config', args=[
                    obj.controller._get_colonel_config()
                ]
            ).publish()
        if commit and self.cleaned_data.get('controls'):
            GatewayObjectCommand(
                self.instance.gateway, obj, command='watch_buttons'
            ).publish()
        return obj

class ColonelPWMOutputConfigForm(PWMOutputBaseConfig):
    output_pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    min = forms.FloatField(
        required=True, initial=0,
        help_text="Minimum component value"
    )
    max = forms.FloatField(
        required=True, initial=100,
        help_text="Maximum component value"
    )
    value_units = forms.CharField(required=False)

    device_min = forms.IntegerField(
        label="Device minimum (%).",
        help_text="Device will turn off once it reaches this internal value. "
                  "Usually it is a good idea to "                  
                  "set this somewhere in between of 5 - 15 %. ",
        initial=10, min_value=0, max_value=100,
    )
    device_max = forms.IntegerField(
        label="Device maximum (%).",
        help_text="Can be used to prevent reaching maximum values. "
                  "Default is 100%",
        initial=100, min_value=0, max_value=100,
    )

    turn_on_time = forms.IntegerField(
        min_value=0, max_value=60000, initial=1000,
        help_text="Turn on speed in ms. 1500 is a great quick default. "
                  "10000 - great slow default."
    )
    turn_off_time = forms.IntegerField(
        min_value=0, max_value=60000, initial=20000,
        help_text="Turn off speed in ms. 3000 is a great quick default. "
                  "20000 - great slow default"
    )
    skew = forms.ChoiceField(
        initial='easeOutSine', choices=EASING_CHOICES,
        help_text="easeOutSine - offers most naturally looking effect."
    )
    on_value = forms.FloatField(
        required=False,
        help_text="Static ON value used to turn the light on with physical controls. <br>"
                  "Leaving this field empty turns the light on to the last used value."
    )

    slaves = Select2ModelMultipleChoiceField(
        queryset=Component.objects.filter(
            base_type__in=('dimmer', ),
        ),
        url='autocomplete-component',
        forward=(forward.Const(['dimmer', ], 'base_type'),),
        required=False
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=10
        )
    )


class DC10VConfigForm(PWMOutputBaseConfig):
    output_pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    min = forms.FloatField(
        required=True, initial=0,
        help_text="Minimum component value displayed to the user."
    )
    max = forms.FloatField(
        required=True, initial=100,
        help_text="Maximum component value displayed to the user."
    )
    value_units = forms.CharField(required=False, initial='%')

    device_min = forms.FloatField(
        label="Device minimum Voltage.",
        help_text="This will be the lowest possible voltage value of a device.\n"
                   "Don't forget to adjust your component min value accordingly "
                   "if you change this.",
        initial=0, min_value=0, max_value=10,
    )
    device_max = forms.FloatField(
        label="Device maximum Voltage.",
        help_text="Can be set lower than it's natural maximum of 10V. \n"
                  "Don't forget to adjust your component max value accordingly "
                  "if you change this.",
        initial=10, min_value=0, max_value=10,
    )
    inverse = forms.BooleanField(required=False, initial=False)

    turn_on_time = forms.IntegerField(
        min_value=0, max_value=60000, initial=0,
        help_text="Turn on speed in ms. 1500 is a great quick default for controlling lights. "
                  "10000 - great slow default."
    )
    turn_off_time = forms.IntegerField(
        min_value=0, max_value=60000, initial=0,
        help_text="Turn off speed in ms. 3000 is a great quick default when controlling lights. "
                  "20000 - great slow default"
    )
    skew = forms.ChoiceField(
        initial='linear', choices=EASING_CHOICES,
        help_text="easeOutSine - offers most naturally looking effect for lights."
    )
    on_value = forms.FloatField(
        required=False,
        help_text="Static ON value used to turn on the device with physical controls. <br>"
                  "Leaving this field empty turns the device on to the last used value."
    )

    slaves = Select2ModelMultipleChoiceField(
        queryset=Component.objects.filter(
            base_type__in=('dimmer',),
        ),
        url='autocomplete-component',
        forward=(forward.Const(['dimmer', ], 'base_type'),),
        required=False
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=10
        )
    )


class ColonelRGBLightConfigForm(ColonelComponentForm):
    output_pin = Select2ModelChoiceField(
        label="Port",
        queryset=ColonelPin.objects.filter(output=True, native=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True, 'native': True}, 'filters')
        ]
    )
    num_leds = forms.IntegerField(
        label=_("Number of leds"), min_value=1, max_value=2000
    )
    strip_type = forms.ChoiceField(
        label="LED strip type",
        choices=(
            ("WS2811", "WS2811"),
            ('WS2812', "WS2812"),
            ('WS2812B', "WS2812B"),
            ('WS2813', "WS2813"),
            ('WS2815', "WS2815"),
            ('SK6812', "SK6812"),
            ('generic', "Generic"),
        )
    )
    has_white = forms.BooleanField(initial=False, required=False)
    color_order = forms.ChoiceField(
        required=False, choices=(
            (None, 'Default'),
            ("RGB", "RGB"), ("RBG", "RBG"), ("GRB", "GRB"),
            ("RGBW", "RGBW"), ("RBGW", "RBGW"), ("GRBW", "GRBW"),
        ),
    )
    custom_timing = forms.CharField(
        required=False,
        help_text="Custom addressable led strip timing (T0H, T0L, T1H, T1L). <br>"
                  "For example SK6812 is: (300, 900, 600, 600)"
    )
    sustain_color = forms.BooleanField(
        initial=True, required=False,
        help_text="Recommended to leave this enabled. <br>"
                  "Addressible signal wire might pick up electrical "
                  "noise from it's surroundings which might cause color change "
                  "on random pixels. Colonel will send color update every 20s "
                  "to sustain last set color if this is enabled. "
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=2
        )
    )

    def save(self, commit=True):
        if 'output_pin' in self.cleaned_data:
            self.instance.config['output_pin_no'] = \
                self.cleaned_data['output_pin'].no
        obj = super().save(commit)
        if commit and self.cleaned_data.get('controls'):
            GatewayObjectCommand(
                self.instance.gateway, obj, command='watch_buttons'
            ).publish()
        return obj

    def clean_custom_timing(self):
        custom_timing = self.cleaned_data.get('custom_timing')
        if not custom_timing:
            return custom_timing
        custom_timing = custom_timing.strip().\
            strip('(').strip('[').rstrip(')').rstrip(']').split(',')
        if len(custom_timing) != 4:
            raise forms.ValidationError("Tuple of 4 integers please.")
        for t in custom_timing:
            try:
                t = int(t)
            except:
                raise forms.ValidationError(f"Integers only please.")
            if t <= 0:
                raise forms.ValidationError(f"Intervals must be greater than 0.")
            if t > 100000:
                raise forms.ValidationError(f"{t} seems way to much!")
        return f"({','.join(custom_timing)})"

    def clean(self):
        super().clean()

        if 'output_pin' in self.cleaned_data:
            self._clean_pin('output_pin')

        if self.cleaned_data.get('controls'):
            self._clean_controls()

        if self.cleaned_data.get('output_pin') and self.cleaned_data.get('controls'):
            for ctrl in self.cleaned_data['controls']:
                if not ctrl['input'].startswith('pin'):
                    continue
                if int(ctrl['input'][4:]) == self.cleaned_data['output_pin'].id:
                    self.add_error(
                        "output_pin",
                        "Can't be used as control pin at the same time!"
                    )

        if 'color_order' in self.cleaned_data:
            if self.cleaned_data.get('color_order'):
                if self.cleaned_data['has_white']:
                    if len(self.cleaned_data['color_order']) != 4:
                        self.add_error(
                            "color_order",
                            _("4 colors expected for stripes with dedicated White led.")
                        )
                else:
                    if len(self.cleaned_data['color_order']) != 3:
                        self.add_error(
                            "color_order",
                            _("3 colors expected for stripes without dedicated White led.")
                        )

        return self.cleaned_data



class DualMotorValveForm(ColonelComponentForm):
    open_pin = Select2ModelChoiceField(
        label="Open Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    open_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    open_duration = forms.FloatField(
        required=True, min_value=0.01, max_value=1000000000,
        initial=2, help_text="Time in seconds to open."
    )
    close_pin = Select2ModelChoiceField(
        label="Close Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    close_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    close_duration = forms.FloatField(
        required=True, min_value=0.01, max_value=1000000000,
        initial=10, help_text="Time in seconds to close."
    )
    min = forms.FloatField(
        label="Minimum displayed value", required=True, initial=0
    )
    max = forms.FloatField(
        label="Maximum displayed value", required=True, initial=100
    )


    def clean(self):
        super().clean()
        if self.cleaned_data.get('open_pin'):
            self._clean_pin('open_pin')
        if self.cleaned_data.get('close_pin'):
            self._clean_pin('close_pin')
        if self.cleaned_data.get('open_pin') \
        and self.cleaned_data.get('close_pin') \
        and self.cleaned_data['open_pin'] == self.cleaned_data['close_pin']:
            self.add_error(
                'close_pin', "Can't be the same as open pin!"
            )
        return self.cleaned_data

    def save(self, commit=True):
        if 'open_pin' in self.cleaned_data:
            self.instance.config['open_pin_no'] = \
                self.cleaned_data['open_pin'].no
        if 'close_pin' in self.cleaned_data:
            self.instance.config['close_pin_no'] = \
                self.cleaned_data['close_pin'].no
        obj = super().save(commit=commit)
        return obj


class BlindsConfigForm(ColonelComponentForm):
    open_pin = Select2ModelChoiceField(
        label="Open Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    open_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    close_pin = Select2ModelChoiceField(
        label="Close Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    close_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    open_direction = forms.ChoiceField(
        label='Closed > Open direction',
        required=True, choices=(
            ('up', "Up"), ('down', "Down"),
            ('right', "Right"), ('left', "Left")
        ),
        help_text="Move direction from fully closed to fully open."

    )
    open_duration = forms.FloatField(
        label='Open duration', min_value=1, max_value=360000,
        initial=30,
        help_text="Time in seconds it takes for your blinds to go "
                  "from fully closed to fully open."
    )
    close_duration = forms.FloatField(
        label='Close duration', min_value=1, max_value=360000,
        initial=30,
        help_text="Time in seconds it takes for your blinds to go "
                  "from fully open to fully closed."
    )
    control_type = forms.ChoiceField(
        initial=0, required=True, choices=(
            ('hold', "Hold"), ('click', 'Click')
        ),
        help_text="What type of blinds you have?<br>"
                  "Hold - blinds goes for as long as contacts are held together<br>"
                  "Click - blinds goes and stops with short click of ontroll contacts."
    )
    slats_angle_duration = forms.FloatField(
        label='Slats angle duration', min_value=0.1, max_value=360000,
        required=False,
        help_text="Takes effect only with App control mode - 'Slide', "
                  "can be used with slat blinds to control slats angle. <br>"
                  "Time in seconds it takes "
                  "to go from fully closed to the start of open movement. <br>"
                  "Usually it's in between of 1 - 3 seconds."
    )
    retain_angle = forms.BooleanField(
        required=False, initial=True,
        help_text="Retain blinds angle after adjusting it's "
                  "position using physical buttons."
    )
    control_mode = forms.ChoiceField(
        label="App control mode", required=True, choices=(
            ('click', "Click"), ('hold', "Hold"), ('slide', "Slide")
        ),
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=2
        )
    )

    def __init__(self, *args, **kwargs):
        self.basic_fields.extend(
            ['open_duration', 'close_duration',
             'slats_angle_duration', 'retain_angle']
        )
        return super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.cleaned_data.get('open_pin') \
        and self.cleaned_data.get('close_pin') \
        and self.cleaned_data['open_pin'] == self.cleaned_data['close_pin']:
            self.add_error(
                'close_pin', "Can't be the same as open pin!"
            )

        if self.cleaned_data.get('open_pin'):
            self._clean_pin('open_pin')
        if self.cleaned_data.get('close_pin'):
            self._clean_pin('close_pin')

        if 'controls' in self.cleaned_data:
            if len(self.cleaned_data['controls']) not in (0, 1, 2):
                self.add_error('controls', "Must have 0, 1 or 2 controls")
                return self.cleaned_data

            if len(self.cleaned_data['controls']) == 2:
                method = None
                for c in self.cleaned_data['controls']:
                    if not method:
                        method = c['method']
                    else:
                        if c['method'] != method:
                            self.add_error('controls', "Both must use the same control method.")
                            return self.cleaned_data

            self._clean_controls()

            if self.cleaned_data.get('open_pin') and self.cleaned_data.get('controls'):
                for ctrl in self.cleaned_data['controls']:
                    if not ctrl['input'].startswith('pin'):
                        continue
                    if int(ctrl['input'][4:]) == self.cleaned_data['open_pin'].id:
                        self.add_error(
                            "open_pin",
                            "Can't be used as control pin at the same time!"
                        )

            if self.cleaned_data.get('close_pin') and self.cleaned_data.get('controls'):
                for ctrl in self.cleaned_data['controls']:
                    if not ctrl['input'].startswith('pin'):
                        continue
                    if int(ctrl['input'][4:]) == self.cleaned_data['close_pin'].id:
                        self.add_error(
                            "close_pin",
                            "Can't be used as control pin at the same time!"
                        )
        return self.cleaned_data

    def save(self, commit=True):
        if 'open_pin' in self.cleaned_data:
            self.instance.config['open_pin_no'] = \
                self.cleaned_data['open_pin'].no
        if 'close_pin' in self.cleaned_data:
            self.instance.config['close_pin_no'] = \
                self.cleaned_data['close_pin'].no
        obj = super().save(commit=commit)
        if commit and self.cleaned_data.get('controls'):
            GatewayObjectCommand(
                self.instance.gateway, obj, command='watch_buttons'
            ).publish()
        return obj


class GateConfigForm(ColonelComponentForm):
    open_pin = Select2ModelChoiceField(
        label="Open Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ], help_text="If your gate is controlled by single input, "
                     "using this port is enough."
    )
    open_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    close_pin = Select2ModelChoiceField(
        label="Close Relay Port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ], required=False
    )
    close_action = forms.ChoiceField(
        choices=(('HIGH', "HIGH"), ('LOW', "LOW")),
    )
    control_method = forms.ChoiceField(
        choices=(('pulse', "Pulse"), ('hold', "Hold")), initial="pulse",
        help_text="What your gate motors expect to receive as control command?"
    )

    sensor_pin = Select2ModelChoiceField(
        label='Gate open/closed sensor port',
        queryset=ColonelPin.objects.filter(input=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'input': True}, 'filters')
        ], required=False,
    )
    closed_value = forms.ChoiceField(
        label='Gate closed value',
        choices=(("LOW", "LOW"), ('HIGH', "HIGH")), initial="LOW",
        help_text="What is the input sensor value, "
                  "when your gate is in closed position?"
    )

    open_duration = forms.FloatField(
        initial=30, min_value=1, max_value=600,
        help_text="How much time in seconds does it take for your gate "
                  "to go from fully closed to fully open?"
    )

    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=2
        )
    )

    auto_open_distance = forms.CharField(
        initial='100 m', required=False,
        help_text="Open the gate automatically whenever somebody is coming home"
                  "and comes closer than this distance. Clear this value out, "
                  "to disable auto opening."
    )
    auto_open_for = Select2ModelMultipleChoiceField(
        queryset=PermissionsRole.objects.all(),
        url='autocomplete-user-roles',  required=False,
        help_text="Open the gates automatically only for these user roles. "
                  "Leaving this field blank opens the gate for all system users."
    )
    location = PlainLocationField(
        zoom=18,
        help_text="Location of your gate. Required only for automatic opening. "
                  "Adjust this if this gate is significantly distanced from "
                  "your actual home location."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.fields['location'].initial:
            self.fields['location'].initial = get_current_instance().location

    def clean_distance(self):
        distance = self.cleaned_data.get('auto_open_distance')
        if not distance:
            return distance
        try:
            distance = input_to_meters(distance)
        except Exception as e:
            raise forms.ValidationError(str(e))

        if distance < 20:
            raise forms.ValidationError(
                "That is to little of a distance. At least 20 meters is required."
            )
        if distance > 2000:
            raise forms.ValidationError(
                "This is to high of a distance. Max 2 km is allowed."
            )

        return distance


    def clean(self):
        super().clean()
        check_pins = ('open_pin', 'close_pin', 'sensor_pin')
        for pin in check_pins:
            if not self.cleaned_data.get(pin):
                continue
            for p in check_pins:
                if pin == pin:
                    continue
                if not self.cleaned_data.get(p):
                    continue
                if self.cleaned_data[pin] == self.cleaned_data[p]:
                    self.add_error(
                        pin, f"Can't be the same {p}!"
                    )

        if self.cleaned_data.get('open_pin'):
            self._clean_pin('open_pin')
        if self.cleaned_data.get('close_pin'):
            self._clean_pin('close_pin')
        if self.cleaned_data.get('sensor_pin'):
            self._clean_pin('sensor_pin')

        if 'controls' in self.cleaned_data:

            self._clean_controls()

            if self.cleaned_data.get('control_pin') and self.cleaned_data.get('controls'):
                for ctrl in self.cleaned_data['controls']:
                    if not ctrl['input'].startswith('pin'):
                        continue
                    if int(ctrl['input'][4:]) == self.cleaned_data['control_pin'].id:
                        self.add_error(
                            "control_pin",
                            "Can't be used as control pin at the same time!"
                        )

            if self.cleaned_data.get('sensor_pin') and self.cleaned_data.get('controls'):
                for ctrl in self.cleaned_data['controls']:
                    if not ctrl['input'].startswith('pin'):
                        continue
                    if int(ctrl['input'][4:]) == self.cleaned_data['sensor_pin'].id:
                        self.add_error(
                            "sensor_pin",
                            "Can't be used as control pin at the same time!"
                        )
        return self.cleaned_data

    def save(self, commit=True):
        if self.cleaned_data.get('open_pin'):
            self.instance.config['open_pin_no'] = \
                self.cleaned_data['open_pin'].no
        if self.cleaned_data.get('close_pin'):
            self.instance.config['close_pin_no'] = \
                self.cleaned_data['close_pin'].no
        if self.cleaned_data.get('sensor_pin'):
            self.instance.config['sensor_pin_no'] = \
                self.cleaned_data['sensor_pin'].no
        obj = super().save(commit=commit)
        if commit and self.cleaned_data.get('controls'):
            GatewayObjectCommand(
                self.instance.gateway, obj, command='watch_buttons'
            ).publish()
        return obj


class BurglarSmokeDetectorConfigForm(ColonelComponentForm):
    power_pin = Select2ModelChoiceField(
        label="Power port",
        queryset=ColonelPin.objects.filter(output=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'output': True}, 'filters')
        ]
    )
    sensor_pin = Select2ModelChoiceField(
        label="Sensor port",
        queryset=ColonelPin.objects.filter(input=True),
        url='autocomplete-colonel-pins',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const({'input': True}, 'filters')
        ]
    )
    sensor_inverse = forms.TypedChoiceField(
        choices=((0, "No"), (1, "Yes")), coerce=int, initial=0,
        help_text="Hint: Set to Yes, to get ON signal when "
                  "you deliver GND to the pin and OFF when you cut it out."
    )

    def clean(self):
        super().clean()
        if 'sensor_pin' in self.cleaned_data:
            self._clean_pin('sensor_pin')
        if 'power_pin' in self.cleaned_data:
            self._clean_pin('power_pin')

        if self.cleaned_data.get('sensor_pin') \
        and self.cleaned_data.get('power_pin') \
        and self.cleaned_data['sensor_pin'] == self.cleaned_data['power_pin']:
            self.add_error(
                'power_pin', "Can't be the same as sensor pin!"
            )

        return self.cleaned_data

    def save(self, commit=True):
        if 'sensor_pin' in self.cleaned_data:
            self.instance.config['sensor_pin_no'] = \
                self.cleaned_data['sensor_pin'].no
        if 'power_pin' in self.cleaned_data:
            self.instance.config['power_pin_no'] = \
                self.cleaned_data['power_pin'].no
        return super().save(commit=commit)


class TTLockConfigForm(ColonelComponentForm):

    door_sensor = Select2ModelChoiceField(
        queryset=Component.objects.filter(base_type='binary-sensor'),
        url='autocomplete-component',
        forward=(
            forward.Const(['binary-sensor'], 'base_type'),
        ), required=False,
        help_text="Quickens up lock status reporting on open/close if provided."
    )
    auto_lock = forms.IntegerField(
        min_value=0, max_value=60, required=False,
        help_text="Lock the lock after given amount of seconds."
    )
    inverse = forms.BooleanField(
        required=False,
        help_text="Inverse operation (if supported by the lock)."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basic_fields.extend(['auto_lock', 'inverse'])

    def clean(self):
        if not self.instance or not self.instance.pk:
            from .controllers import TTLock
            other_lock = self.cleaned_data['colonel'].components.filter(
                controller_uid=TTLock.uid
            ).first()
            if other_lock:
                raise forms.ValidationError(
                    f"Single Colonel can support single TTLock only.\n"
                    f"You already have {other_lock} on this Colonel."
                )
        return self.cleaned_data

    def save(self, commit=True):
        obj = super(ColonelComponentForm, self).save(commit)
        if commit:
            if 'door_sensor' in self.cleaned_data:
                GatewayObjectCommand(
                    self.instance.gateway, self.cleaned_data['door_sensor'],
                    command='watch_lock_sensor'
                ).publish()
            GatewayObjectCommand(
                obj.gateway, self.cleaned_data['colonel'], id=obj.id,
                command='call', method='update_config', args=[
                    obj.controller._get_colonel_config()
                ]
            ).publish()
        return obj


class DALIDeviceConfigForm(ColonelComponentForm):
    interface = Select2ModelChoiceField(
        queryset=Interface.objects.filter(type='dali'),
        url='autocomplete-interfaces',
        forward=[
            forward.Self(),
            forward.Field('colonel'),
            forward.Const(
                {'type': 'dali'}, 'filters'
            )
        ]
    )

    def clean_interface(self):
        if not self.instance.pk:
            return self.cleaned_data['interface']
        if 'interface' in self.changed_data:
            raise forms.ValidationError(
                "Changing interface after component is created "
                "it is not allowed!"
            )
        return self.cleaned_data['interface']

    def clean(self):
        if not self.cleaned_data.get('colonel'):
            return self.cleaned_data
        if self.cleaned_data['interface'].colonel != self.cleaned_data['colonel']:
            self.add_error(
                'interface',
                f"This interface is on {self.cleaned_data['interface'].colonel}, "
                f"however we need an interface from {self.cleaned_data['colonel']}."
            )
        return self.cleaned_data

    def save(self, commit=True):
        if 'interface' in self.cleaned_data:
            self.instance.config['dali_interface'] = \
                self.cleaned_data['interface'].no
        is_new = not self.instance.pk
        obj = super().save(commit=commit)
        if commit:
            if not is_new:
                GatewayObjectCommand(
                    obj.gateway, self.cleaned_data['colonel'], id=obj.id,
                    command='call', method='update_config', args=[
                        obj.controller._get_colonel_config()
                    ]
                ).publish()
        return obj


class DaliLampForm(DALIDeviceConfigForm, BaseComponentForm):
    fade_time = forms.TypedChoiceField(
        initial=1, coerce=int, choices=(
            (0, "Instant"),
            (1, "0.7 s"), (2, "1.0 s"), (3, "1.4 s"), (4, "2.0 s"), (5, "2.8 s"),
            (6, "4.0 s"), (7, "5.7 s"), (8, "8.0 s")
        )
    )
    gear_min = forms.IntegerField(
        min_value=1, max_value=254, initial=90,
        help_text="Minimum level at which device starts operating up (1 - 254), "
                  "SIMO.io DALI interface detects this value automatically when "
                  "pairing a new device. <br>"
                  "Most LED drivers we tested starts at 86. <br>"
                  "If you set this value to low, you might start seeing device "
                  "beings dying out when you hit it with lower value than it "
                  "is capable of supplying."
    )
    on_value = forms.FloatField(
        required=True, initial=100,
        help_text="ON value when used with toggle switch"
    )
    auto_off = forms.FloatField(
        required=False, min_value=0.01, max_value=1000000000,
        help_text="If provided, lamp will be turned off after "
                  "given amount of seconds after last turn on event."
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=999
        )
    )

    def clean(self):
        if 'controls' in self.cleaned_data:
            self._clean_controls()
        return self.cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit:
            if self.cleaned_data.get('controls'):
                GatewayObjectCommand(
                    self.instance.gateway, obj, command='watch_buttons'
                ).publish()
            if self.instance.pk:
                old_controls = Component.objects.get(
                    pk=self.instance.pk
                ).config.get('controls')
                if old_controls != self.cleaned_data.get('controls'):
                    self.cleaned_data['colonel'].update_config()
        return obj


class DaliSwitchConfigForm(DALIDeviceConfigForm, BaseComponentForm):
    auto_off = forms.FloatField(
        required=False, min_value=0.01, max_value=1000000000,
        help_text="If provided, lamp will be turned off after "
                  "given amount of seconds after last turn on event."
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=999
        )
    )

    def clean(self):
        if 'controls' in self.cleaned_data:
            self._clean_controls()
        return self.cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit:
            if self.cleaned_data.get('controls'):
                GatewayObjectCommand(
                    self.instance.gateway, obj, command='watch_buttons'
                ).publish()
            if self.instance.pk:
                old_controls = Component.objects.get(
                    pk=self.instance.pk
                ).config.get('controls')
                if old_controls != self.cleaned_data.get('controls'):
                    self.cleaned_data['colonel'].update_config()
        return obj


class DaliGearGroupForm(DALIDeviceConfigForm, BaseComponentForm):
    auto_off = forms.FloatField(
        required=False, min_value=0.01, max_value=1000000000,
        help_text="If provided, group will be turned off after "
                  "given amount of seconds after last turn on event."
    )
    members = Select2ModelMultipleChoiceField(
        queryset=Component.objects.filter(
            controller_uid='simo.fleet.controllers.DALILamp',
        ),
        label="Members", required=True,
        url='autocomplete-component',
        forward=(
            forward.Const(
                ['simo.fleet.controllers.DALILamp', ], 'controller_uid'
            ),
        )
    )
    on_value = forms.FloatField(
        required=True, initial=100,
        help_text="ON value when used with toggle switch"
    )
    controls = FormsetField(
        formset_factory(
            ControlForm, can_delete=True, can_order=True, extra=0, max_num=999
        )
    )

    def clean(self):
        if 'members' in self.cleaned_data:
            if len(self.cleaned_data['members']) < 2:
                raise forms.ValidationError("At least two members are required.")
            for member in self.cleaned_data['members']:
                if member.config['interface'] != self.cleaned_data['interface'].id:
                    self.add_error(
                        'members', f"{member} belongs to other DALI interface."
                    )
        self.group_addr = None
        if not self.instance.pk:
            from .controllers import DALIGearGroup
            occupied_addresses = set([
                int(c['config'].get('da', 0)) for c in Component.objects.filter(
                controller_uid=DALIGearGroup.uid,
                config__colonel=self.cleaned_data['colonel'].id,
                config__interface=self.cleaned_data['interface'].id,
            ).values('config')])
            for addr in range(16):
                if addr in occupied_addresses:
                    continue
                self.group_addr = addr
                break
            if self.group_addr is None:
                self.add_error(
                    'interface',
                    "Already has 16 groups. No more groups are allowed on DALI line."
                )
        else:
            self.group_addr = self.instance.config['da']
        if 'controls' in self.cleaned_data:
            self._clean_controls()
        return self.cleaned_data

    def save(self, commit=True):
        old_members = self.instance.config.get('members', [])
        self.instance.config['da'] = self.group_addr
        is_new = not self.instance.pk
        obj = super().save(commit)
        if commit:
            new_members = obj.config.get('members', [])
            for removed_member in Component.objects.filter(
                id__in=set(old_members) - set(new_members)
            ):
                self.controller._modify_member_group(
                    removed_member, self.group_addr, remove=True
                )
            for member in Component.objects.filter(id__in=new_members):
                self.controller._modify_member_group(member, self.group_addr)
            if is_new:
                GatewayObjectCommand(
                    obj.gateway, self.cleaned_data['colonel'],
                    command='finalize',
                    data={
                        'temp_id': 'none',
                        'permanent_id': obj.id,
                        'comp_config': {
                            'type': obj.controller_uid.split('.')[-1],
                            'family': self.controller.family,
                            'config': obj.config
                        }
                    }
                ).publish()
            else:
                GatewayObjectCommand(
                    obj.gateway, self.cleaned_data['colonel'], id=obj.id,
                    command='call', method='update_config', args=[
                        obj.controller._get_colonel_config()
                    ]
                ).publish()

        if commit:
            if self.cleaned_data.get('controls'):
                GatewayObjectCommand(
                    self.instance.gateway, obj, command='watch_buttons'
                ).publish()
            if self.instance.pk:
                old_controls = Component.objects.get(
                    pk=self.instance.pk
                ).config.get('controls')
                if old_controls != self.cleaned_data.get('controls'):
                    self.cleaned_data['colonel'].update_config()
        return obj


class DaliOccupancySensorConfigForm(DALIDeviceConfigForm, BaseComponentForm):
    hold_time = forms.TypedChoiceField(
        initial=3, coerce=int, choices=(
            (1, "10 s"), (2, "20 s"), (3, "30 s"), (4, "40 s"), (5, "50 s"),
            (6, "1 min"), (9, "1.5 min"), (12, "2 min"), (18, "3 min"),
            (30, "5 min"), (60, "10 min"), (120, "20 min"),
        )
    )


class DALILightSensorConfigForm(DALIDeviceConfigForm, BaseComponentForm):
    pass


class DALIButtonConfigForm(DALIDeviceConfigForm, BaseComponentForm):
    pass


class SentinelDeviceConfigForm(BaseComponentForm):
    colonel = Select2ModelChoiceField(
        label="Sentinel", queryset=Colonel.objects.filter(type='sentinel'),
        url='autocomplete-colonels',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit colonels to current instance for convenience
        instance = get_current_instance()
        if instance:
            self.fields['colonel'].queryset = self.fields['colonel'].queryset.filter(
                instance=instance
            )

    def save(self, commit=True):
        from simo.core.models import Icon
        colonel = self.cleaned_data.get('colonel')
        if not colonel:
            return

        from .controllers import (
            RoomSiren, AirQualitySensor, TempHumSensor, AmbientLightSensor,
            RoomPresenceSensor, VoiceAssistant, SmokeDetector
        )

        org_name = self.cleaned_data['name']
        org_icon = self.cleaned_data['icon']
        last_comp = None
        for CtrlClass, icon, suffix, cat_slug in (
            (RoomSiren, 'siren', 'siren', 'security'),
            (AirQualitySensor, 'leaf', 'air quality', 'climate'),
            (TempHumSensor, 'temperature-half', 'temperature', 'climate'),
            (AmbientLightSensor, 'brightness-low', 'brightness', 'light'),
            (RoomPresenceSensor, 'person', 'presence', 'security'),
            (VoiceAssistant, 'microphone-lines', 'voice assistant', 'other'),
            (SmokeDetector, 'fire-smoke', 'dust/pollution', 'security'),
        ):
            default_icon = Icon.objects.filter(slug=icon).first()
            self.cleaned_data['icon'] = default_icon.slug if default_icon else org_icon
            self.cleaned_data['name'] = f"{org_name} {suffix}"
            self.cleaned_data['category'] = Category.objects.filter(
                name__icontains=cat_slug
            ).first()

            comp = Component.objects.filter(
                config__colonel=colonel.id,
                controller_uid=CtrlClass.uid
            ).first()

            form = CtrlClass.config_form(
                controller_uid=CtrlClass.uid, instance=comp,
                data=self.cleaned_data
            )
            if form.is_valid():
                comp = form.save()
                comp.value_units = CtrlClass.default_value_units
                comp.config['colonel'] = colonel.id
                comp.save()
                last_comp = comp
            else:
                raise Exception(form.errors)

        if colonel and last_comp:
            GatewayObjectCommand(
                last_comp.gateway, colonel, id=last_comp.id,
                command='call', method='update_config', args=[
                    last_comp.controller._get_colonel_config()
                ]
            ).publish()

        return last_comp


class RoomZonePresenceConfigForm(BaseComponentForm):
    colonel = Select2ModelChoiceField(
        label="Sentinel", queryset=Colonel.objects.filter(type='sentinel'),
        url='autocomplete-colonels',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = get_current_instance()
        if instance:
            self.fields['colonel'].queryset = self.fields['colonel'].queryset.filter(
                instance=instance
            )


class VoiceAssistantConfigForm(BaseComponentForm):
    voice = forms.ChoiceField(
        label="Voice",
        required=True, choices=(
            ('male', "Male"), ('female', "Female"),
        ),
    )
