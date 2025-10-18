from logging import Logger

from redis.asyncio import Redis
from tp_helper.base_items.base_worker_service import BaseWorkerService
from tp_helper.decorators.decorator_retry_forever import retry_forever

from tp_shared.nsis_service.repos.nsis_results_ack_list_queue_repo import (
    NsisResultsAckListQueueRepo,
)
from tp_shared.nsis_service.schemas.nsis_result_message import NsisResultMessage


class BaseNsisResultsAckListQueueWorkerService(
    NsisResultsAckListQueueRepo, BaseWorkerService
):
    def __init__(self, redis_client: Redis, logger: Logger):
        BaseWorkerService.__init__(self, logger=logger, redis_client=redis_client)
        NsisResultsAckListQueueRepo.__init__(self, redis_client=redis_client)

    @retry_forever(
        start_message="📥 Начало чтения задач из очереди {queue_name}",
        error_message="❌ Ошибка при чтении из очереди {queue_name}",
    )
    async def pop(self) -> NsisResultMessage | None:
        return await NsisResultsAckListQueueRepo.pop(self)

    @retry_forever(
        start_message="🗑️ Удаление задач из очереди {queue_name}",
        error_message="❌ Ошибка при удалении задач из очереди {queue_name}",
    )
    async def ack(self) -> None:
        return await NsisResultsAckListQueueRepo.ack(self)
