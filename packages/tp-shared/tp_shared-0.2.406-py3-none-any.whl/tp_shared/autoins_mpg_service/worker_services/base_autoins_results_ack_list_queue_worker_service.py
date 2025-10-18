from logging import Logger

from redis.asyncio import Redis
from tp_helper.base_items.base_worker_service import BaseWorkerService
from tp_helper.decorators.decorator_retry_forever import retry_forever

from tp_shared.autoins_mpg_service.repos.autoins_results_ack_list_queue_repo import (
    AutoinsResultsAckListQueueRepo,
)
from tp_shared.autoins_mpg_service.schemas.autoins_result_message import (
    AutoinsResultMessage,
)


class BaseAutoinsResultsAckListQueueWorkerService(
    BaseWorkerService, AutoinsResultsAckListQueueRepo
):
    def __init__(self, redis_client: Redis, logger: Logger):
        BaseWorkerService.__init__(self, logger=logger, redis_client=redis_client)
        AutoinsResultsAckListQueueRepo.__init__(self, redis_client=redis_client)

    @retry_forever(
        start_message="📥 Чтение задач из очереди {queue_name}",
        error_message="❌ Ошибка при чтении из очереди {queue_name}",
    )
    async def pop(self) -> AutoinsResultMessage | None:
        return await AutoinsResultsAckListQueueRepo.pop(self)

    @retry_forever(
        start_message="🗑️ ack в очередь {queue_name}",
        error_message="❌ Ошибка при ack в очередь {queue_name}",
    )
    async def ack(self) -> None:
        return await AutoinsResultsAckListQueueRepo.ack(self)
