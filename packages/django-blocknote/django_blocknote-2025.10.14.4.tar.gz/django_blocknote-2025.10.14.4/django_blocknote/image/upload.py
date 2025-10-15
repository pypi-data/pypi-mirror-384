"""Image tools."""

from __future__ import annotations

from bisect import bisect
from io import BytesIO
from pathlib import Path

import filetype
import structlog
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import UploadedFile
from django.utils.module_loading import (
    import_string,
)
from PIL import (
    Image,
    ImageSequence,
    UnidentifiedImageError,
)

from django_blocknote.exceptions import (
    InvalidImageTypeError,
    PillowImageError,
)
from django_blocknote.helpers import get_storage_class

logger = structlog.get_logger(__name__)


def convert_image_to_webp(uploaded_file: UploadedFile) -> tuple[str, BytesIO]:
    """
    Converts an uploaded  validated image to WEBP format.

    Returns:
        A tuple containing the original filename with a .webp extension and
        the BytesIO stream of the converted image.
    """

    with uploaded_file.open("rb") as image_file:
        img = Image.open(image_file)

        # Handle multi-frame images (like GIFs or animated WebPs)
        if getattr(img, "is_animated", False):
            for i, frame in enumerate(ImageSequence.Iterator(img)):
                if getattr(frame, "mode", None) != "RGB":
                    img.seek(i)
                    img.paste(frame.convert("RGB"))

        # Handle single-frame images (like JPEG, PNG)
        elif getattr(img, "mode", None) != "RGB":
            img = img.convert("RGB")

        image_stream = BytesIO()
        quality = _determine_quality(uploaded_file.size)
        img.save(image_stream, format="WEBP", quality=quality, method=6)
        image_stream.seek(0)

        filename = Path(uploaded_file.name)
        webp_filename = filename.with_suffix(".webp")

        return str(webp_filename), image_stream


def _determine_quality(image_size: int) -> int:
    """Determines the optimal WebP image quality level based on file size.

    This function uses a binary search algorithm (`bisect`) to efficiently
    find the appropriate quality level based on pre-defined file size thresholds.

    Args:
        image_size: The size of the original image in bytes.

    Returns:
        The recommended quality level for WebP compression (1-100). Lower
        values mean smaller file size but potentially lower visual quality.
    """

    # File size thresholds (in bytes) and corresponding quality levels
    thresholds = [500_000, 1_000_000, 2_000_000, 10_000_000]
    qualities = [30, 20, 10, 5, 3]  # 3 is the default for sizes over 10 MB

    # Find the index where image_size would be inserted to maintain sorted order
    index = bisect(thresholds, image_size)
    # Return the corresponding quality level
    return qualities[index]


def image_verify(image):
    """Verifies whether an image file is valid and has a supported type.

    Validates an image file and ensures it falls within the permitted image
    types. The function checks for potential corruption, decompression bombs,
    and unsupported file formats.

    Args:
        image: The image file to verify. An image file-like object or a filename.

    Raises:
        PillowImageError: If the image is corrupt, too large, or cannot be verified.
        InvalidImageTypeError: If the image has an unsupported file type.
    """
    logger.debug(
        event="verify_image_file",
        msg="Checking Image passed to function",
        data={
            "image": image,
        },
    )
    # Fallback to `BlockNote` default image types if not set.
    permitted_image_types = settings.DJ_BN_PERMITTED_IMAGE_TYPES

    # filetype checks the file, not just the extension.
    kind = filetype.guess(image)

    match kind:
        case None:
            extension = "unknown"
        case _:
            extension = kind.extension.lower()

    if kind is None or extension not in permitted_image_types:
        error_msg = (
            f"Invalid image type, valid types {permitted_image_types}\n"
            f"It seems you have uploaded a '{extension}' filetype!"
        )
        logger.error(error_msg)
        raise InvalidImageTypeError(error_msg)

    try:
        logger.debug(
            event="verify_image_file",
            msg="Checking Image opens correctly",
            data={
                "image": image,
                "kind": kind,
            },
        )

        Image.open(image).verify()

        logger.debug(
            event="verify_image_file",
            msg="Checking Image has opened and closed correctly",
            data={
                "image": image,
                "kind": kind,
            },
        )

    except (
        FileNotFoundError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as e:
        error_messages = {
            FileNotFoundError: "This image file is not valid or corrupted.",
            UnidentifiedImageError: "This image file is corrupted.",
            Image.DecompressionBombError: "This image file is corrupted or too large to use.",
        }
        error_msg = error_messages[type(e)]
        logger.exception(
            event="verify_image_file",
            msg=error_msg,
        )
        raise PillowImageError(error_msg, e) from e


def handle_uploaded_image(request):
    """Handles an uploaded image, saving it to storage and returning its URL.

    Leverages a custom URL handler if specified in Django settings.

    Args:
        request: The Django request object containing the uploaded file.
                Available in `request.FILES["file"]`

    Returns:
        str: The URL where the uploaded image is stored
    """
    image = request.FILES.get("file", None)

    try:
        storage = get_storage_class()
    except ImproperlyConfigured as e:
        logger.exception(
            event="handle_uploaded_image_storage_error",
            msg="A valid storage system has not been configured",
            data={
                "error": str(e),
            },
        )
        return "A valid storage system has not been configured"

    # Get image formatter
    match getattr(settings, "DJ_BN_IMAGE_FORMATTER", ""):
        case "":
            convert_image = convert_image_to_webp
        case formatter_path:
            convert_image = import_string(formatter_path)

    # Get URL handler
    match getattr(settings, "DJ_BN_IMAGE_URL_HANDLER", ""):
        case "":
            get_image_url_and_optionally_save = None
        case handler_path:
            get_image_url_and_optionally_save = import_string(handler_path)

    # Process image formatting
    match (settings.DJ_BN_FORMAT_IMAGE, convert_image):
        case (True, formatter) if formatter:
            file_name, image = formatter(image)
            logger.debug(
                event="handle_uploaded_image_formatted",
                msg="Image converted using custom formatter",
                data={
                    "original_name": request.FILES.get("file").name,
                    "new_name": file_name,
                },
            )
        case _:
            file_name = image.name

    # Handle URL generation and optional saving
    match get_image_url_and_optionally_save:
        case None:
            img_saved = False
            image_url = file_name
        case handler:
            image_url, img_saved = handler(request, file_name, image)
            logger.debug(
                event="handle_uploaded_image_custom_handler",
                msg="Used custom URL handler",
                data={
                    "image_url": image_url,
                    "img_saved": img_saved,
                },
            )

    # Save to storage if not already saved
    match img_saved:
        case False:
            filename = storage.save(name=image_url, content=image)
            image_url = storage.url(filename)
            logger.debug(
                event="handle_uploaded_image_saved",
                msg="Image saved to storage",
                data={
                    "filename": filename,
                    "image_url": image_url,
                },
            )
        case True:
            logger.debug(
                event="handle_uploaded_image_already_saved",
                msg="Image already saved by custom handler",
                data={
                    "image_url": image_url,
                },
            )

    return image_url


def has_permission_to_upload_images(request) -> bool:
    """
    Checks if the user  has permission to upload images.

    Args:
        request (django.http.HttpRequest): The HTTP request object representing
        the user's interaction.

    Returns:
        bool: True if the user has permission to upload images, False otherwise.

    Behavior:
        - By default, all users have permission to upload images.
        - If the Django setting `DJ_BN_STAFF_ONLY_IMAGE_UPLOADS` is set to True,
          only staff users will have permission.
    """
    has_perms = True
    if (
        hasattr(settings, "DJ_BN_STAFF_ONLY_IMAGE_UPLOADS")
        and (settings.DJ_BN_STAFF_ONLY_IMAGE_UPLOADS)
        and not request.user.is_staff
    ):
        has_perms = False

    return has_perms
