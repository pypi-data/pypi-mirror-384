from django.contrib import admin  # noqa: I001
from django.template import Context, Template
from django.utils.html import format_html

from django_blocknote.models import (
    UnusedImageURLS,
    # DocumentTemplate,
)
from django_blocknote.models.fields import BlockNoteField
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django_blocknote.models import DocumentTemplate

try:
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    BaseModelAdmin = UnfoldModelAdmin
except ImportError:
    BaseModelAdmin = admin.ModelAdmin


User = get_user_model()


@admin.register(UnusedImageURLS)
class UnusedImageURLSAdmin(BaseModelAdmin):
    list_display = [
        "user",
        "image_url",
        "created",
        "deleted",
        "processing_stats",
        "processing",
        "deletion_error",
        "retry_count",
    ]
    search_fields = [
        "user",
        "image_url",
    ]

    list_filter = [
        "user",
        "created",
        "deleted",
        "processing",
    ]


class BlockNoteAdminMixin:
    """
    Mixin to automatically handle BlockNote fields in Django admin.
    Adds read-only preview fields for all BlockNote fields.
    """

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # Automatically add preview fields for BlockNote fields
        # self._setup_blocknote_previews()

    # TODO: Delete this, left just in case for a bit
    # def _setup_blocknote_previews(self):
    #     """Automatically create preview methods for BlockNote fields"""
    #     blocknote_fields = []
    #     for field in self.model._meta.get_fields():
    #         if isinstance(field, BlockNoteField):
    #             blocknote_fields.append(field.name)
    #             preview_method_name = f"{field.name}_preview"
    #
    #             # Create dynamic preview method
    #             def make_preview_method(field_name):
    #                 def preview_method(self, obj):
    #                     # Handle case where obj is None (during creation)
    #                     if obj is None or obj.pk is None:
    #                         return format_html(
    #                             '<em style="color: #999;">Save to see preview</em>',
    #                         )
    #
    #                     content = getattr(obj, field_name)
    #                     if content:
    #                         try:
    #                             template = Template(
    #                                 "{% load blocknote_tags %}{% blocknote_viewer content %}",
    #                             )
    #                             return format_html(
    #                                 template.render(Context({"content": content})),
    #                             )
    #                         except Exception as e:
    #                             return format_html(
    #                                 '<em style="color: #d32f2f;">Preview error: {}</em>',
    #                                 str(e),
    #                             )
    #                     return format_html('<em style="color: #999;">No content</em>')
    #
    #                 preview_method.short_description = (
    #                     f"{field.verbose_name or field_name.title()} Preview"
    #                 )
    #                 preview_method.allow_tags = True
    #                 return preview_method
    #
    #             # Add method to class
    #             setattr(
    #                 self.__class__,
    #                 preview_method_name,
    #                 make_preview_method(field.name),
    #             )
    #
    #     # Add preview fields to readonly_fields if they exist
    #     if blocknote_fields:
    #         existing_readonly = list(getattr(self, "readonly_fields", []))
    #         preview_fields = [f"{field}_preview" for field in blocknote_fields]
    #         self.readonly_fields = existing_readonly + preview_fields

    def get_readonly_fields(self, request, obj=None):
        """Override to handle preview fields when creating new objects"""
        readonly_fields = super().get_readonly_fields(request, obj)

        # If creating a new object, remove preview fields from readonly
        if obj is None or obj.pk is None:
            # Filter out preview fields for new objects
            readonly_fields = [
                field for field in readonly_fields if not field.endswith("_preview")
            ]

        return readonly_fields


class BlockNoteModelAdmin(BlockNoteAdminMixin, BaseModelAdmin):
    """
    ModelAdmin that automatically handles BlockNote fields.
    Drop-in replacement for admin.ModelAdmin when you have BlockNote fields.
    """


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(BlockNoteModelAdmin):
    """Admin for DocumentTemplate with ownership-based permissions"""

    list_display = ["title", "user", "group", "show_in_menu", "created_at"]
    list_filter = ["group", "show_in_menu", "created_at"]
    search_fields = ["title", "user__username", "subtext"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        """All admin users can see all templates (for support)"""
        return super().get_queryset(request).select_related("user")

    def get_readonly_fields(self, request, obj=None):
        """Make everything readonly for non-superusers viewing others' templates"""
        readonly_fields = list(self.readonly_fields)

        # Only apply readonly logic for existing objects
        if obj is not None and not request.user.is_superuser:
            if obj.user != request.user:
                # Admin staff viewing someone else's template - everything readonly
                readonly_fields.extend(
                    [
                        "title",
                        "subtext",
                        "aliases",
                        "group",
                        "icon",
                        "content",
                        "user",
                        "show_in_menu",
                    ],
                )

        return readonly_fields

    def has_change_permission(self, request, obj=None):
        """Users can edit their own templates, all admin can view"""
        if obj is None:
            return True  # Permission to view changelist

        if request.user.is_superuser:
            return True

        # Non-superusers can view all but only edit their own
        return True  # View permission, edit controlled by readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Only superusers and template owners can delete"""
        if obj is None:
            return True  # Permission to view changelist

        if request.user.is_superuser:
            return True

        return obj.user == request.user

    def has_add_permission(self, request):
        """Any admin user can create templates (they'll own them)"""
        return True

    def save_model(self, request, obj, form, change):
        """Handle template saves with ownership validation"""
        if change:
            # Editing existing template
            if not request.user.is_superuser and obj.user != request.user:
                # This shouldn't happen due to readonly_fields, but extra safety
                raise PermissionDenied("You can only edit your own templates")

            # Check for ownership transfer (only superusers can do this)
            if "user" in form.changed_data and not request.user.is_superuser:
                raise PermissionDenied(
                    "Only superusers can transfer template ownership",
                )
        # Creating new template
        elif not request.user.is_superuser:
            obj.user = request.user

        super().save_model(request, obj, form, change)

    def delete_queryset(self, request, queryset):
        """Handle bulk delete with permission checks and cache refresh"""
        # Check permissions for bulk delete
        if not request.user.is_superuser:
            # Non-superusers can only bulk delete their own templates
            user_templates = queryset.filter(user=request.user)
            if user_templates.count() != queryset.count():
                raise PermissionDenied("You can only delete your own templates")

        # Capture users before deletion for cache refresh
        users_to_refresh = set(queryset.values_list("user", flat=True))

        # Perform the deletion
        super().delete_queryset(request, queryset)

        # Refresh cache for affected users
        for user_id in users_to_refresh:
            try:
                user = User.objects.get(id=user_id)
                DocumentTemplate.refresh_user_cache(user)
                logger.debug(f"Cache refreshed for user {user_id} after bulk delete")
            except User.DoesNotExist:
                logger.warning(
                    f"User {user_id} not found during cache refresh after delete",
                )
            except Exception as e:
                logger.exception(f"Error refreshing cache for user {user_id}: {e}")
