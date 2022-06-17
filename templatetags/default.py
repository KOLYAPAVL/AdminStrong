from django import template

register = template.Library()

@register.filter(name='field_type')
def field_type(field):
    TYPES = {
        'TextInput': 'text',
        'NumberInput': 'number',
        'DateTimeInput': 'datetime-local',
        'Textarea': 'textarea',
        'DateInput': 'date',
    }
    return TYPES.get(field.field.widget.__class__.__name__, 'text')

@register.filter(name='get_field')
def get_field(field, value):
    return field[value]

@register.filter(name='is_textarea')
def is_textarea(field):
    return field.field.widget.__class__.__name__ == 'Textarea'

@register.filter(name='is_date_field')
def is_date_field(field):
    return field.field.widget.__class__.__name__ == 'DateInput'

@register.filter(name='is_bool_field')
def is_bool_field(field):
    return field.field.widget.__class__.__name__ == 'CheckboxInput'

@register.filter(name='get_choices')
def get_choices(field, value):
    return field[value]

@register.filter(name='get_foreign_url')
def get_foreign_url(field, value):
    return field[value]['url']

@register.filter(name='is_true')
def is_true(field):
    return field == True

@register.filter(name='is_none')
def is_none(field):
    return field is None

@register.filter(name='is_false')
def is_false(field):
    return field == False

@register.filter(name='get_foreign_name')
def get_foreign_name(field, value):
    return field[value]['name']

@register.filter(name='plus')
def plus(field, value):
    return int(field) + int(value)

@register.filter(name='minus')
def minus(field, value):
    return int(field) - int(value)