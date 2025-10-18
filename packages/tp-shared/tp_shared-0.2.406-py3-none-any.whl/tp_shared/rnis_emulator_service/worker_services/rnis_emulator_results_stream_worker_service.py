from datetime import timedelta
from logging import Logger

from tp_helper.base_items.base_worker_service import BaseWorkerService
from tp_helper.decorators.decorator_retry_forever import retry_forever

from tp_shared.rnis_emulator_service.repos.rnis_emulator_results_stream_queue_repo import (
    RnisEmulatorResultsStreamQueueRepo,
)
from tp_shared.rnis_emulator_service.schemas.rnis_emulator_result_message import (
    RnisEmulatorResultMessage,
)


class RnisEmulatorResultsStreamQueueWorkerService(BaseWorkerService):
    def __init__(
        self,
        repo: RnisEmulatorResultsStreamQueueRepo,
        logger: Logger,
        group_name: str,
        consumer_name: str,
    ):
        super().__init__(logger=logger)
        self.repo = repo
        self.queue_name = self.repo.QUEUE_NAME
        self.group_name = group_name
        self.consumer_name = consumer_name

    @retry_forever(
        start_message="➕ Добавление сообщения из очередь {queue_name}",
        error_message="❌ Ошибка при добавление сообщения в очередь {queue_name}",
    )
    async def add(self, message: RnisEmulatorResultMessage) -> None:
        await self.repo.add(message)

    @retry_forever(
        start_message="📥 Получение сообщений из очереди {queue_name}",
        error_message="⚠️ Ошибка получения сообщений из очереди {queue_name}",
    )
    async def pop(
        self,
        stream_id: str = ">",
        block: int = 60,
        count: int = 100,
        prioritize_claimed: bool = True,
        min_idle_time: int = 60000,
    ) -> list[tuple[str, RnisEmulatorResultMessage]] | None:
        return await self.repo.pop(
            group_name=self.group_name,
            consumer_name=self.consumer_name,
            stream_id=stream_id,
            block=block,
            count=count,
            prioritize_claimed=prioritize_claimed,
            min_idle_time=min_idle_time,
        )

    @retry_forever(
        start_message="✅ Подтверждение сообщения в потоке {queue_name}",
        error_message="⚠️ Ошибка подтверждения сообщения в потоке {queue_name}",
    )
    async def ack(self, message_id: str):
        await self.repo.ack(self.group_name, message_id)

    @retry_forever(
        start_message="🔍 Поиск зависших сообщений в потоке {queue_name}",
        error_message="🚫 Ошибка при auto-claim сообщений в потоке {queue_name}",
    )
    async def claim_reassign(
        self,
        min_idle_time: int = 60000,
        count: int = 100,
    ) -> list[tuple[str, RnisEmulatorResultMessage]]:
        return await self.repo.claim_reassign(
            group_name=self.group_name,
            consumer_name=self.consumer_name,
            min_idle_time=min_idle_time,
            count=count,
        )

    @retry_forever(
        start_message="👥 Создание группы потребителей в потоке {queue_name}",
        error_message="❌ Ошибка создания группы в потоке {queue_name}",
    )
    async def create_consumer_group(self, create_stream: bool = True):
        await self.repo.create_consumer_group(
            group_name=self.group_name,
            create_stream=create_stream,
        )

    @retry_forever(
        start_message="🧹 Очистка сообщений старше {retention} в потоке {queue_name}",
        error_message="⚠️ Ошибка при очистке сообщений в потоке {queue_name}",
    )
    async def trim_by_age(self, retention: timedelta) -> int:
        return await self.repo.trim_by_age(retention)

    @retry_forever(
        start_message="🗑️ Полная очистка потока {queue_name}",
        error_message="❌ Ошибка при полной очистке потока {queue_name}",
    )
    async def delete_all(self) -> None:
        await self.repo.delete_all()
