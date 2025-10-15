"""
Serializers for tags and related objects.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from rest_framework import serializers

from eox_tagging.api.v1 import fields
from eox_tagging.constants import AccessLevel, Status
from eox_tagging.edxapp_accessors import get_object_from_edxapp, get_site
from eox_tagging.models import Tag

MODELS_WITH_COMPOUND_KEYS = {
    "courseenrollment": ["username", "course_id"],
    "generatedcertificate": ["username", "course_id"],
}


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""

    target_id = serializers.CharField(source="target_object", write_only=True)
    owner_id = serializers.CharField(
        source="owner_object", required=False, write_only=True
    )
    owner_type = serializers.CharField(
        source="owner_object_type", write_only=True, required=False
    )
    target_type = serializers.CharField(source="target_object_type", write_only=True)
    meta = serializers.SerializerMethodField()
    access = fields.EnumField(enum=AccessLevel, required=False)
    status = fields.EnumField(enum=Status, required=False)

    class Meta:
        """Meta class."""

        model = Tag
        fields = (
            "meta",
            "key",
            "tag_value",
            "tag_type",
            "access",
            "activation_date",
            "expiration_date",
            "target_id",
            "owner_id",
            "owner_type",
            "target_type",
            "status",
        )

    def get_meta(self, instance):
        """Getter of read-only field that returns technical information."""
        return {
            "target_id": str(instance.target_object),
            "target_type": instance.target_object_type,
            "owner_id": str(instance.owner_object),
            "owner_type": instance.owner_object_type,
            "created_at": instance.created_at,
            "inactivated_at": instance.inactivated_at,
        }

    def create(self, validated_data):
        """Function that creates a Tag instance."""
        target_object = None
        owner_object = None
        target_type = validated_data.pop("target_object_type")
        owner_type = validated_data.pop("owner_object_type", None)
        target = validated_data.pop("target_object", None)

        if target_type and target_type.lower() in MODELS_WITH_COMPOUND_KEYS:
            data = self._convert_compound_keys(target, target_type.lower())
        else:
            data = {
                "target_id": target,
            }

        try:
            target_object = get_object_from_edxapp(target_type, **data)
        except Exception as exc:
            raise serializers.ValidationError(
                {"Target": _(f"Error getting {target_type} object.")}
            ) from exc

        if owner_type and owner_type.lower() == "user":
            owner_object = self.context.get("request").user
        else:
            owner_object = get_site()

        tag_object = {
            "target_object": target_object,
            "owner_object": owner_object,
        }
        tag_object.update(validated_data)

        try:
            return Tag.objects.create_tag(**tag_object)
        except ValidationError as validation_error:
            raise serializers.ValidationError({"Tag": _(f"{validation_error.message}")})

    @staticmethod
    def _convert_compound_keys(ids, object_type):
        """
        Function that converts strings with format: `key1: key2` into a dictionary.
        """
        target_id = ids.replace(" ", "").split(":", 1)
        if len(target_id) == 1:
            return {
                "target_id": ids,
            }
        target_labels = MODELS_WITH_COMPOUND_KEYS.get(object_type)
        target_pairs = zip(target_labels, target_id)
        return dict(target_pairs)
