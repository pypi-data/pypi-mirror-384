"""Module for defining custom fields."""
from rest_framework import serializers


class EnumField(serializers.ChoiceField):
    """Serializer field for choices."""

    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = [(e.value, e.name) for e in enum]
        super().__init__(**kwargs)

    def to_representation(self, value):
        """Function that helps with choice serialization."""
        try:
            return getattr(value, 'name', self.enum(value).name)
        except AttributeError:
            return self.enum(value).name

    def to_internal_value(self, data):
        """Function that helps with choice deserialization."""
        try:
            return self.enum[data.upper()]
        except KeyError:
            return None
