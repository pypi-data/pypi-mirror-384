"""
Admin class.
"""
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from eox_tagging.forms import TagForm
from eox_tagging.models import OpaqueKeyProxyModel, Tag


class TagAdmin(admin.ModelAdmin):
    """Tag admin."""
    list_display = [
        "key",
        "tag_type",
        "tag_value",
        "tagged_object",
        "owner",
        "status",
    ]
    readonly_fields = (
        'target_as_nice_string',
        'status',
        'created_at',
        'inactivated_at',
    )
    search_fields = ('tag_type', 'tag_value', 'status')

    form = TagForm

    def target_as_nice_string(self, tag):
        """
        Render the opaque key proxy as a nice Course Key or any other target as its unicode.
        """
        return str(tag.target_object)

    def get_search_results(self, request, queryset, search_term):
        """
        Custom search to support searching on the tagged objects
        """
        queryset, use_distinct = super().get_search_results(
            request,
            queryset,
            search_term
        )
        # TODO: we need to connect the TagQuery search here.
        return queryset, use_distinct

    def owner(self, tag):
        """
        Displays useful info about the owner of the tag.
        """
        # pylint: disable=broad-except
        try:
            return f"{tag.owner_object_type}: {tag.owner_object}"
        except Exception as error:
            return str(error)

    def tagged_object(self, tag):
        """
        Displays useful info about the tagged object.
        """
        # pylint: disable=broad-except
        try:
            if tag.target_object:
                return f"{tag.target_object_type}: {tag.target_object}"
            return f"Resource locator: {tag.resource_locator}"
        except Exception as error:
            return str(error)

    def add_view(self, request, form_url='', extra_context=None):
        """
        Custom method to handle the specific case of tagging course_keys

        The POST request is modified to add the target object if and only if an opaque_key is defined
        and no target_object_id is specified.

        We decided to do this because we needed to add the target object before the Tag instance was
        created.
        """
        should_intervene = True

        if not request.POST:
            should_intervene = False

        if request.POST.get('target_type', None) and request.POST.get('target_object_id', None):
            should_intervene = False

        if not request.POST.get('opaque_key', None):
            should_intervene = False

        if should_intervene:
            try:
                course_key = CourseKey.from_string(request.POST.get('opaque_key'))
                opaque_key_proxy, _ = OpaqueKeyProxyModel.objects.get_or_create(opaque_key=course_key)
            except InvalidKeyError:
                opaque_key = request.POST['opaque_key']
                message = f"EOX_TAGGING | Error: Opaque Key {opaque_key} does not match with opaque_keys.edx definition"
                messages.error(request, message)
                return HttpResponseRedirect(request.path)

            request.POST = request.POST.copy()
            request.POST['target_type'] = ContentType.objects.get(model='OpaqueKeyProxyModel').id
            request.POST['target_object_id'] = opaque_key_proxy.id

        return super().add_view(request, form_url='', extra_context=None)


admin.site.register(Tag, TagAdmin)
