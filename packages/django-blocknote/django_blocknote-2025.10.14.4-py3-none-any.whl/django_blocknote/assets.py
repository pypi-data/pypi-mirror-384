import json
from pathlib import Path

import structlog
from django.contrib.staticfiles import finders

logger = structlog.get_logger(__name__)


def get_vite_asset(asset_name):
    """
    Get the actual filename of a Vite asset from the manifest.
    Handles hashed filenames for cache busting.

    Args:
        asset_name (str): The original asset name (e.g., 'blocknote.js', 'style.css')

    Returns:
        str: The actual filename with hash (e.g., 'js/blocknote.abc123.js')
    """

    try:
        # Find the manifest file
        if not (
            manifest_path_str := finders.find("django_blocknote/.vite/manifest.json")
        ):
            # Fallback to original filename if no manifest
            return f"django_blocknote/{asset_name}"
        # Read the manifest
        manifest = Path(manifest_path_str)
        manifest = json.loads(manifest.read_text())

        # Handle specific asset lookups based on your manifest structure
        match asset_name:
            case "src/blocknote.ts":
                js_entry = manifest.get("src/blocknote.ts", {})
                if file_path := js_entry.get("file", ""):
                    asset_path = f"django_blocknote/{file_path}"
                else:
                    asset_path = "django_blocknote/js/blocknote.js"
                return asset_path

            case name if name == "blocknote.css" or name.endswith(".css"):
                css_entry = manifest.get("style.css", {})
                if file_path := css_entry.get("file", ""):
                    asset_path = f"django_blocknote/{file_path}"
                else:
                    asset_path = "django_blocknote/css/blocknote.css"
                return asset_path

            case _:
                # Final fallback: return original path
                return f"django_blocknote/{asset_name}"

    except FileNotFoundError:
        msg = f"Warning: Vite manifest file not found for {asset_name}"
        logger.exception(
            event="get_vite_asset_file_not_found",
            msg=msg,
            data={"asset_name": asset_name},
        )
        return f"django_blocknote/{asset_name}"

    except json.JSONDecodeError:
        msg = f"Warning: Invalid JSON in Vite manifest for {asset_name}"
        logger.exception(
            event="get_vite_asset_json_decode_error",
            msg=msg,
            data={"asset_name": asset_name},
        )
        return f"django_blocknote/{asset_name}"

    except KeyError as e:
        msg = f"Warning: Missing key in Vite manifest for {asset_name}: {e}"
        logger.exception(
            event="get_vite_asset_key_error",
            msg=msg,
            data={"asset_name": asset_name, "missing_key": str(e)},
        )
        return f"django_blocknote/{asset_name}"
