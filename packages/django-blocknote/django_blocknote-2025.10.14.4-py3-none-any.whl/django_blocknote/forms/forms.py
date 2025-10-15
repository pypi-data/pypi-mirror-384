from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_blocknote.models import DocumentTemplate
from django_blocknote.widgets import BlockNoteWidget

from .mixins import BlockNoteModelFormMixin


class DocumentTemplateForm(BlockNoteModelFormMixin):
    """Form for creating and editing document templates with BlockNote content."""

    class Meta:
        model = DocumentTemplate
        fields = [
            "title",
            "subtext",
            "aliases",
            "group",
            "icon",
            "content",
            "show_in_menu",
        ]
        widgets = {
            "content": BlockNoteWidget(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter template title"),
                },
            ),
            "subtext": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Brief description (optional)"),
                    "maxlength": 20,
                },
            ),
            "aliases": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("e.g., memo, note, draft"),
                },
            ),
            "group": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("e.g., Work, Personal, Projects"),
                },
            ),
            "icon": forms.Select(
                attrs={
                    "class": "form-select",
                },
            ),
            "show_in_menu": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                },
            ),
        }
        labels = {
            "title": _("Template Title"),
            "subtext": _("Description"),
            "aliases": _("Search Keywords"),
            "group": _("Category"),
            "icon": _("Icon"),
            "content": _("Template Content"),
            "show_in_menu": _("Show in Slash Menu"),
        }
        help_texts = {
            "title": _("The name that will appear in the slash menu"),
            "subtext": _("Short description shown under the title (max 20 characters)"),
            "aliases": _("Comma-separated keywords to help users find this template"),
            "group": _("Optional category to organize your templates"),
            "icon": _("Icon displayed in the slash menu"),
            "content": _("Design your template using the BlockNote editor below"),
            "show_in_menu": _("Uncheck to hide this template from the slash menu"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial content for new templates
        if not self.instance.pk:
            self.fields["content"].initial = [
                {
                    "id": "initial-block",
                    "type": "paragraph",
                    "props": {
                        "textColor": "default",
                        "backgroundColor": "default",
                        "textAlignment": "left",
                    },
                    "content": [
                        {
                            "type": "text",
                            "text": "Start designing your template...",
                            "styles": {},
                        },
                    ],
                    "children": [],
                },
            ]

        # Make title field required and prominent
        self.fields["title"].required = True
        self.fields["title"].widget.attrs.update(
            {
                "autofocus": True,
                "required": True,
            },
        )

        # Add helpful placeholder for content
        self.fields["content"].widget.attrs.update(
            {
                "placeholder": _("Use the editor to create your template structure..."),
            },
        )

    def clean_title(self):
        """Validate template title."""
        title = self.cleaned_data.get("title")
        if not title:
            raise ValidationError(_("Template title is required."))

        title = title.strip()
        if len(title) < 2:
            raise ValidationError(
                _("Template title must be at least 2 characters long."),
            )

        return title

    def clean_subtext(self):
        """Validate and clean subtext field."""
        subtext = self.cleaned_data.get("subtext", "")
        if subtext:
            subtext = subtext.strip()
            if len(subtext) > 20:
                raise ValidationError(_("Description must be 20 characters or less."))
        return subtext

    def clean_aliases(self):
        """Clean and validate aliases field."""
        aliases = self.cleaned_data.get("aliases", "")
        if aliases:
            # Clean up the aliases - remove extra spaces, empty entries
            alias_list = [
                alias.strip() for alias in aliases.split(",") if alias.strip()
            ]
            # Rejoin with proper formatting
            aliases = ", ".join(alias_list)
        return aliases

    def clean_group(self):
        """Clean group field."""
        group = self.cleaned_data.get("group", "")
        if group:
            group = group.strip()
        return group

    def clean_content(self):
        """Validate BlockNote content structure."""
        content = self.cleaned_data.get("content")

        if not content:
            raise ValidationError(_("Template content cannot be empty."))

        # Basic validation - ensure it's a list
        if not isinstance(content, list):
            raise ValidationError(_("Invalid content format."))

        # Check if content is essentially empty (only contains empty paragraphs)
        if self._is_content_empty(content):
            raise ValidationError(_("Template must contain some content."))

        return content

    def _is_content_empty(self, content):
        """Check if BlockNote content is essentially empty."""
        if not content:
            return True

        for block in content:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type", "")
            block_content = block.get("content", [])

            # Skip empty paragraph blocks
            if block_type == "paragraph":
                if not block_content:
                    continue
                # Check if paragraph has any actual text
                has_text = False
                for item in block_content:
                    if isinstance(item, dict) and item.get("text", "").strip():
                        has_text = True
                        break
                if has_text:
                    return False
            else:
                # Non-paragraph blocks are considered content
                return False

        return True

    def save(self, commit=True):
        """Save the template with additional processing."""
        template = super().save(commit=False)

        # Ensure user is set (this should be handled by the view, but double-check)
        if hasattr(self, "user") and self.user:
            template.user = self.user

        if commit:
            template.save()

        return template


class DocumentTemplateQuickForm(BlockNoteModelFormMixin):
    """Simplified form for quick template creation."""

    class Meta:
        model = DocumentTemplate
        fields = ["title", "content"]
        widgets = {
            "content": BlockNoteWidget(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Template title"),
                    "autofocus": True,
                },
            ),
        }
        labels = {
            "title": _("Title"),
            "content": _("Content"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set some sensible defaults for quick creation
        self.fields["title"].required = True

        # Set default content
        if not self.instance.pk:
            self.fields["content"].initial = [
                {
                    "id": "quick-block",
                    "type": "paragraph",
                    "props": {
                        "textColor": "default",
                        "backgroundColor": "default",
                        "textAlignment": "left",
                    },
                    "content": [
                        {
                            "type": "text",
                            "text": "Quick template content...",
                            "styles": {},
                        },
                    ],
                    "children": [],
                },
            ]

    def save(self, commit=True):
        """Save with defaults for quick creation."""
        template = super().save(commit=False)

        # Set defaults for fields not in the form
        if not template.icon:
            template.icon = "template"
        if not template.group:
            template.group = _("Quick Templates")
        if template.show_in_menu is None:
            template.show_in_menu = True

        # Ensure user is set
        if hasattr(self, "user") and self.user:
            template.user = self.user

        if commit:
            template.save()

        return template


class DocumentTemplateSearchForm(forms.Form):
    """Form for searching and filtering templates."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search templates..."),
            },
        ),
        label=_("Search"),
    )

    group = forms.CharField(
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            },
        ),
        label=_("Category"),
    )

    show_hidden = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            },
        ),
        label=_("Include hidden templates"),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            # Populate group choices based on user's templates
            groups = (
                DocumentTemplate.objects.filter(user=user)
                .values_list("group", flat=True)
                .distinct()
            )

            group_choices = [("", _("All Categories"))]
            for group in groups:
                if group:
                    group_choices.append((group, group))

            self.fields["group"].widget = forms.Select(
                choices=group_choices,
                attrs={"class": "form-select"},
            )
