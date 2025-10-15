import json
import uuid

import structlog
from django import forms
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import NoReverseMatch, reverse

from django_blocknote.assets import get_vite_asset

logger = structlog.get_logger(__name__)

templates = [
    {
        "id": "1",
        "title": "Meeting Notes",
        "subtext": "Agenda & actions",
        "aliases": ["meeting", "notes", "agenda"],
        "group": "Business",
        "icon": "meeting",
        "content": [
            {
                "id": "block-1",
                "type": "heading",
                "props": {"level": 1},
                "content": [{"type": "text", "text": "Meeting Title"}],
            },
            {
                "id": "block-2",
                "type": "paragraph",
                "content": [{"type": "text", "text": "Date: "}],
            },
            {
                "id": "block-3",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Attendees"}],
            },
            {
                "id": "block-4",
                "type": "bulletListItem",
                "content": [{"type": "text", "text": "Attendee 1"}],
            },
            {
                "id": "block-5",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Agenda"}],
            },
            {
                "id": "block-6",
                "type": "bulletListItem",
                "content": [{"type": "text", "text": "Item 1"}],
            },
            {
                "id": "block-7",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Action Items"}],
            },
            {
                "id": "block-8",
                "type": "checkListItem",
                "content": [{"type": "text", "text": "Action item 1"}],
            },
        ],
    },
    {
        "id": "2",
        "title": "Invoice Template",
        "subtext": "Billing format",
        "aliases": ["invoice", "bill", "payment"],
        "group": "Finance",
        "icon": "receipt",
        "content": [
            {
                "id": "block-1",
                "type": "heading",
                "props": {"level": 1},
                "content": [{"type": "text", "text": "INVOICE"}],
            },
            {
                "id": "block-2",
                "type": "paragraph",
                "content": [{"type": "text", "text": "Invoice #: "}],
            },
            {
                "id": "block-3",
                "type": "paragraph",
                "content": [{"type": "text", "text": "Date: "}],
            },
            {
                "id": "block-4",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Bill To:"}],
            },
            {
                "id": "block-5",
                "type": "paragraph",
                "content": [{"type": "text", "text": "Customer Name"}],
            },
        ],
    },
    {
        "id": "3",
        "title": "Daily Journal",
        "subtext": "Personal notes",
        "aliases": ["journal", "diary", "daily"],
        "group": "Personal",
        "icon": "book",
        "content": [
            {
                "id": "block-1",
                "type": "heading",
                "props": {"level": 1},
                "content": [{"type": "text", "text": "Daily Journal Entry"}],
            },
            {
                "id": "block-2",
                "type": "paragraph",
                "content": [{"type": "text", "text": "Date: "}],
            },
            {
                "id": "block-3",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Mood"}],
            },
            {
                "id": "block-4",
                "type": "paragraph",
                "content": [{"type": "text", "text": ""}],
            },
            {
                "id": "block-5",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Key Events"}],
            },
            {
                "id": "block-6",
                "type": "bulletListItem",
                "content": [{"type": "text", "text": "Event 1"}],
            },
            {
                "id": "block-7",
                "type": "heading",
                "props": {"level": 2},
                "content": [{"type": "text", "text": "Reflections"}],
            },
            {
                "id": "block-8",
                "type": "paragraph",
                "content": [{"type": "text", "text": ""}],
            },
        ],
    },
]


class BlockNoteWidget(forms.Textarea):
    """
    A rich text widget for BlockNote editor integration.
    Usage:
        class MyForm(forms.Form):
            content = forms.CharField(widget=BlockNoteWidget())
        # Or with custom config:
        content = forms.CharField(
            widget=BlockNoteWidget(
                editor_config={'placeholder': 'Start typing...'},
                menu_type='minimal'
            )
        )
    """

    template_name = "django_blocknote/blocknote.html"

    def __init__(
        self,
        attrs=None,
        editor_config=None,
        image_upload_config=None,
        image_removal_config=None,
        menu_type="default",
        mode="edit",
        template_max_blocks=None,
    ):
        # Set default CSS class
        default_attrs = {"class": "django-blocknote-editor"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

        # Store widget configuration
        self.editor_config = editor_config or {}
        self.image_upload_config = image_upload_config or {}
        self.image_removal_config = image_removal_config or {}
        self.menu_type = menu_type
        self.mode = mode
        self.template_max_blocks = template_max_blocks

    @property
    def media(self):
        """Define CSS and JS assets required by this widget."""
        return forms.Media(
            css={"all": [get_vite_asset("blocknote.css")]},
            js=[get_vite_asset("src/blocknote.ts")],
        )

    def format_value(self, value):
        """
        Convert the field value to the format expected by the widget template.
        BlockNote expects a list of block objects. Handle various input formats:
        - None/empty -> empty list
        - JSON string -> parsed list
        - Already a list -> return as-is
        """
        if value is None or value == "":
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(value, list):
            return value
        return []

    def value_from_datadict(self, data, files, name):
        """
        Extract the widget value from form data.
        BlockNote typically submits JSON, so we need to handle that.
        """
        value = data.get(name)
        if value:
            try:
                # Validate it's proper JSON
                json.loads(value)
                return value
            except (json.JSONDecodeError, TypeError):
                pass
        return value

    def get_context(self, name, value, attrs):
        """Build the template context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        # Generate unique ID for this editor instance
        widget_id = attrs.get("id", f"blocknote_{uuid.uuid4().hex[:8]}")

        def safe_json_dump(data, fallback="{}"):
            """Convert data to JSON with error handling."""
            try:
                return json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False)
            except (TypeError, ValueError):
                return fallback

        # 🔧 INTERFACE TRANSLATION: Convert Django config to BlockNote format
        translated_editor_config = self.translate_editor_config_to_blocknote(
            self.editor_config.copy() if self.editor_config else {}
        )

        # Collect and serialize all config data
        configs = {
            "editor_config": translated_editor_config,  # Now uses translated config
            "image_upload_config": self._get_image_upload_config(),
            "image_removal_config": self._get_image_removal_config(),
            "slash_menu_config": self._get_slash_menu_config(),
            "template_config": self._get_template_config(),
            "initial_content": self.format_value(value),
            "doc_templates": self._get_user_templates(),
        }

        # Add all configs to context as JSON
        for key, config_data in configs.items():
            fallback = "[]" if key in ["initial_content", "doc_templates"] else "{}"
            context["widget"][key] = safe_json_dump(config_data, fallback)

        # Add additional widget data
        context["widget"].update(
            {
                "editor_id": widget_id,
            }
        )

        # Add unified context variables for template
        context["mode"] = self.mode
        context["editor_id"] = widget_id
        context["has_content"] = bool(self.format_value(value))

        # Debug output in development
        if getattr(settings, "DEBUG", False):
            logger.debug(
                event="blocknote_widget_context",
                msg=f"BlockNote Widget Context: {widget_id}",
                data={
                    "widget_id": widget_id,
                    "mode": self.mode,
                    "editor_config": self.editor_config,
                    "translated_config": translated_editor_config,
                    "configs": {
                        k: v
                        if k not in ["initial_content"]
                        else (v[:150] + "..." if len(v) > 100 else v)
                        for k, v in configs.items()
                    },
                    "template_count": len(configs["doc_templates"])
                    if isinstance(configs["doc_templates"], list)
                    else 0,
                },
            )

        return context

    def _get_image_upload_config(self):
        """
        Get upload configuration with proper precedence:
        1. Widget config (from __init__) - highest priority
        2. Settings config - fallback
        3. Django URL resolution - only if no explicit URL provided
        """
        # Start with global settings
        base_config = getattr(settings, "DJ_BN_IMAGE_UPLOAD_CONFIG", {}).copy()

        # Apply widget-specific overrides (highest priority)
        base_config.update(self.image_upload_config)

        # Only try URL resolution if no explicit URL was provided
        if "uploadUrl" not in base_config:
            try:
                base_config["uploadUrl"] = reverse("django_blocknote:upload_image")
            except NoReverseMatch:
                logger.exception(
                    event="url_resolution_failed",
                    msg="No upload URL configured and django_blocknote URLs not included",
                    data={"url_name": "django_blocknote:upload_image"},
                )

        logger.debug(
            event="get_image_upload_config",
            msg="Using upload config with widget overrides",
            data={"config": base_config},
        )

        return base_config

    def _get_image_removal_config(self):
        """
        Get removal configuration with proper precedence:
        1. Widget config (from __init__) - highest priority
        2. Settings config - fallback
        3. Django URL resolution - only if no explicit URL provided
        """
        # Start with global settings
        base_config = getattr(settings, "DJ_BN_IMAGE_REMOVAL_CONFIG", {}).copy()

        # Apply widget-specific overrides (highest priority)
        base_config.update(self.image_removal_config)

        # Only try URL resolution if no explicit URL was provided
        if "removalUrl" not in base_config:
            try:
                base_config["removalUrl"] = reverse("django_blocknote:remove_image")
            except NoReverseMatch:
                logger.exception(
                    event="url_resolution_failed",
                    msg="No removal URL configured and django_blocknote URLs not included",
                    data={"url_name": "django_blocknote:remove_image"},
                )

        logger.debug(
            event="get_image_removal_config",
            msg="Using removal config with widget overrides",
            data={"config": base_config},
        )

        return base_config

    def _get_slash_menu_config(self):
        """
        Get slash menu configuration based on menu_type from global settings.
        Widget-specific config acts as override only.
        """
        # Get all configurations from settings
        all_configs = getattr(settings, "DJ_BN_SLASH_MENU_CONFIGS", {})

        # Get the specific config for this menu type
        if self.menu_type in all_configs:
            config = all_configs[self.menu_type].copy()
            msg = f"Found menu configuration for type: {self.menu_type}"
            logger.debug(
                event="get_slash_menu_config",
                msg=msg,
                data={"menu_type": self.menu_type, "config": config},
            )
        else:
            # Fallback to _default if menu_type not found
            config = all_configs.get("_default", {}).copy()
            msg = f"Menu type '{self.menu_type}' not found, using _default"
            logger.warning(
                event="get_slash_menu_config",
                msg=msg,
                data={
                    "requested_type": self.menu_type,
                    "available_types": list(all_configs.keys()),
                },
            )

        return config

    def _get_user_templates(self):
        """Get templates for the current user, with fallback to empty list"""
        # Get user from attrs (set by form mixin)
        logger.debug(
            event="blocknote_get_use_template",
            msg="Checking user exists",
            date={
                "user": self.attrs.get("user", "USER NOT FOUND"),
            },
        )
        user = self.attrs.get("user", None)
        if not user or not getattr(user, "is_authenticated", False):
            if settings.DEBUG:
                return templates
            return []

        try:
            # Import here to avoid circular imports
            from django_blocknote.models import DocumentTemplate

            return DocumentTemplate.get_cached_templates(user)
        except Exception as e:
            logger.exception(
                event="_get_user_templates",
                msg="Error loading user templates",
                data={
                    "error": str(e),
                },
            )
            return []

    def _get_template_config(self):
        """
        Get template configuration with proper precedence:
        1. Widget config (from __init__) - highest priority
        2. Settings config - fallback
        3. Hard defaults - final fallback
        """
        # Start with global settings
        base_config = getattr(settings, "DJ_BN_TEMPLATE_CONFIG", {}).copy()

        # Apply widget-specific overrides (highest priority)
        if self.template_max_blocks is not None:
            base_config["maxBlocks"] = self.template_max_blocks

        # Set defaults if nothing configured
        if "maxBlocks" not in base_config:
            base_config["maxBlocks"] = 1000

        # Always use our optimized chunk size (not configurable)
        base_config["chunkSize"] = 200  # Fixed implementation detail

        logger.debug(
            event="get_template_config",
            msg="Using template config with widget overrides",
            data={"config": base_config},
        )

        return base_config

    def _deep_merge(self, target, source):
        """Simple deep merge utility"""
        result = target.copy()
        for key, value in source.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def translate_editor_config_to_blocknote(self, django_config):
        """
        Interface method: Convert Django config to React-processable overrides
        React will handle merging with BlockNote defaults
        """
        logger.debug(
            event="translate_editor_config_input",
            msg="Converting Django config to BlockNote format",
            data={"input_config": django_config, "widget_mode": self.mode},
        )

        blocknote_config = django_config.copy()

        # Build dictionary overrides based on what Django provides
        dictionary_override = {}

        # Handle placeholder
        if "placeholder" in django_config:
            logger.debug(
                event="placeholder_found",
                msg="Processing placeholder configuration",
                data={"placeholder": django_config["placeholder"]},
            )

            dictionary_override["placeholders"] = {
                "default": django_config["placeholder"],
                "emptyDocument": django_config["placeholder"],
            }

            if "heading_placeholder" in django_config:
                dictionary_override["placeholders"]["heading"] = django_config[
                    "heading_placeholder"
                ]

            # Clean up Django-specific keys
            del blocknote_config["placeholder"]
            if "heading_placeholder" in blocknote_config:
                del blocknote_config["heading_placeholder"]
        else:
            logger.debug(
                event="placeholder_not_found",
                msg="No placeholder found in Django config",
            )

        # Handle any other Django dictionary customizations
        if "dictionary" in django_config:
            logger.debug(
                event="existing_dictionary_found",
                msg="Merging existing dictionary configuration",
                data={"existing_dictionary": django_config["dictionary"]},
            )
            dictionary_override = self._deep_merge(
                dictionary_override, django_config["dictionary"]
            )
            del blocknote_config["dictionary"]

        # Always send readonly state to React, even if no other overrides
        if self.mode == "readonly":
            blocknote_config["_django_readonly"] = True
            logger.debug(
                event="readonly_mode_set", msg="Added readonly flag to configuration"
            )

        # If we have any overrides, send them to React for processing
        if dictionary_override:
            blocknote_config["_django_dictionary_override"] = dictionary_override
            logger.debug(
                event="dictionary_override_added",
                msg="Added dictionary override to configuration",
                data={"dictionary_override": dictionary_override},
            )
        else:
            logger.debug(
                event="no_dictionary_override", msg="No dictionary override created"
            )

        logger.debug(
            event="translate_editor_config_output",
            msg="Completed Django config to BlockNote translation",
            data={"final_blocknote_config": blocknote_config},
        )

        return blocknote_config
