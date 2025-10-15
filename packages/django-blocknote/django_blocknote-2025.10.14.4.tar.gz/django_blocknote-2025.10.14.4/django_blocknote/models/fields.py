import json
from typing import Any

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from django_blocknote.widgets import BlockNoteWidget


class BlockNoteField(models.JSONField):
    """A field for storing BlockNote editor content."""

    def __init__(
        self,
        editor_config: dict[str, Any] | None = None,
        image_upload_config: dict[str, Any] | None = None,
        image_removal_config: dict[str, Any] | None = None,
        menu_type: str = "",
        template_max_blocks: int | None = None,
        *args,
        **kwargs,
    ):
        # Use None as default and create new dict to avoid mutable default
        self.editor_config = editor_config or {}
        self.image_upload_config = image_upload_config or {}
        self.image_removal_config = image_removal_config or {}
        self.menu_type = menu_type or ""
        self.template_max_blocks = template_max_blocks

        # TODO: Update names and check still required.
        blocknote_settings = getattr(settings, "DJANGO_BLOCKNOTE", {})
        field_config = blocknote_settings.get("FIELD_CONFIG", {})

        # Apply defaults that aren't already specified
        for key, default_value in field_config.items():
            kwargs.setdefault(key, default_value)

        kwargs.setdefault("encoder", DjangoJSONEncoder)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = BlockNoteWidget(
            editor_config=self.editor_config,
            image_upload_config=self.image_upload_config,
            image_removal_config=self.image_removal_config,
            menu_type=self.menu_type,
            template_max_blocks=self.template_max_blocks,
        )
        return super().formfield(**kwargs)

    def from_db_value(
        self,
        value,
        expression,  # noqa: ARG002
        connection,  # noqa: ARG002
    ):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value
        return value
