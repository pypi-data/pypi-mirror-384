import asyncio
import logging
from typing import Callable, Optional

from strats.core import Clock, Monitor, State

logger = logging.getLogger(__name__)


class StaticMonitor(Monitor):
    def __init__(
        self,
        static_job: Callable,
        **kwargs,
    ):
        self.static_job = static_job

        super().__init__(**kwargs)

    async def run(self, clock: Clock, state: Optional[State]):
        await self.delay()
        self.set_descriptor(state)
        logger.info(f"{self.name} start")

        success = self.exec_on_init()
        if not success:
            return

        try:
            await self.static_job(clock, state)

        except asyncio.CancelledError:
            # To avoid "ERROR:asyncio:Task exception was never retrieved",
            # Re-raise the CancelledError
            raise
        except Exception as e:
            # Unexpected error
            logger.error(f"Error in {self.name}: {e}")
        finally:
            self.exec_on_delete()
            logger.info(f"{self.name} stopped")
