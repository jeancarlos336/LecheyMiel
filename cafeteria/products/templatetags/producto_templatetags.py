from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Añade una clase CSS a un campo de formulario o elemento HTML
   
    Uso en plantilla: {{ form.field|add_class:"form-control" }}
    """
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = f"{css_classes} {arg}"
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes})


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave
    """
    if dictionary is None:
        return []  # Devolver lista vacía en lugar de causar error
    return dictionary.get(key, [])

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplica dos valores.
    Uso en plantilla: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return value * arg  # Para casos donde no son números (aunque no es lo ideal)
        except Exception:
            return ''

@register.filter
def in_list(value, arg):
    """
    Verifica si un valor está en una lista de elementos separados por comas.
    
    Uso en plantilla: 
    {{ detalle.estado|in_list:"cancelado,entregado,otro_estado" }}
    """
    return str(value) in arg.split(',')

@register.filter
def endswith(value, arg):
    """
    Verifica si el valor termina con el argumento
    """
    return value.endswith(arg)


@register.filter(name='div')
def div(value, arg):
    """Divide value por arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter(name='last_item')
def last_item(value):
    """
    Obtiene el último elemento de una lista o queryset
    Uso en plantilla: {{ lista|last_item }}
    """
    try:
        if value:
            return value[-1] if hasattr(value, '__getitem__') else list(value)[-1]
        return None
    except (IndexError, TypeError):
        return None

@register.filter(name='first_item')
def first_item(value):
    """
    Obtiene el primer elemento de una lista o queryset
    Uso en plantilla: {{ lista|first_item }}
    """
    try:
        if value:
            return value[0] if hasattr(value, '__getitem__') else list(value)[0]
        return None
    except (IndexError, TypeError):
        return None

@register.filter(name='safe_attr')
def safe_attr(obj, attr_name):
    """
    Accede de forma segura a un atributo de un objeto
    Uso en plantilla: {{ objeto|safe_attr:"atributo" }}
    """
    try:
        return getattr(obj, attr_name, None)
    except AttributeError:
        return None