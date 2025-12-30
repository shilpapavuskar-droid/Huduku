
import asyncio
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # avoid running in migrations
        from django.conf import settings
        if not getattr(settings, "RUN_BOOTSTRAP", True):
            return

        from .bootstrap import bootstrap_categories

        async def run_bootstrap_async():
            try:
                # run sync DB code in a worker thread
                await asyncio.to_thread(bootstrap_categories)
            except Exception as exc:
                logger.exception("Error running bootstrap_categories: %s", exc)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # no running loop: create one and run async task
            asyncio.run(run_bootstrap_async())
        else:
            # running loop exists: schedule task on it
            loop.create_task(run_bootstrap_async())
