"""django-blocknote models"""

import structlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models
from django.utils.translation import pgettext_lazy as _

from .fields import BlockNoteField

User = get_user_model()


logger = structlog.get_logger(__name__)


class UnusedImageURLS(models.Model):
    """Image urls that are no longer referenced in BlockNote"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "User",
        ),
        help_text=_(
            "Help text",
            "The user deleting the image",
        ),
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name=_(
            "Verbose name",
            "Image URL",
        ),
        help_text=_(
            "Help text",
            "The images url.",
        ),
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_(
            "Verbose name",
            "Created",
        ),
        help_text=_(
            "Help text",
            "The date and time when this record was created.",
        ),
    )

    deleted = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Deleted",
        ),
        help_text=_(
            "Help text",
            "The date and time when this record was deleted (if applicable).",
        ),
    )
    processing = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Processing",
        ),
        help_text=_(
            "Help text",
            "The date and time when this record was claimed for processing.",
        ),
    )
    deletion_error = models.TextField(
        blank=True,
        default="",
        verbose_name=_(
            "Verbose name",
            "Deletion Error",
        ),
        help_text=_(
            "Help text",
            "Error message if deletion failed (used for troubleshooting).",
        ),
    )
    processing_stats = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Processing Stats",
        ),
        help_text=_(
            "Help text",
            "Processing Stats",
        ),
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_(
            "Verbose name",
            "Retry Count",
        ),
        help_text=_(
            "Help text",
            "Number of times deletion has been attempted.",
        ),
    )

    class Meta:
        verbose_name = _(
            "Verbose name",
            "Django BlockNote Unused Images",
        )
        verbose_name_plural = _(
            "Verbose name",
            "Django BlockNote Unused Images",
        )
        app_label = "django_blocknote"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "image_url",
                ],
                name="djbn_image_url_no_duplicates",
                violation_error_message="Django CKeditor removed image url may not be duplicated.",
            ),
        ]

    def __str__(self):
        return str(self.image_url)


class DocumentTemplate(models.Model):
    ICON_CHOICES = [
        # General Document Types
        ("document", _("Choice", "Document")),
        ("template", _("Choice", "Template")),
        ("report", _("Choice", "Report")),
        ("letter", _("Choice", "Letter")),
        ("meeting", _("Choice", "Meeting")),
        ("checklist", _("Choice", "Checklist")),
        ("calendar", _("Choice", "Calendar")),
        ("book", _("Choice", "Book/Journal")),
        # Financial & Business
        ("chart", _("Choice", "Chart/Graph")),
        ("calculator", _("Choice", "Calculator")),
        ("currency", _("Choice", "Currency/Money")),
        ("bank", _("Choice", "Bank/Account")),
        ("receipt", _("Choice", "Receipt/Invoice")),
        ("trend", _("Choice", "Trend/Analytics")),
        ("briefcase", _("Choice", "Business/Portfolio")),
        ("scale", _("Choice", "Balance/Journal")),
        ("eye", _("Choice", "Watchlist/Monitor")),
        ("presentation", _("Choice", "Presentation")),
        ("spreadsheet", _("Choice", "Spreadsheet")),
        ("contract", _("Choice", "Contract/Agreement")),
        ("clock", _("Choice", "Time/Schedule")),
        ("bookmark", _("Choice", "Bookmark/Saved")),
    ]

    # BlockNote slash menu fields - these map directly to the slash menu item structure
    title = models.CharField(
        max_length=200,
        verbose_name=_(
            "Verbose name",
            "Title",
        ),
        help_text=_(
            "Help text",
            "The title displayed in the slash menu",
        ),
    )

    subtext = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Subtext",
        ),
        help_text=_(
            "Help text",
            "Brief description shown under title in slash menu (max 20 characters)",
        ),
    )

    aliases = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Aliases",
        ),
        help_text=_(
            "Help text",
            "Comma-separated search aliases for slash menu filtering",
        ),
    )

    group = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_(
            "Verbose name",
            "Group",
        ),
        help_text=_(
            "Help text",
            "Group name for organizing templates in slash menu (e.g., app name)",
        ),
    )

    icon = models.CharField(
        max_length=50,
        choices=ICON_CHOICES,
        default="template",
        verbose_name=_(
            "Verbose name",
            "Icon",
        ),
        help_text=_(
            "Help text",
            "Icon displayed in the slash menu",
        ),
    )

    # Template content and metadata
    content = BlockNoteField(
        menu_type="template",
        verbose_name=_(
            "Verbose name",
            "Template Content",
        ),
        help_text=_(
            "Help text",
            "BlockNote template blocks",
        ),
        editor_config={
            "placeholder": "Add your document template here ...",
            "animations": True,
        },
        image_upload_config={
            "img_model": "journals.JournalTradePlanImage",
        },
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "Owner",
        ),
        help_text=_(
            "Help text",
            "The user who created this template",
        ),
    )

    show_in_menu = models.BooleanField(
        default=True,
        verbose_name=_(
            "Verbose name",
            "Show in Menu",
        ),
        help_text=_(
            "Help text",
            "Whether this template appears in the slash menu",
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_(
            "Verbose name",
            "Created At",
        ),
        help_text=_(
            "Help text",
            "When this template was created",
        ),
    )

    class Meta:
        verbose_name = _(
            "Verbose name",
            "Document Template",
        )
        verbose_name_plural = _(
            "Verbose name",
            "Document Templates",
        )
        ordering = ["group", "title"]
        indexes = [
            models.Index(fields=["user", "show_in_menu"]),
            models.Index(fields=["group"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user}:{self.group}:{self.title}"

    def save(self, *args, **kwargs):
        """Override save to refresh cache"""
        try:
            super().save(*args, **kwargs)

            # Refresh cache for current user
            self.refresh_user_cache(self.user)

            logger.debug(
                event="template_saved",
                msg="Template saved and cache refreshed",
                data={
                    "template_id": self.pk,
                    "template_title": self.title,
                    "user_id": self.user.id,
                },
            )
        except Exception as e:
            logger.exception(
                event="template_save_error",
                msg="Error saving template or refreshing cache",
                data={
                    "template_title": getattr(self, "title", "Unknown"),
                    "user_id": getattr(self.user, "id", None)
                    if hasattr(self, "user")
                    else None,
                    "error": e,
                },
            )
            raise

    def delete(self, *args, **kwargs):
        """Override delete to refresh cache after template removal"""
        user = self.user
        title = self.title  # Capture before deletion
        template_id = self.pk

        try:
            super().delete(*args, **kwargs)

            # Refresh cache after deletion
            self.refresh_user_cache(user)

            logger.debug(
                event="template_deleted",
                msg="Template deleted and cache refreshed",
                data={
                    "template_id": template_id,
                    "template_title": title,
                    "user_id": user.id,
                },
            )
        except Exception as e:
            logger.exception(
                event="template_delete_error",
                msg="Error deleting template or refreshing cache",
                data={
                    "template_id": template_id,
                    "template_title": title,
                    "user_id": user.id if user else None,
                    "error": e,
                },
            )
            raise

    @classmethod
    def get_cached_templates(cls, user):
        """Get user templates from cache, fallback to DB"""
        cache_key = cls.get_cache_key(user.id)
        templates = cache.get(cache_key)

        if templates is None:
            logger.debug(
                event="template_cache_miss",
                msg="Cache miss for user templates, fetching from DB",
                data={
                    "user_id": user.id,
                    "cache_key": cache_key,
                },
            )
            templates = cls.refresh_user_cache(user)
        else:
            logger.debug(
                event="template_cache_hit",
                msg="Cache hit for user templates",
                data={
                    "user_id": user.id,
                    "template_count": len(templates),
                    "cache_key": cache_key,
                },
            )

        return templates

    @staticmethod
    def get_cache_key(user_id):
        """Generate cache key for user templates"""
        return f"djbn_templates_user_{user_id}"

    @classmethod
    def get_cache_timeout(cls):
        """
        Get cache timeout from settings with sensible default

        DJANGO_BLOCKNOTE_CACHE_TIMEOUT
        ------------------------------
        Controls how long template data is cached (in seconds).

        Default: 3600 (1 hour)

        Examples:
        - 0: Disable caching (always fetch from DB)
        - 300: Cache for 5 minutes (frequent changes)
        - 3600: Cache for 1 hour (default, balanced)
        - 86400: Cache for 24 hours (stable templates)

        Note: Templates are automatically refreshed when saved/deleted regardless of timeout.
        """
        return getattr(
            settings,
            "DJANGO_BLOCKNOTE_CACHE_TIMEOUT",
            3600,
        )  # 1 hour default

    @classmethod
    def refresh_user_cache(cls, user):
        """Refresh cache for a specific user's templates"""
        cache_key = cls.get_cache_key(user.id)

        try:
            # Get active templates for user with only needed fields
            templates_qs = (
                cls.objects.filter(user=user, show_in_menu=True)
                .values("pk", "title", "subtext", "aliases", "group", "icon", "content")
                .order_by("group", "title")
            )

            # Build templates list efficiently with list comprehension
            templates = []
            for template_data in templates_qs:
                # Parse comma-separated aliases string to get list
                aliases_str = template_data["aliases"].strip()
                if aliases_str:
                    aliases_list = [
                        alias.strip()
                        for alias in aliases_str.split(",")
                        if alias.strip()
                    ]
                else:
                    aliases_list = []

                templates.append(
                    {
                        "id": str(template_data["pk"]),
                        "title": template_data["title"],
                        "subtext": template_data["subtext"] or "",
                        "aliases": aliases_list,  # Already a list from JSON
                        "group": template_data["group"] or "",
                        "icon": template_data["icon"],
                        "content": template_data["content"],
                    },
                )

            # Use configurable cache timeout
            timeout = cls.get_cache_timeout()
            cache.set(cache_key, templates, timeout)

            logger.info(
                event="template_cache_refreshed",
                msg="Template cache refreshed for user",
                data={
                    "user_id": user.id,
                    "template_count": len(templates),
                    "cache_key": cache_key,
                    "cache_timeout": timeout,
                },
            )

            return templates

        except Exception as e:
            logger.exception(
                event="template_cache_refresh_error",
                msg="Error refreshing template cache for user",
                data={
                    "user_id": user.id,
                    "cache_key": cache_key,
                    "error": e,
                },
            )
            # Return empty list as fallback
            return []

    @classmethod
    def invalidate_user_cache(cls, user):
        """Invalidate cache for a specific user"""
        cache_key = cls.get_cache_key(user.id)

        try:
            cache.delete(cache_key)

            logger.info(
                event="template_cache_invalidated",
                msg="Template cache invalidated for user",
                data={
                    "user_id": user.id,
                    "cache_key": cache_key,
                },
            )
        except Exception as e:
            logger.exception(
                event="template_cache_invalidation_error",
                msg="Error invalidating template cache for user",
                data={
                    "user_id": user.id,
                    "cache_key": cache_key,
                    "error": e,
                },
            )
