from django.db import models
from django.core.validators import EmailValidator


class StringNotNullField(models.CharField):
    description = "Custom String with Not Null"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)
        kwargs['null'] = False  # Ensure the field is not nullable
        kwargs['help_text'] = kwargs.get('help_text', 'string field with null false')
        super(StringNotNullField, self).__init__(*args, **kwargs)


class StringOptionsField(models.CharField):
    description = "Custom String Field with Options"

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])  # Retrieve choices from kwargs
        max_length = kwargs.pop('max_length', 255)  # Retrieve max_length from kwargs
        default = kwargs.pop('default', '')  # Retrieve default value from kwargs
        kwargs['help_text'] = kwargs.get('help_text', 'string field with options')
        kwargs['null'] = True  # Allow the field to be nullable
        super(StringOptionsField, self).__init__(max_length=max_length, choices=choices, default=default, **kwargs)


class CustomDateTimeField(models.DateTimeField):
    description = "Custom DateTime Field with Auto-Add Now"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True  # Allow the field to be nullable
        super(CustomDateTimeField, self).__init__(*args, **kwargs)


class TextNotNullField(models.TextField):
    description = "Custom Text Field with Not Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = False  # Ensure the field is not nullable
        kwargs['help_text'] = kwargs.get('help_text', 'text field with null false')
        super(TextNotNullField, self).__init__(*args, **kwargs)


class TextNullField(models.TextField):
    description = "Custom Text Field with Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True  # Ensure the field is nullable
        kwargs['help_text'] = kwargs.get('help_text', 'text field with null true')
        super(TextNullField, self).__init__(*args, **kwargs)


class StringNullField(models.CharField):
    description = "Custom String with Null"

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])  # Retrieve choices from kwargs
        kwargs['max_length'] = kwargs.get('max_length', 255)
        kwargs['null'] = True  # Allow the field to be nullable
        kwargs['help_text'] = kwargs.get('help_text', 'string field with null True')
        super(StringNullField, self).__init__(choices=choices, *args, **kwargs)


class IntegerOptionsField(models.IntegerField):
    description = "Custom String Field with Options"

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])  # Retrieve choices from kwargs
        default = kwargs.pop('default', '')  # Retrieve default value from kwargs
        kwargs['help_text'] = kwargs.get('help_text', 'string field with options')
        kwargs['null'] = True  # Allow the field to be nullable
        super(IntegerOptionsField, self).__init__(choices=choices, default=default, **kwargs)


class BooleanTrueField(models.BooleanField):
    description = "Custom Boolean Field with Default True"

    def __init__(self, *args, **kwargs):
        kwargs['default'] = True  # Set the default value to True
        super(BooleanTrueField, self).__init__(*args, **kwargs)

    def toggle(self, instance):
        value = getattr(instance, self.attname)
        setattr(instance, self.attname, not value)
        instance.save()


class BooleanFalseField(models.BooleanField):
    description = "Custom Boolean Field with Default False"

    def __init__(self, *args, **kwargs):
        kwargs['default'] = False  # Set the default value to False
        super(BooleanFalseField, self).__init__(*args, **kwargs)

    def toggle(self, instance):
        value = getattr(instance, self.attname)
        setattr(instance, self.attname, not value)
        instance.save()


class BooleanNullField(models.BooleanField):
    description = "Custom Boolean Field with Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True  # Allow the field to be nullable
        super(BooleanNullField, self).__init__(*args, **kwargs)


class CustomEmailField(models.EmailField):
    description = "Custom Email Field"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 254)  # Set a default max length for email addresses
        kwargs['validators'] = [EmailValidator()]  # Add email validation
        super(CustomEmailField, self).__init__(*args, **kwargs)


class FloatNullField(models.FloatField):
    description = "Custom Float Field with Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True  # Allow the field to be nullable
        super(FloatNullField, self).__init__(*args, **kwargs)


class CustomJsonField(models.JSONField):
    description = "Custom Json Field with Null"

    def __init__(self, *args, **kwargs):
        kwargs['default'] = kwargs.get('default', list)  # Set a default value for the JSON field
        kwargs['null'] = True  # Allow the field to be nullable
        kwargs['help_text'] = kwargs.get('help_text', 'Json field with null true')
        super(CustomJsonField, self).__init__(*args, **kwargs)


class IntegerNullField(models.IntegerField):
    description = "Custom Integer with Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True  # Allow the field to be nullable
        kwargs['help_text'] = kwargs.get('help_text', 'Integer field with null True')
        super(IntegerNullField, self).__init__(*args, **kwargs)


class LookupFieldMixin:
    """
    Mixin to filter queryset by a lookup field (workspace_id).
    """
    lookup_field = 'workspace_id'

    def filter_queryset(self, queryset):
        if self.lookup_field in self.kwargs:
            lookup_value = self.kwargs[self.lookup_field]
            filter_kwargs = {self.lookup_field: lookup_value}
            queryset = queryset.filter(**filter_kwargs)
        return super().filter_queryset(queryset)
