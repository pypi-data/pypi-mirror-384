import structlog

from django_blocknote.models import DocumentTemplate

logger = structlog.get_logger(__name__)


class TemplateCache:
    """Helper class for cache management commands"""

    @staticmethod
    def refresh_all_users():
        """Refresh template cache for all users (useful for management commands)"""
        users_with_templates = User.objects.filter(
            documenttemplate__isnull=False,
        ).distinct()

        refreshed_count = 0
        for user in users_with_templates:
            DocumentTemplate.refresh_user_cache(user)
            refreshed_count += 1

        logger.info(f"Refreshed template cache for {refreshed_count} users")
        return refreshed_count

    @staticmethod
    def clear_all_template_caches():
        """Clear all template caches (useful for cache reset)"""
        users_with_templates = User.objects.filter(
            documenttemplate__isnull=False,
        ).distinct()

        cleared_count = 0
        for user in users_with_templates:
            DocumentTemplate.invalidate_user_cache(user)
            cleared_count += 1

        logger.info(f"Cleared template cache for {cleared_count} users")
        return cleared_count
