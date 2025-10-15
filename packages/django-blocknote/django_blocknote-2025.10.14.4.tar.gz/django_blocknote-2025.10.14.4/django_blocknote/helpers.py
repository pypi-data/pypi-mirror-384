"""django-blocknote helpers."""

import structlog
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import (
    import_string,
)

logger = structlog.get_logger(__name__)


def get_storage_class():
    """
    Determines the appropriate storage class for BlockNote based on settings.

    This function searches through a prioritized set of Django settings
    to dynamically determine the storage class to be used.

    Priority Order:
        1. DJ_BN_FILE_STORAGE setting
        2. DEFAULT_FILE_STORAGE
        3. STORAGES['default']

    Returns:
        The imported storage class

    Raises:
        ImproperlyConfigured: If no valid storage class configuration is found
    """
    # We can directly call DJ_BN_IMAGE_STORAGE because it is always available.
    dj_bn_img_storage_setting = settings.DJ_BN_IMAGE_STORAGE
    default_storage_setting = getattr(settings, "DEFAULT_FILE_STORAGE", None)
    storages_setting = getattr(settings, "STORAGES", {})
    default_storage_name = storages_setting.get("default", {}).get("BACKEND")

    # Determine storage class using priority order
    match (dj_bn_img_storage_setting, default_storage_setting, default_storage_name):
        case (storage_class, _, _) if storage_class:
            pass
        case (_, storage_class, _) if storage_class:
            pass
        case (_, _, storage_class) if storage_class:
            pass
        case _:
            storage_class = ""

    try:
        return _get_storage_object(storage_class)
    except ImproperlyConfigured as e:
        logger.exception(
            event="get_storage_class",
            msg="Failed to configure storage class",
            data={
                "storage_class": storage_class,
                "error": str(e),
            },
        )
        raise ImproperlyConfigured from e


def _get_storage_object(storage_class: str = ""):
    try:
        storage = import_string(storage_class)
        return storage()
    except ImportError as e:
        error_msg = (
            "Either DJ_BN_IMAGE_STORAGE, DEFAULT_FILE_STORAGE, "
            "or STORAGES['default'] setting is required."
        )
        raise ImproperlyConfigured(error_msg) from e
