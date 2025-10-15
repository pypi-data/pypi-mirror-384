import json
import uuid

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from django_blocknote.assets import get_vite_asset
from django_blocknote.widgets import BlockNoteWidget

register = template.Library()


@register.simple_tag
def load_react(version="18", dev=None):
    """
    Load React and ReactDOM from CDN
    Usage:
        {% load_react %}  # Production version 18
        {% load_react version="17" %}  # Specific version
        {% load_react dev=True %}  # Development version (auto-detected if DEBUG=True)
    """
    # Auto-detect development mode if not specified
    if dev is None:
        dev = getattr(settings, "DEBUG", False)

    # Choose development or production build
    if dev:
        react_js = f"https://unpkg.com/react@{version}/umd/react.development.js"
        react_dom_js = (
            f"https://unpkg.com/react-dom@{version}/umd/react-dom.development.js"
        )
    else:
        react_js = f"https://unpkg.com/react@{version}/umd/react.production.min.js"
        react_dom_js = (
            f"https://unpkg.com/react-dom@{version}/umd/react-dom.production.min.js"
        )

    html = f"""
    <!-- React {version} ({"development" if dev else "production"}) -->
    <script crossorigin src="{react_js}"></script>
    <script crossorigin src="{react_dom_js}"></script>
    """
    return mark_safe(html)


@register.simple_tag
def load_blocknote_deps():
    """
    Load all BlockNote dependencies including React
    Usage:
        {% load_blocknote_deps %}
    """
    # Auto-detect development mode
    dev = getattr(settings, "DEBUG", False)

    # Load React first
    react_html = load_react(dev=dev)

    return mark_safe(react_html)


@register.inclusion_tag("django_blocknote/tags/react_debug.html")
def react_debug():
    """
    Show React debugging information (only in DEBUG mode)
    Usage:
        {% react_debug %}
    """
    return {"debug": getattr(settings, "DEBUG", False)}


@register.simple_tag
def blocknote_media():
    """
    Include BlockNote CSS and JS (without React dependencies)
    Uses Vite asset resolution for proper hashed filenames
    Usage:
        {% blocknote_media %}
    """
    # Get the actual asset URLs using Vite manifest
    css_url = static(get_vite_asset("blocknote.css"))
    js_url = static(get_vite_asset("src/blocknote.ts"))

    html = f"""
    <link rel="stylesheet" href="{css_url}">
    <script src="{js_url}"></script>
    """

    if getattr(settings, "DEBUG", False):
        html += f"""
        <!-- Debug: CSS from {get_vite_asset("blocknote.css")} -->
        <!-- Debug: JS from {get_vite_asset("src/blocknote.ts")} -->
        """

    return mark_safe(html)


@register.simple_tag
def blocknote_form_validation():
    """
    Include BlockNote form validation script
    Usage:
        {% blocknote_form_validation %}
    """
    script = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔧 BlockNote form validation initialized');

        // Find all forms that contain BlockNote textareas
        const formsWithBlockNote = document.querySelectorAll('form');

        formsWithBlockNote.forEach(form => {
            // Look for BlockNote textareas using multiple selectors
            const blockNoteTextareas = form.querySelectorAll(
                'textarea[id*="blocknote"], textarea[data-blocknote], textarea[id$="_editor"], .django-blocknote-wrapper textarea'
            );

            if (blockNoteTextareas.length > 0) {
                console.log(`📝 Found form with ${blockNoteTextareas.length} BlockNote field(s)`);

                form.addEventListener('submit', function(e) {
                    console.log('🔍 Validating BlockNote fields before form submission...');

                    let hasErrors = false;

                    blockNoteTextareas.forEach((textarea, index) => {
                        const value = textarea.value.trim();
                        const fieldName = textarea.name || textarea.id || `field_${index}`;

                        // If empty, set to valid empty array
                        if (!value) {
                            textarea.value = '[]';
                            console.log(`✅ Fixed empty textarea: ${fieldName}`);
                            return;
                        }

                        // Validate JSON
                        try {
                            const parsed = JSON.parse(value);
                            // Ensure it's an array
                            if (!Array.isArray(parsed)) {
                                throw new Error('Content must be an array');
                            }
                            console.log(`✅ Valid JSON for ${fieldName}`);
                        } catch (error) {
                            console.error(`❌ Invalid JSON in ${fieldName}:`, error);

                            // Try to fix common issues
                            try {
                                // If it's just text, wrap it in a paragraph block
                                const fixedContent = [{
                                    id: `fix-${Date.now()}-${index}`,
                                    type: 'paragraph',
                                    props: {},
                                    content: [{ type: 'text', text: value }],
                                    children: []
                                }];
                                textarea.value = JSON.stringify(fixedContent);
                                console.log(`🔧 Auto-fixed content for ${fieldName}`);
                            } catch (fixError) {
                                // Ultimate fallback
                                textarea.value = '[]';
                                console.log(`🔧 Reset to empty array: ${fieldName}`);
                            }
                        }
                    });

                    if (hasErrors) {
                        e.preventDefault();
                        alert('Please fix the errors in the form before submitting.');
                        return false;
                    }

                    console.log('✅ All BlockNote fields validated successfully');
                });
            }
        });

        // Also handle HTMX form submissions if present
        if (typeof htmx !== 'undefined') {
            document.addEventListener('htmx:beforeRequest', function(evt) {
                // Similar validation for HTMX requests
                const form = evt.target.closest('form');
                if (form) {
                    const blockNoteTextareas = form.querySelectorAll(
                        'textarea[id*="blocknote"], textarea[data-blocknote], textarea[id$="_editor"], .django-blocknote-wrapper textarea'
                    );

                    blockNoteTextareas.forEach(textarea => {
                        if (!textarea.value.trim()) {
                            textarea.value = '[]';
                        }
                    });
                }
            });
        }
    });
    </script>
    """

    return mark_safe(script)


@register.simple_tag
def blocknote_form_validation_debug():
    """
    Debug version that shows more information (only in DEBUG mode)
    Usage:
        {% blocknote_form_validation_debug %}
    """
    if not getattr(settings, "DEBUG", False):
        return blocknote_form_validation()  # Use regular version in production

    script = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        console.group('🔧 BlockNote Form Validation Debug');
        console.log('Initializing form validation...');

        const allForms = document.querySelectorAll('form');
        console.log(`Found ${allForms.length} total forms on page`);

        allForms.forEach((form, formIndex) => {
            const blockNoteTextareas = form.querySelectorAll(
                'textarea[id*="blocknote"], textarea[data-blocknote], textarea[id$="_editor"], .django-blocknote-wrapper textarea'
            );

            if (blockNoteTextareas.length > 0) {
                console.log(`📝 Form ${formIndex + 1}: Found ${blockNoteTextareas.length} BlockNote field(s)`);

                blockNoteTextareas.forEach((textarea, textareaIndex) => {
                    console.log(`  Field ${textareaIndex + 1}:`, {
                        id: textarea.id,
                        name: textarea.name,
                        value_length: textarea.value.length,
                        has_content: textarea.value.trim().length > 0
                    });
                });

                form.addEventListener('submit', function(e) {
                    console.group(`🔍 Validating Form ${formIndex + 1}`);

                    let hasErrors = false;

                    blockNoteTextareas.forEach((textarea, index) => {
                        const value = textarea.value.trim();
                        const fieldName = textarea.name || textarea.id || `field_${index}`;

                        console.log(`Checking field: ${fieldName}`);
                        console.log(`  Value length: ${value.length}`);

                        if (!value) {
                            textarea.value = '[]';
                            console.log(`  ✅ Fixed empty field`);
                            return;
                        }

                        try {
                            const parsed = JSON.parse(value);
                            if (!Array.isArray(parsed)) {
                                throw new Error('Content must be an array');
                            }
                            console.log(`  ✅ Valid JSON (${parsed.length} blocks)`);
                        } catch (error) {
                            console.error(`  ❌ Invalid JSON:`, error.message);

                            try {
                                const fixedContent = [{
                                    id: `fix-${Date.now()}-${index}`,
                                    type: 'paragraph',
                                    props: {},
                                    content: [{ type: 'text', text: value }],
                                    children: []
                                }];
                                textarea.value = JSON.stringify(fixedContent);
                                console.log(`  🔧 Auto-fixed content`);
                            } catch (fixError) {
                                textarea.value = '[]';
                                console.log(`  🔧 Reset to empty array`);
                            }
                        }
                    });

                    console.groupEnd();

                    if (hasErrors) {
                        e.preventDefault();
                        alert('Please fix the errors in the form before submitting.');
                        return false;
                    }
                });
            }
        });

        console.groupEnd();
    });
    </script>
    """

    return mark_safe(script)


@register.simple_tag
def blocknote_full(
    include_form_validation=True,
):
    """
    Load complete BlockNote setup (built assets + form validation)
    Usage:
        {% blocknote_full %}  # Includes form validation
        {% blocknote_full include_form_validation=False %}  # Skip form validation
    """
    # Load built assets instead of CDN
    media = blocknote_media()

    # Add form validation if requested
    form_validation = ""
    if include_form_validation:
        form_validation = blocknote_form_validation()

    debug = ""
    if getattr(settings, "DEBUG", False):
        debug = (
            """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.group('🔧 BlockNote Full Setup Debug');
            console.log('React available:', typeof React !== 'undefined');
            console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');
            console.log('DjangoBlockNote available:', typeof DjangoBlockNote !== 'undefined');
            console.log('Form validation included:', """
            + str(include_form_validation).lower()
            + """);
            // Check if assets loaded correctly
            const cssLoaded = Array.from(document.styleSheets).some(sheet => 
                sheet.href && sheet.href.includes('blocknote')
            );
            console.log('BlockNote CSS loaded:', cssLoaded);
            // Log current static files URLs for debugging
            console.log('Asset paths used:');
            console.log('  CSS:', document.querySelector('link[href*="blocknote"]')?.href);
            console.log('  JS:', 'Built assets (no CDN)');
            console.groupEnd();
        });
        </script>
        """
        )

    return mark_safe(media + form_validation + debug)


@register.simple_tag
def blocknote_deps():
    """
    DEPRECATED: This tag previously loaded CDN dependencies.
    Now returns empty string as dependencies are bundled in built assets.
    Use {% blocknote_full %} instead.
    """
    if getattr(settings, "DEBUG", False):
        return mark_safe("""
        <!-- 
        WARNING: {% blocknote_deps %} is deprecated. 
        Dependencies are now bundled in built assets.
        Use {% blocknote_full %} instead.
        -->
        """)
    return ""


@register.simple_tag
def load_blocknote_deps():
    """
    DEPRECATED: This function previously loaded CDN dependencies.
    Now returns empty string as dependencies are bundled in built assets.
    """
    if getattr(settings, "DEBUG", False):
        return """
        <!-- 
        CDN dependencies no longer needed - using built assets
        -->
        """
    return ""


@register.simple_tag
def blocknote_asset_debug():
    """
    Debug template tag to show asset resolution info
    Usage:
        {% blocknote_asset_debug %}
    """
    if not getattr(settings, "DEBUG", False):
        return ""

    css_asset = get_vite_asset("blocknote.css")
    js_asset = get_vite_asset("src/blocknote.ts")
    css_url = static(css_asset)
    js_url = static(js_asset)

    # Try to find manifest
    manifest_path = finders.find("django_blocknote/.vite/manifest.json")
    manifest_exists = manifest_path is not None

    # Check if built assets exist
    css_file_exists = finders.find(css_asset) is not None
    js_file_exists = finders.find(js_asset) is not None

    html = f"""
    <div style="background: #f8f9fa; border: 1px solid #dee2e6; padding: 1rem; margin: 1rem 0; font-family: monospace; font-size: 0.875rem;">
        <h4>🔧 BlockNote Asset Debug</h4>
        <p><strong>Build Status:</strong> {
        "✅ Built Assets" if manifest_exists else "❌ Missing Build"
    }</p>
        <p><strong>Manifest found:</strong> {manifest_exists}</p>
        {
        f"<p><strong>Manifest path:</strong> {manifest_path}</p>"
        if manifest_exists
        else ""
    }
        <hr>
        <p><strong>CSS asset:</strong> {css_asset} {
        "✅" if css_file_exists else "❌"
    }</p>
        <p><strong>CSS URL:</strong> {css_url}</p>
        <p><strong>JS asset:</strong> {js_asset} {"✅" if js_file_exists else "❌"}</p>
        <p><strong>JS URL:</strong> {js_url}</p>
        <hr>
        <p><strong>STATIC_URL:</strong> {settings.STATIC_URL}</p>
        <p><strong>STATICFILES_DIRS:</strong> {
        getattr(settings, "STATICFILES_DIRS", [])
    }</p>
        {
        '<p style="color: red;"><strong>⚠️ Assets missing:</strong> Run your build process to generate assets</p>'
        if not (css_file_exists and js_file_exists)
        else '<p style="color: green;"><strong>✅ All assets found</strong></p>'
    }
    </div>
    """
    return mark_safe(html)


def get_user_theme(user):
    """
    Robust user theme detection supporting multiple patterns:
    - user.profile.theme (field or property)
    - user.userprofile.theme (field or property)
    - user.preferences.theme (field or property)
    - user.theme_preference (direct field)
    """
    if not user or not user.is_authenticated:
        return None

    # List of possible theme attribute paths to check
    theme_paths = [
        ("profile", "theme"),
        ("userprofile", "theme"),
        ("preferences", "theme"),
        ("user_preferences", "theme"),
        ("settings", "theme"),
    ]

    # Check each possible path
    for relation_name, theme_attr in theme_paths:
        try:
            # Check if user has the relation
            if hasattr(user, relation_name):
                relation_obj = getattr(user, relation_name, None)
                # Handle case where relation exists but is None
                if relation_obj is None:
                    continue
                # Check if the relation object has the theme attribute
                if hasattr(relation_obj, theme_attr):
                    theme_value = getattr(relation_obj, theme_attr, None)
                    # Validate theme value
                    if theme_value and theme_value in ["light", "dark", "auto"]:
                        return theme_value
        except (AttributeError, ObjectDoesNotExist, TypeError):
            # Continue to next path if this one fails
            continue

    # Check for direct theme attributes on user
    direct_theme_attrs = ["theme", "theme_preference", "ui_theme", "color_scheme"]
    for attr_name in direct_theme_attrs:
        try:
            if hasattr(user, attr_name):
                theme_value = getattr(user, attr_name, None)
                if theme_value and theme_value in ["light", "dark", "auto"]:
                    return theme_value
        except (AttributeError, TypeError):
            continue

    return None


@register.simple_tag(takes_context=True)
def blocknote_viewer(
    context,
    content,
    container_id=None,
    css_class="blocknote-viewer",
    theme=None,
):
    """
    Simple viewer that uses BlockNoteWidget in readonly mode
    """
    # Get viewer config from settings
    viewer_config = getattr(
        settings,
        "DJ_BN_VIEWER_CONFIG",
        {
            "theme": "light",
            "animations": True,
        },
    )
    # Handle if it's accidentally a tuple
    if isinstance(viewer_config, tuple):
        viewer_config = viewer_config[0].copy()
    else:
        viewer_config = viewer_config.copy()

    # Theme priority: explicit > user preference > setting default
    if theme:
        # Explicit override has highest priority
        viewer_config["theme"] = theme
    else:
        # Try to get user's theme preference
        user = context.get("user") if context else None
        user_theme = get_user_theme(user)
        if user_theme:
            viewer_config["theme"] = user_theme

    # Create widget in readonly mode
    widget = BlockNoteWidget(
        mode="readonly",
        editor_config=viewer_config,
        attrs={
            "id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
            "class": css_class,
        },
    )

    # Render the widget with proper attrs
    field_name = "blocknote_content"
    content_json = json.dumps(content or [], cls=DjangoJSONEncoder, ensure_ascii=False)
    attrs = {
        "id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
        "class": css_class,
    }

    return widget.render(field_name, content_json, attrs=attrs)


# INFO: Can delete, here for reference

# @register.simple_tag(takes_context=True)
# def blocknote_viewer(
#     context,
#     content,
#     container_id=None,
#     css_class="blocknote-viewer",
#     theme=None,
# ):
#     """
#     Simple viewer that uses BlockNoteWidget in readonly mode
#     """
#     # Get viewer config from settings
#     viewer_config = getattr(
#         settings,
#         "DJ_BN_VIEWER_CONFIG",
#         {
#             "theme": "light",
#             "animations": True,
#         },
#     )
#     # Handle if it's accidentally a tuple
#     if isinstance(viewer_config, tuple):
#         viewer_config = viewer_config[0].copy()
#     else:
#         viewer_config = viewer_config.copy()
#
#     # Theme priority: explicit > user preference > setting default
#     if theme:
#         # Explicit override has highest priority
#         viewer_config["theme"] = theme
#     else:
#         # Try to get user's theme preference
#         user = context.get("user") if context else None
#         user_theme = get_user_theme(user)
#         if user_theme:
#             viewer_config["theme"] = user_theme
#
#     # Create widget in readonly mode
#     widget = BlockNoteWidget(
#         mode="readonly",
#         editor_config=viewer_config,
#         attrs={
#             "id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
#             "class": css_class,
#         },
#     )
#
#     # Render the widget
#     field_name = "blocknote_content"
#     content_json = json.dumps(content or [], cls=DjangoJSONEncoder, ensure_ascii=False)
#
#     return widget.render(field_name, content_json)


# @register.simple_tag(takes_context=True)
# def blocknote_viewer(
#     context,
#     content,
#     container_id=None,
#     css_class="blocknote-viewer",
#     theme=None,
# ):
#     """
#     Simple viewer that uses BlockNoteWidget in readonly mode
#     """
#     # Get viewer config from settings
#     viewer_config = getattr(
#         settings,
#         "DJ_BN_VIEWER_CONFIG",
#         {
#             "theme": "light",
#             "animations": True,
#         },
#     )
#     # Handle if it's accidentally a tuple
#     if isinstance(viewer_config, tuple):
#         viewer_config = viewer_config[0].copy()
#     else:
#         viewer_config = viewer_config.copy()
#
#     # Theme priority: explicit > user preference > setting default
#     if theme:
#         # Explicit override has highest priority
#         viewer_config["theme"] = theme
#     else:
#         # Try to get user's theme preference
#         user = context.get("user")
#         user_theme = get_user_theme(user)
#         if user_theme:
#             viewer_config["theme"] = user_theme
#
#     # Create widget in readonly mode
#     widget = BlockNoteWidget(
#         mode="readonly",
#         editor_config=viewer_config,
#         attrs={
#             "id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
#             "class": css_class,
#         },
#     )
#
#     # Render the widget
#     field_name = "blocknote_content"
#     content_json = json.dumps(content or [], cls=DjangoJSONEncoder, ensure_ascii=False)
#
#     return widget.render(field_name, content_json)
#
#
# # @register.inclusion_tag(
# #     "django_blocknote/tags/blocknote_viewer.html",
# #     takes_context=True,
# # )
# # def blocknote_viewer(
# #     context,
# #     content,
# #     container_id=None,
# #     css_class="blocknote-viewer",
# #     theme=None,
# # ):
# #     """
# #     Simple viewer with robust user theme detection
# #     """
# #     # Get viewer config from settings
# #     viewer_config = getattr(
# #         settings,
# #         "DJ_BN_VIEWER_CONFIG",
# #         {
# #             "theme": "light",
# #             "animations": True,
# #         },
# #     )
# #
# #     # Handle if it's accidentally a tuple
# #     if isinstance(viewer_config, tuple):
# #         viewer_config = viewer_config[0].copy()
# #     else:
# #         viewer_config = viewer_config.copy()
# #
# #     # Theme priority: explicit > user preference > setting default
# #     if theme:
# #         # Explicit override has highest priority
# #         viewer_config["theme"] = theme
# #     else:
# #         # Try to get user's theme preference
# #         user = context.get("user")
# #         user_theme = get_user_theme(user)
# #         if user_theme:
# #             viewer_config["theme"] = user_theme
# #
# #     default_upload_config = getattr(settings, "DJ_BN_IMAGE_UPLOAD_CONFIG", {})
# #     image_upload_config = default_upload_config.copy()
# #
# #     default_removal_config = getattr(settings, "DJ_BN_IMAGE_REMOVAL_CONFIG", {})
# #     image_removal_config = default_removal_config.copy()
# #
# #     # Add slash menu config
# #     default_slash_menu_config = getattr(settings, "DJ_BN_SLASH_MENU_CONFIG", {})
# #     slash_menu_config = default_slash_menu_config.copy()
# #
# #     if "uploadUrl" not in image_upload_config:
# #         try:
# #             image_upload_config["uploadUrl"] = reverse("django_blocknote:upload_image")
# #         except NoReverseMatch:
# #             image_upload_config["uploadUrl"] = "/django-blocknote/upload-image/"
# #
# #     image_upload_config.update({"showProgress": False})
# #
# #     if "removalUrl" not in image_removal_config:
# #         try:
# #             image_removal_config["removalUrl"] = reverse(
# #                 "django_blocknote:remove_image",
# #             )
# #         except NoReverseMatch:
# #             image_removal_config["removalUrl"] = "/django-blocknote/remove-image/"
# #
# #     # Serialize configs
# #     content_json = json.dumps(content or [], cls=DjangoJSONEncoder, ensure_ascii=False)
# #     editor_config_json = json.dumps(
# #         viewer_config,
# #         cls=DjangoJSONEncoder,
# #         ensure_ascii=False,
# #     )
# #     image_upload_config_json = json.dumps(
# #         image_upload_config,
# #         cls=DjangoJSONEncoder,
# #         ensure_ascii=False,
# #     )
# #     image_removal_config_json = json.dumps(
# #         image_removal_config,
# #         cls=DjangoJSONEncoder,
# #         ensure_ascii=False,
# #     )
# #     slash_menu_config_json = json.dumps(
# #         slash_menu_config,
# #         cls=DjangoJSONEncoder,
# #         ensure_ascii=False,
# #     )
# #
# #     return {
# #         "container_id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
# #         "css_class": css_class,
# #         "content_json": content_json,
# #         "has_content": bool(content),
# #         "editor_config": editor_config_json,
# #         "image_upload_config": image_upload_config_json,
# #         "image_removal_config": image_removal_config_json,
# #         "slash_menu_config": slash_menu_config_json,
# #     }
# #
# #
# # # NOTE: Prior to removal of the cdn as a source
# #
# # # @register.simple_tag
# # # def blocknote_full(
# # #     include_form_validation=True,
# # # ):
# # #     """
# # #     Load complete BlockNote setup (all dependencies + assets + form validation)
# # #     Usage:
# # #         {% blocknote_full %}  # Includes form validation
# # #         {% blocknote_full include_form_validation=False %}  # Skip form validation
# # #     """
# # #     deps = load_blocknote_deps()
# # #     media = blocknote_media()
# # #
# # #     # Add form validation if requested
# # #     form_validation = ""
# # #     if include_form_validation:
# # #         form_validation = blocknote_form_validation()
# # #
# # #     debug = ""
# # #     if getattr(settings, "DEBUG", False):
# # #         debug = (
# # #             """
# # #         <script>
# # #         document.addEventListener('DOMContentLoaded', function() {
# # #             console.group('🔧 BlockNote Full Setup Debug');
# # #             console.log('React available:', typeof React !== 'undefined');
# # #             console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');
# # #             console.log('DjangoBlockNote available:', typeof DjangoBlockNote !== 'undefined');
# # #             console.log('BlockNoteManager available:', typeof window.BlockNoteManager !== 'undefined');
# # #             console.log('Form validation included:', """
# # #             + str(include_form_validation).lower()
# # #             + """);
# # #
# # #             // Check if assets loaded correctly
# # #             const cssLoaded = Array.from(document.styleSheets).some(sheet =>
# # #                 sheet.href && sheet.href.includes('blocknote')
# # #             );
# # #             console.log('BlockNote CSS loaded:', cssLoaded);
# # #
# # #             // Log current static files URLs for debugging
# # #             console.log('Asset paths used:');
# # #             console.log('  CSS:', document.querySelector('link[href*="blocknote"]')?.href);
# # #             console.log('  JS:', 'Loaded via script tag');
# # #
# # #             console.groupEnd();
# # #         });
# # #         </script>
# # #         """
# # #         )
# # #
# # #     return mark_safe(deps + media + form_validation + debug)
# #
# #
# # # @register.simple_tag
# # # def blocknote_asset_debug():
# # #     """
# # #     Debug template tag to show asset resolution info
# # #     Usage:
# # #         {% blocknote_asset_debug %}
# # #     """
# # #     if not getattr(settings, "DEBUG", False):
# # #         return ""
# # #
# # #     css_asset = get_vite_asset("blocknote.css")
# # #     js_asset = get_vite_asset("src/blocknote.ts")
# # #     css_url = static(css_asset)
# # #     js_url = static(js_asset)
# # #
# # #     # Try to find manifest
# # #     manifest_path = finders.find("django_blocknote/.vite/manifest.json")
# # #     manifest_exists = manifest_path is not None
# # #
# # #     html = f"""
# # #     <div style="background: #f8f9fa; border: 1px solid #dee2e6; padding: 1rem; margin: 1rem 0; font-family: monospace; font-size: 0.875rem;">
# # #         <h4>🔧 BlockNote Asset Debug</h4>
# # #         <p><strong>Manifest found:</strong> {manifest_exists}</p>
# # #         {f"<p><strong>Manifest path:</strong> {manifest_path}</p>" if manifest_exists else ""}
# # #         <p><strong>CSS asset:</strong> {css_asset}</p>
# # #         <p><strong>CSS URL:</strong> {css_url}</p>
# # #         <p><strong>JS asset:</strong> {js_asset}</p>
# # #         <p><strong>JS URL:</strong> {js_url}</p>
# # #         <p><strong>STATIC_URL:</strong> {settings.STATIC_URL}</p>
# # #         <p><strong>STATICFILES_DIRS:</strong> {getattr(settings, "STATICFILES_DIRS", [])}</p>
# # #     </div>
# # #     """
# # #
# # #     return mark_safe(html)
# # #
# # #
# # # def get_user_theme(user):
# # #     """
# # #     Robust user theme detection supporting multiple patterns:
# # #     - user.profile.theme (field or property)
# # #     - user.userprofile.theme (field or property)
# # #     - user.preferences.theme (field or property)
# # #     - user.theme_preference (direct field)
# # #     """
# # #     if not user or not user.is_authenticated:
# # #         return None
# # #
# # #     # List of possible theme attribute paths to check
# # #     theme_paths = [
# # #         ("profile", "theme"),
# # #         ("userprofile", "theme"),
# # #         ("preferences", "theme"),
# # #         ("user_preferences", "theme"),
# # #         ("settings", "theme"),
# # #     ]
# # #
# # #     # Check each possible path
# # #     for relation_name, theme_attr in theme_paths:
# # #         try:
# # #             # Check if user has the relation
# # #             if hasattr(user, relation_name):
# # #                 relation_obj = getattr(user, relation_name, None)
# # #
# # #                 # Handle case where relation exists but is None
# # #                 if relation_obj is None:
# # #                     continue
# # #
# # #                 # Check if the relation object has the theme attribute
# # #                 if hasattr(relation_obj, theme_attr):
# # #                     theme_value = getattr(relation_obj, theme_attr, None)
# # #
# # #                     # Validate theme value
# # #                     if theme_value and theme_value in ["light", "dark", "auto"]:
# # #                         return theme_value
# # #
# # #         except (AttributeError, ObjectDoesNotExist, TypeError):
# # #             # Continue to next path if this one fails
# # #             continue
# # #
# # #     # Check for direct theme attributes on user
# # #     direct_theme_attrs = ["theme", "theme_preference", "ui_theme", "color_scheme"]
# # #
# # #     for attr_name in direct_theme_attrs:
# # #         try:
# # #             if hasattr(user, attr_name):
# # #                 theme_value = getattr(user, attr_name, None)
# # #                 if theme_value and theme_value in ["light", "dark", "auto"]:
# # #                     return theme_value
# # #         except (AttributeError, TypeError):
# # #             continue
# # #
# # #     return None
# # #
# # #
# # # @register.inclusion_tag(
# # #     "django_blocknote/tags/blocknote_viewer.html",
# # #     takes_context=True,
# # # )
# # # def blocknote_viewer(
# # #     context,
# # #     content,
# # #     container_id=None,
# # #     css_class="blocknote-viewer",
# # #     theme=None,
# # # ):
# # #     """
# # #     Simple viewer with robust user theme detection
# # #     """
# # #
# # #     # Get viewer config from settings
# # #     viewer_config = getattr(
# # #         settings,
# # #         "DJ_BN_VIEWER_CONFIG",
# # #         {
# # #             "theme": "light",
# # #             "animations": True,
# # #         },
# # #     )
# # #
# # #     # Handle if it's accidentally a tuple
# # #     if isinstance(viewer_config, tuple):
# # #         viewer_config = viewer_config[0].copy()
# # #     else:
# # #         viewer_config = viewer_config.copy()
# # #
# # #     # Theme priority: explicit > user preference > setting default
# # #     if theme:
# # #         # Explicit override has highest priority
# # #         viewer_config["theme"] = theme
# # #     else:
# # #         # Try to get user's theme preference
# # #         user = context.get("user")
# # #         user_theme = get_user_theme(user)
# # #         if user_theme:
# # #             viewer_config["theme"] = user_theme
# # #
# # #     default_upload_config = getattr(settings, "DJ_BN_IMAGE_UPLOAD_CONFIG", {})
# # #     image_upload_config = default_upload_config.copy()
# # #     default_removal_config = getattr(settings, "DJ_BN_IMAGE_REMOVAL_CONFIG", {})
# # #     image_removal_config = default_removal_config.copy()
# # #
# # #     if "uploadUrl" not in image_upload_config:
# # #         try:
# # #             image_upload_config["uploadUrl"] = reverse("django_blocknote:upload_image")
# # #         except NoReverseMatch:
# # #             image_upload_config["uploadUrl"] = "/django-blocknote/upload-image/"
# # #
# # #     image_upload_config.update({"showProgress": False})
# # #
# # #     if "removalUrl" not in image_removal_config:
# # #         try:
# # #             image_removal_config["removalUrl"] = reverse(
# # #                 "django_blocknote:remove_image",
# # #             )
# # #         except NoReverseMatch:
# # #             image_removal_config["removalUrl"] = "/django-blocknote/remove-image/"
# # #
# # #     # Serialize configs
# # #     content_json = json.dumps(content or [], cls=DjangoJSONEncoder, ensure_ascii=False)
# # #     editor_config_json = json.dumps(
# # #         viewer_config,
# # #         cls=DjangoJSONEncoder,
# # #         ensure_ascii=False,
# # #     )
# # #     image_upload_config_json = json.dumps(
# # #         image_upload_config,
# # #         cls=DjangoJSONEncoder,
# # #         ensure_ascii=False,
# # #     )
# # #     image_removal_config_json = json.dumps(
# # #         image_removal_config,
# # #         cls=DjangoJSONEncoder,
# # #         ensure_ascii=False,
# # #     )
# # #
# # #     return {
# # #         "container_id": container_id or f"blocknote_viewer_{uuid.uuid4().hex[:8]}",
# # #         "css_class": css_class,
# # #         "content_json": content_json,
# # #         "has_content": bool(content),
# # #         "editor_config": editor_config_json,
# # #         "image_upload_config": image_upload_config_json,
# # #         "image_removal_config": image_removal_config_json,
# # #     }
