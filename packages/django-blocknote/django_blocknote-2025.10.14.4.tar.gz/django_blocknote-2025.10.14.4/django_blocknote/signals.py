"""Django BlockNote signals"""

import structlog
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

from django_blocknote.models import DocumentTemplate

logger = structlog.get_logger(__name__)


@receiver(user_logged_out)
def invalidate_user_template_cache_on_logout(sender, request, user, **kwargs):
    """Invalidate user's template cache when they log out"""
    try:
        if user and user.is_authenticated:
            DocumentTemplate.invalidate_user_cache(user)
            logger.info(
                event="user_logged_out_cache_invalidated",
                msg="Template cache invalidated for user on logout",
                data={
                    "user_id": user.id,
                },
            )
    except Exception as e:
        logger.exception(
            event="user_logged_out_cache_invalidation_error",
            msg="Error invalidating template cache on user logout",
            data={
                "user_id": user.id if user else None,
                "error": e,
            },
        )
