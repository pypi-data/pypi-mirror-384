from datetime import timedelta
from logging import Logger

from redis.asyncio import Redis
from tp_helper.base_items.base_worker_service import BaseWorkerService
from tp_helper.decorators.decorator_retry_forever import retry_forever

from tp_shared.mos_passes_service.repo.mos_passes_results_stream_queue_repo import (
    MosPassesResultsStreamQueueRepo,
)
from tp_shared.mos_passes_service.schemas.mos_passes_result_message import (
    MosPassesResultMessage,
)


class BaseMosPassesResultsStreamQueueWorkerService(
    MosPassesResultsStreamQueueRepo, BaseWorkerService
):
    def __init__(
        self,
        redis_client: Redis,
        logger: Logger,
        group_name: str,
        consumer_name: str,
    ):
        BaseWorkerService.__init__(self, redis_client=redis_client, logger=logger)
        MosPassesResultsStreamQueueRepo.__init__(self, redis_client=redis_client)

        self.group_name = group_name
        self.consumer_name = consumer_name

    @retry_forever(
        start_message="Добавление сообщения из очередь {queue_name}",
        error_message="Ошибка при добавление сообщения в очередь {queue_name}",
    )
    async def add(self, message: MosPassesResultMessage) -> None:
        await MosPassesResultsStreamQueueRepo.add(self, message)

    @retry_forever(
        start_message="Получение сообщений из очереди {queue_name}",
        error_message="Ошибка получения сообщений из очереди {queue_name}",
    )
    async def pop(
        self,
        stream_id: str = ">",
        block: int = 0,
        count: int = 100,
        prioritize_claimed: bool = True,
        min_idle_time: int = 60000,
    ) -> list[tuple[str, MosPassesResultMessage]] | None:
        return await MosPassesResultsStreamQueueRepo.pop(
            self,
            group_name=self.group_name,
            consumer_name=self.consumer_name,
            stream_id=stream_id,
            block=block,
            count=count,
            prioritize_claimed=prioritize_claimed,
            min_idle_time=min_idle_time,
        )

    @retry_forever(
        start_message="Подтверждение сообщения в потоке {queue_name}",
        error_message="Ошибка подтверждения сообщения в потоке {queue_name}",
    )
    async def ack(self, message_id: str):
        await MosPassesResultsStreamQueueRepo.ack(self, self.group_name, message_id)

    @retry_forever(
        start_message="Поиск зависших сообщений в потоке {queue_name}",
        error_message="Ошибка при auto-claim сообщений в потоке {queue_name}",
    )
    async def claim_reassign(
        self,
        min_idle_time: int = 60000,
        count: int = 100,
    ) -> list[tuple[str, MosPassesResultMessage]]:
        return await MosPassesResultsStreamQueueRepo.claim_reassign(
            self,
            group_name=self.group_name,
            consumer_name=self.consumer_name,
            min_idle_time=min_idle_time,
            count=count,
        )

    @retry_forever(
        start_message="Создание группы потребителей в потоке {queue_name}",
        error_message="Ошибка создания группы в потоке {queue_name}",
    )
    async def create_consumer_group(self, create_stream: bool = True):
        await MosPassesResultsStreamQueueRepo.create_consumer_group(
            self,
            group_name=self.group_name,
            create_stream=create_stream,
        )

    @retry_forever(
        start_message="Очистка сообщений старше {retention} в потоке {queue_name}",
        error_message="Ошибка при очистке сообщений в потоке {queue_name}",
    )
    async def trim_by_age(self, retention: timedelta) -> int:
        return await MosPassesResultsStreamQueueRepo.trim_by_age(self, retention)

    @retry_forever(
        start_message="Полная очистка потока {queue_name}",
        error_message="Ошибка при полной очистке потока {queue_name}",
    )
    async def delete_all(self) -> None:
        await MosPassesResultsStreamQueueRepo.delete_all(self)
