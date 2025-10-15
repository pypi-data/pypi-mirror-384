import threading  # noqa: I001
from typing import Any
from pathlib import Path
from django.conf import settings
import structlog
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from django_blocknote.models import UnusedImageURLS
import urllib.parse
import uuid

User = get_user_model()
logger = structlog.get_logger(__name__)


def process_image_urls(image_urls: list[Any], user=None) -> dict[str, Any]:
    """
    Process a list of image URLs - the main business logic function.
    Args:
        image_urls: List of image URLs (may contain invalid types)
        user: User instance to associate with the URLs
    Returns:
        Dict with success/error status and appropriate data
    """
    try:
        # Validate and clean URLs
        validation_result = validate_image_urls(image_urls)
        if not validation_result["valid_urls"]:
            return {
                "success": False,
                "error": {
                    "message": "No valid image URLs found",
                    "code": "NO_VALID_URLS",
                    "details": {
                        "total_provided": len(image_urls),
                        "validation_errors": validation_result["errors"],
                    },
                },
                "status_code": 400,
            }
        valid_urls = validation_result["valid_urls"]
        validation_warnings = validation_result["errors"]

        # Save URLs to database - pass the user
        save_result = save_urls_to_database(valid_urls, user)

        # Build success response
        response_data = {
            "success": {
                "message": "Image URLs processed successfully",
                "total_provided": len(image_urls),
                "valid_urls": len(valid_urls),
                "created_count": save_result["created_count"],
                "duplicate_count": save_result["duplicate_count"],
                "processing_time": save_result["processing_time"],
            },
        }

        # Add warnings if any validation issues occurred
        if validation_warnings:
            response_data["success"]["warnings"] = validation_warnings
            response_data["success"]["warning_count"] = len(validation_warnings)

        if save_result["errors"]:
            response_data["success"]["save_errors"] = save_result["errors"]
            response_data["success"]["save_error_count"] = len(save_result["errors"])

        return {  # noqa: TRY300
            "success": True,
            "data": response_data,
            "status_code": 201,  # Created
        }

    except Exception as e:
        logger.exception(
            event="process_image_urls_error",
            msg="Error in process_image_urls",
            data={"error": str(e)},
        )
        return {
            "success": False,
            "error": {
                "message": "Failed to process image URLs",
                "code": "PROCESSING_ERROR",
                "details": str(e),
            },
            "status_code": 500,
        }


def validate_image_urls(image_urls: list[Any]) -> dict[str, list]:
    """
    Validate and clean a list of image URLs.
    Args:
        image_urls: List of potential URLs (may contain invalid types)
    Returns:
        Dict with valid_urls list and errors list
    """
    valid_urls = []
    errors = []

    for i, url in enumerate(image_urls):
        try:
            # Check if it's a string
            if not isinstance(url, str):
                errors.append(f"Index {i}: Expected string, got {type(url).__name__}")
                continue

            # Check if it's not empty
            if not url.strip():
                errors.append(f"Index {i}: Empty URL")
                continue

            # Decode URL to normalize it (removes %20, etc.)
            try:
                decoded_url = urllib.parse.unquote(url).strip()
            except Exception as decode_error:
                errors.append(f"Index {i}: Failed to decode URL - {decode_error!s}")
                continue

            # Check if it's a valid media URL (using decoded version)
            if not is_valid_media_url(decoded_url):
                errors.append(f"Index {i}: Invalid media URL format")
                continue

            # Check URL length (reasonable limit on decoded URL)
            if len(decoded_url) > 500:
                errors.append(f"Index {i}: URL too long (>{500} characters)")
                continue

            # Store the decoded/normalized URL
            valid_urls.append(decoded_url)

        except Exception as e:
            errors.append(f"Index {i}: Validation error - {e!s}")
            logger.warning(
                event="url_validation_error",
                msg="URL validation error",
                data={"index": i, "url": str(url)[:100], "error": str(e)},
            )

    logger.info(
        event="url_validation_completed",
        msg="URL validation completed",
        data={
            "total_provided": len(image_urls),
            "valid_count": len(valid_urls),
            "error_count": len(errors),
        },
    )

    return {
        "valid_urls": valid_urls,
        "errors": errors,
    }


def is_valid_media_url(url: str) -> bool:
    """
    Validate that a URL is a valid media URL for this application.
    Note: This function expects the URL to already be decoded.
    Args:
        url: Decoded URL string to validate
    Returns:
        True if valid media URL, False otherwise
    """
    try:
        # Get media URL from settings
        media_url = getattr(settings, "MEDIA_URL", "/media/")

        # Basic checks
        if not url or not isinstance(url, str):
            return False

        # Must contain media URL
        if media_url not in url:
            return False

        # Try to parse URL to check it's well-formed
        try:
            # Extract the file path part (URL should already be decoded)
            file_path = url.split(media_url)[1]

            # Check it's not empty after parsing
            if not file_path.strip():
                return False

            # Check for directory traversal attempts
            if ".." in file_path or file_path.startswith("/"):
                return False

            return True

        except (IndexError, ValueError):
            return False

    except Exception as e:
        logger.warning(
            event="url_validation_error",
            msg="URL validation error",
            data={"url": url[:100], "error": str(e)},
        )
        return False


def get_media_file_path(url: str) -> Path:
    """
    Extract the file system path from a media URL.
    Note: This function expects the URL to already be decoded.
    Args:
        url: Decoded media URL
    Returns:
        Path object for the file
    Raises:
        ValueError: If URL is invalid
    """
    if not is_valid_media_url(url):
        raise ValueError(f"Invalid media URL: {url}")

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_root = Path(getattr(settings, "MEDIA_ROOT", ""))

    # Extract file path from URL (URL should already be decoded)
    file_path = url.split(media_url)[1]
    return media_root / file_path


def get_processing_stats() -> dict[str, Any]:
    """
    Get statistics about unused image processing.
    Useful for monitoring and dashboards.
    """
    try:
        from django.db.models import Count

        stats = UnusedImageURLS.objects.aggregate(
            total_records=Count("id"),
            pending_deletion=Count("id", filter=models.Q(deleted__isnull=True)),
            deleted_records=Count("id", filter=models.Q(deleted__isnull=False)),
        )

        # Add some time-based stats
        recent_cutoff = timezone.now() - timezone.timedelta(days=7)
        stats["recent_additions"] = UnusedImageURLS.objects.filter(
            created__gte=recent_cutoff,
        ).count()

        return stats

    except Exception as e:
        logger.exception(
            event="processing_stats_error",
            msg="Error getting processing stats",
            data={"error": str(e)},
        )
        return {"error": str(e)}


def save_urls_to_database(valid_urls: list[str], user=None) -> dict[str, Any]:
    """
    Save valid URLs to the database, handling duplicates gracefully.
    Args:
        valid_urls: List of validated URL strings
        user: User instance to associate with the URLs
    Returns:
        Dict with save results and statistics
    """
    start_time = timezone.now()

    try:
        # Check for existing URLs to avoid duplicates
        existing_urls = get_existing_urls(valid_urls)
        new_urls = [url for url in valid_urls if url not in existing_urls]

        created_count = 0
        errors = []

        if new_urls:
            created_count = bulk_create_url_records(new_urls, errors, user)

        end_time = timezone.now()
        processing_time = (end_time - start_time).total_seconds()

        logger.info(
            event="database_save_completed",
            msg="Database save completed",
            data={
                "total_urls": len(valid_urls),
                "new_urls": len(new_urls),
                "created_count": created_count,
                "duplicate_count": len(existing_urls),
                "error_count": len(errors),
                "processing_time": processing_time,
                "user_id": user.id if user else None,
            },
        )

        return {
            "created_count": created_count,
            "duplicate_count": len(existing_urls),
            "errors": errors,
            "processing_time": round(processing_time, 3),
        }

    except Exception as e:
        logger.exception(
            event="database_save_error",
            msg="Error saving URLs to database",
            data={"error": str(e)},
        )
        return {
            "created_count": 0,
            "duplicate_count": 0,
            "errors": [f"Database error: {e!s}"],
            "processing_time": 0,
        }


def get_existing_urls(urls: list[str]) -> set:
    """
    Get set of URLs that already exist in database (not deleted).
    Args:
        urls: List of URLs to check
    Returns:
        Set of existing URLs
    """
    try:
        existing = UnusedImageURLS.objects.filter(
            image_url__in=urls,
            deleted__isnull=True,  # Only consider non-deleted records
        ).values_list("image_url", flat=True)
        return set(existing)

    except Exception:
        logger.exception(
            event="existing_urls_check_error",
            msg="Error checking existing URLs",
            data={},
        )
        # Return empty set so we attempt to create (bulk_create will handle conflicts)
        return set()


def bulk_create_url_records(urls: list[str], errors: list[str], user=None) -> int:
    """
    Bulk create URL records in database.
    Args:
        urls: List of URLs to create
        errors: List to append any errors to
        user: User instance to associate with the URLs
    Returns:
        Number of records actually created
    """
    try:
        # Create instances - include user
        instances = [UnusedImageURLS(image_url=url, user=user) for url in urls]

        # Get batch size from settings
        batch_size = getattr(settings, "DJ_BN_BULK_CREATE_BATCH_SIZE", 50)

        # Bulk create with conflict handling
        with transaction.atomic():
            created_instances = UnusedImageURLS.objects.bulk_create(
                instances,
                batch_size=batch_size,
                ignore_conflicts=True,  # Handle any race condition duplicates
            )

        created_count = len(created_instances)

        logger.debug(
            event="bulk_create_completed",
            msg="Bulk create completed",
            data={
                "requested_count": len(urls),
                "created_count": created_count,
                "batch_size": batch_size,
                "user_id": user.id if user else None,
            },
        )

        return created_count  # noqa: TRY300

    except Exception as e:
        error_msg = f"Bulk create failed: {e!s}"
        errors.append(error_msg)
        logger.exception(
            event="bulk_create_error", msg="Bulk create error", data={"error": str(e)}
        )
        return 0


def trigger_cleanup_if_needed() -> None:
    """
    Check if cleanup is needed and trigger background cleanup if threshold reached.
    This is called from the view's finally block.
    """
    try:
        # Check if deletion is enabled
        if not getattr(settings, "DJ_BN_IMAGE_DELETION", False):
            return

        # Get threshold setting
        threshold = getattr(settings, "DJ_BN_BULK_DELETE_BATCH_SIZE", 20)

        # Quick count check (fast query) - only count truly pending ones
        pending_count = UnusedImageURLS.objects.filter(
            deleted__isnull=True,
            processing__isnull=True,  # Not currently being processed
        ).count()

        logger.debug(
            event="cleanup_threshold_check",
            msg="Cleanup threshold check",
            data={
                "pending_count": pending_count,
                "threshold": threshold,
                "cleanup_needed": pending_count >= threshold,
            },
        )

        if pending_count >= threshold:
            # Trigger async cleanup
            logger.info(
                event="triggering_async_cleanup",
                msg="Triggering async cleanup",
                data={"pending_count": pending_count, "threshold": threshold},
            )

            # Start cleanup in background thread
            cleanup_thread = threading.Thread(
                target=_background_cleanup_batch,
                args=(threshold,),
                name="ImageCleanup",
                daemon=True,
            )
            cleanup_thread.start()

    except Exception:
        logger.exception(
            event="cleanup_trigger_error", msg="Error in cleanup trigger", data={}
        )


def _background_cleanup_batch(batch_size: int) -> None:
    """
    Background cleanup function that implements claim-and-process pattern.
    Runs in a separate thread, not blocking the main request.
    """
    start_time = timezone.now()
    batch_id = f"cleanup_{start_time.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    try:
        logger.info(
            event="background_cleanup_started",
            msg="Starting background cleanup batch",
            data={"batch_size": batch_size, "batch_id": batch_id},
        )

        # Step 1: Claim URLs atomically
        claim_start_time = timezone.now()
        claimed_urls = _claim_urls_for_deletion(batch_size, batch_id)
        claim_end_time = timezone.now()
        claim_time = (claim_end_time - claim_start_time).total_seconds()

        if not claimed_urls:
            logger.debug(
                event="no_urls_to_cleanup",
                msg="No URLs to clean up",
                data={"claim_time": round(claim_time, 3), "batch_id": batch_id},
            )
            return

        logger.info(
            event="urls_claimed_for_deletion",
            msg="Claimed URLs for deletion",
            data={
                "claimed_count": len(claimed_urls),
                "claim_time": round(claim_time, 3),
                "batch_id": batch_id,
            },
        )

        # Step 2: Process deletions (this can take time with S3)
        deletion_start_time = timezone.now()
        deletion_results = _process_url_deletions(claimed_urls, batch_id)
        deletion_end_time = timezone.now()
        deletion_time = (deletion_end_time - deletion_start_time).total_seconds()

        # Step 3: Handle results (reset failed ones)
        reset_start_time = timezone.now()
        _handle_deletion_results(deletion_results)
        reset_end_time = timezone.now()
        reset_time = (reset_end_time - reset_start_time).total_seconds()

        end_time = timezone.now()
        total_processing_time = (end_time - start_time).total_seconds()

        logger.info(
            event="background_cleanup_completed",
            msg="Background cleanup completed",
            data={
                "batch_id": batch_id,
                "total_processed": len(claimed_urls),
                "successful": deletion_results["success_count"],
                "failed": deletion_results["error_count"],
                "processing_times": {
                    "claim_time": round(claim_time, 3),
                    "deletion_time": round(deletion_time, 3),
                    "reset_time": round(reset_time, 3),
                    "total_time": round(total_processing_time, 3),
                },
            },
        )

    except Exception as e:
        end_time = timezone.now()
        total_processing_time = (end_time - start_time).total_seconds()
        logger.exception(
            event="background_cleanup_error",
            msg="Error in background cleanup batch",
            data={
                "batch_id": batch_id,
                "processing_time": round(total_processing_time, 3),
                "error": str(e),
            },
        )


def _claim_urls_for_deletion(batch_size: int, batch_id: str) -> list[dict[str, Any]]:
    """
    Atomically claim URLs for deletion by marking them as deleted.
    This prevents race conditions between multiple cleanup processes.
    Returns:
        List of claimed URL records with id and image_url
    """
    claimed_urls = []

    try:
        with transaction.atomic():
            # Get URLs to claim (using select_for_update to prevent races)
            url_records = list(
                UnusedImageURLS.objects.select_for_update()
                .filter(
                    deleted__isnull=True,
                    processing__isnull=True,  # Only claim unprocessed URLs
                )
                .order_by("created")[
                    # Process oldest first
                    :batch_size
                ]
                .values("id", "image_url"),
            )

            if not url_records:
                return []

            # Extract IDs for batch update
            url_ids = [record["id"] for record in url_records]

            # Initialize processing stats for each URL
            processing_start_time = timezone.now()
            initial_stats = {
                "batch_id": batch_id,
                "processing_started_at": processing_start_time.isoformat(),
                "claim_time": timezone.now().isoformat(),
                "retry_attempt": 1,
            }

            # Mark all as processing (claim them)
            updated_count = UnusedImageURLS.objects.filter(
                id__in=url_ids
            ).update(
                processing=processing_start_time,  # Mark as being processed
                deletion_error="",  # Clear any previous errors (empty string instead of None)
                processing_stats=initial_stats,
            )

            logger.debug(
                event="urls_claimed_for_processing",
                msg="URLs claimed for processing",
                data={
                    "batch_id": batch_id,
                    "requested_batch_size": batch_size,
                    "found_urls": len(url_records),
                    "updated_count": updated_count,
                },
            )

            claimed_urls = url_records

    except Exception:
        logger.exception(
            event="claim_urls_error",
            msg="Error claiming URLs for deletion",
            data={"batch_id": batch_id},
        )

    return claimed_urls


def _process_url_deletions(
    claimed_urls: list[dict[str, Any]], batch_id: str
) -> dict[str, Any]:
    """
    Process the actual file deletions for claimed URLs.
    This is the slow part (S3 operations) that happens outside the transaction.
    Returns:
        Dict with success/error counts and detailed results
    """
    start_time = timezone.now()
    success_count = 0
    error_count = 0
    error_details = []  # For resetting failed URLs
    individual_deletion_times = []

    for url_record in claimed_urls:
        file_start_time = timezone.now()
        try:
            url_id = url_record["id"]
            image_url = url_record["image_url"]

            # Attempt to delete the file
            file_deletion_result = _delete_single_file(image_url)
            file_end_time = timezone.now()
            file_deletion_time = (file_end_time - file_start_time).total_seconds()
            individual_deletion_times.append(file_deletion_time)

            # Update processing stats regardless of success/failure
            _update_processing_stats(
                url_id,
                batch_id,
                file_deletion_time,
                file_deletion_result["success"],
                file_deletion_result.get("error"),
                file_deletion_result.get("file_size"),
            )

            if file_deletion_result["success"]:
                success_count += 1
                # Mark as successfully deleted
                _mark_as_deleted(url_id)
                logger.debug(
                    event="file_deleted_successfully",
                    msg="File deleted successfully",
                    data={
                        "url_id": url_id,
                        "image_url": image_url,
                        "deletion_time": round(file_deletion_time, 3),
                        "batch_id": batch_id,
                        "file_size": file_deletion_result.get("file_size"),
                    },
                )
            else:
                error_count += 1
                error_msg = file_deletion_result.get(
                    "error", "File not found or deletion failed"
                )
                error_details.append(
                    {
                        "url_id": url_id,
                        "image_url": image_url,
                        "error": error_msg,
                    },
                )
                logger.warning(
                    event="file_deletion_failed",
                    msg="File deletion failed",
                    data={
                        "url_id": url_id,
                        "image_url": image_url,
                        "error": error_msg,
                        "deletion_time": round(file_deletion_time, 3),
                        "batch_id": batch_id,
                    },
                )

        except Exception as e:
            file_end_time = timezone.now()
            file_deletion_time = (file_end_time - file_start_time).total_seconds()
            individual_deletion_times.append(file_deletion_time)

            # Update processing stats for exception case
            _update_processing_stats(
                url_record["id"], batch_id, file_deletion_time, False, str(e)
            )

            error_count += 1
            error_msg = f"Exception during deletion: {e!s}"
            error_details.append(
                {
                    "url_id": url_record["id"],
                    "image_url": url_record["image_url"],
                    "error": error_msg,
                },
            )
            logger.exception(
                event="file_deletion_exception",
                msg="Exception during file deletion",
                data={
                    "url_id": url_record["id"],
                    "image_url": url_record["image_url"],
                    "error": str(e),
                    "deletion_time": round(file_deletion_time, 3),
                    "batch_id": batch_id,
                },
            )

    end_time = timezone.now()
    total_processing_time = (end_time - start_time).total_seconds()

    # Calculate timing stats
    avg_deletion_time = (
        sum(individual_deletion_times) / len(individual_deletion_times)
        if individual_deletion_times
        else 0
    )
    max_deletion_time = (
        max(individual_deletion_times) if individual_deletion_times else 0
    )
    min_deletion_time = (
        min(individual_deletion_times) if individual_deletion_times else 0
    )

    logger.info(
        event="url_deletions_processed",
        msg="URL deletions processing completed",
        data={
            "batch_id": batch_id,
            "total_urls": len(claimed_urls),
            "successful_deletions": success_count,
            "failed_deletions": error_count,
            "processing_times": {
                "total_time": round(total_processing_time, 3),
                "avg_deletion_time": round(avg_deletion_time, 3),
                "max_deletion_time": round(max_deletion_time, 3),
                "min_deletion_time": round(min_deletion_time, 3),
            },
        },
    )

    return {
        "success_count": success_count,
        "error_count": error_count,
        "error_details": error_details,
        "processing_time": round(total_processing_time, 3),
        "timing_stats": {
            "avg_deletion_time": round(avg_deletion_time, 3),
            "max_deletion_time": round(max_deletion_time, 3),
            "min_deletion_time": round(min_deletion_time, 3),
        },
    }


def _delete_single_file(image_url: str) -> dict[str, Any]:
    """
    Delete a single file from storage.
    Returns:
        Dict with success status, error message, and file info
    """
    try:
        # Extract file path from URL (URL should already be normalized)
        file_path = get_media_file_path(image_url)
        file_size = None

        # Check if file exists and get size
        if default_storage.exists(str(file_path)):
            try:
                file_size = default_storage.size(str(file_path))
            except Exception:
                pass  # Size not critical, continue with deletion

            # Delete the file
            default_storage.delete(str(file_path))
            return {
                "success": True,
                "file_size": file_size,
                "file_path": str(file_path),
            }

        # File doesn't exist (might have been manually deleted)
        logger.debug(
            event="file_not_found_during_deletion",
            msg="File not found during deletion",
            data={"image_url": image_url, "file_path": str(file_path)},
        )
        return {
            "success": False,
            "error": "File not found",
            "file_path": str(file_path),
        }

    except Exception as e:
        logger.exception(
            event="delete_file_error",
            msg="Error deleting file",
            data={"image_url": image_url, "error": str(e)},
        )
        return {"success": False, "error": str(e)}


def _update_processing_stats(
    url_id: int,
    batch_id: str,
    deletion_time: float,
    success: bool,
    error: str = None,
    file_size: int = None,
) -> None:
    """
    Update the processing_stats JSONField for a URL record.
    """
    try:
        completion_time = timezone.now()

        # Get current stats to preserve existing data
        url_record = UnusedImageURLS.objects.filter(id=url_id).first()
        if not url_record:
            return

        current_stats = url_record.processing_stats or {}

        # Update stats with new information
        updated_stats = {
            **current_stats,  # Preserve existing stats
            "deletion_time": round(deletion_time, 3),
            "deletion_completed_at": completion_time.isoformat(),
            "deletion_success": success,
            "storage_method": "s3"
            if "s3" in str(default_storage.__class__)
            else "local",
        }

        if file_size is not None:
            updated_stats["file_size"] = file_size

        if error:
            updated_stats["deletion_error"] = error

        if success:
            updated_stats["deletion_completed"] = True

        # Calculate total processing time if we have start time
        if "processing_started_at" in current_stats:
            try:
                from django.utils.dateparse import parse_datetime

                start_time = parse_datetime(current_stats["processing_started_at"])
                if start_time:
                    total_time = (completion_time - start_time).total_seconds()
                    updated_stats["total_processing_time"] = round(total_time, 3)
            except Exception:
                pass  # Not critical if we can't calculate total time

        # Update the record
        UnusedImageURLS.objects.filter(id=url_id).update(processing_stats=updated_stats)

    except Exception as e:
        logger.exception(
            event="update_processing_stats_error",
            msg="Error updating processing stats",
            data={"url_id": url_id, "error": str(e)},
        )


def _mark_as_deleted(url_id: int) -> None:
    """
    Mark a URL record as successfully deleted.
    """
    try:
        UnusedImageURLS.objects.filter(id=url_id).update(
            deleted=timezone.now(),
            processing=None,  # Clear processing flag
        )
    except Exception as e:
        logger.exception(
            event="mark_as_deleted_error",
            msg="Error marking URL as deleted",
            data={"url_id": url_id, "error": str(e)},
        )


def _handle_deletion_results(deletion_results: dict[str, Any]) -> None:
    """
    Handle the results of deletion attempts.
    Reset failed deletions so they can be retried later.
    """
    error_details = deletion_results.get("error_details", [])
    if not error_details:
        logger.debug(
            event="all_deletions_successful",
            msg="All deletions were successful, no cleanup needed",
            data={"successful_count": deletion_results.get("success_count", 0)},
        )
        return  # All deletions succeeded

    start_time = timezone.now()

    try:
        # Reset failed deletions in a transaction
        with transaction.atomic():
            for error_detail in error_details:
                url_id = error_detail["url_id"]
                error_message = error_detail["error"]

                # Reset the processing flag and store error info
                UnusedImageURLS.objects.filter(id=url_id).update(
                    processing=None,  # Reset processing flag to allow retry
                    deletion_error=error_message,  # Store error for investigation
                    retry_count=models.F("retry_count") + 1,  # Increment retry counter
                )

        end_time = timezone.now()
        reset_processing_time = (end_time - start_time).total_seconds()

        logger.info(
            event="failed_deletions_reset",
            msg="Reset failed deletions for retry",
            data={
                "failed_count": len(error_details),
                "processing_time": round(reset_processing_time, 3),
            },
        )

    except Exception as e:
        end_time = timezone.now()
        reset_processing_time = (end_time - start_time).total_seconds()
        logger.exception(
            event="reset_failed_deletions_error",
            msg="Error resetting failed deletions",
            data={
                "failed_count": len(error_details),
                "error": str(e),
                "processing_time": round(reset_processing_time, 3),
            },
        )
