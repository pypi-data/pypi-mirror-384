import asyncio
import os
import psutil
import traceback
from collections import deque
from datetime import datetime, timezone, timedelta
from google.cloud.pubsub_v1.publisher.futures import Future
from uuid import UUID, uuid4
from maleo.logging.enums import Level
from maleo.logging.logger import EnvironmentT, ServiceKeyT, Application
from maleo.schemas.application import ApplicationContext, OptApplicationContext
from maleo.schemas.google import PubslisherHandler
from maleo.schemas.connection import OptConnectionContext
from maleo.schemas.operation.action.system import SystemOperationAction
from maleo.schemas.operation.context import generate
from maleo.schemas.operation.enums import (
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.system import SuccessfulSystemOperation
from maleo.schemas.pagination import FlexiblePagination
from maleo.schemas.response import (
    SingleDataResponse,
    MultipleDataResponse,
)
from maleo.schemas.security.authentication import OptAnyAuthentication
from maleo.schemas.security.authorization import OptAnyAuthorization
from maleo.schemas.security.impersonation import OptImpersonation
from maleo.types.uuid import OptUUID
from maleo.utils.exception import extract_details
from .config import ResourceConfig
from .constants import STATUS_LOG_LEVEL
from .schemas import (
    CPUUsage,
    MemoryUsage,
    Usage,
    RegularMeasurement,
    AverageMeasurement,
    PeakMeasurement,
)


class ResourceMonitor:
    def __init__(
        self,
        config: ResourceConfig,
        logger: Application[EnvironmentT, ServiceKeyT],
        publish: bool = False,
        publisher: PubslisherHandler | None = None,
        application_context: OptApplicationContext = None,
    ):
        self.application_context = (
            application_context
            if application_context is not None
            else ApplicationContext.from_env()
        )
        self.config = config
        self.logger = logger
        self.publish = publish
        self.publisher = publisher
        self.process = psutil.Process(os.getpid())
        self.cpu_window = deque(maxlen=self.config.measurement.window)

        # Store historical data with timestamps
        self.measurement_history: deque[RegularMeasurement] = deque(
            maxlen=10_000
        )  # Adjust max length as needed
        self.is_monitoring = False
        self.monitor_task: asyncio.Task | None = None

        # Operation context setup
        self.operation_context = generate(
            origin=Origin.SERVICE, layer=Layer.INFRASTRUCTURE, target=Target.MONITORING
        )
        self.operation_action = SystemOperationAction(
            type=SystemOperationType.METRIC_REPORT, details={"type": "resource"}
        )

    async def start_monitoring(
        self,
        operation_id: OptUUID = None,
    ) -> None:
        """Start the resource monitoring loop."""
        operation_id = operation_id if operation_id is not None else uuid4()
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(operation_id))

    async def stop_monitoring(self) -> None:
        """Stop the resource monitoring loop."""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None

    async def _monitor_loop(
        self,
        operation_id: UUID,
    ) -> None:
        """Internal monitoring loop."""
        frequency = self.config.measurement.frequency
        log_count: int = 1
        publish_count: int = 1
        while self.is_monitoring:
            try:
                await self._measure(
                    operation_id,
                    frequency.should_log and frequency.log == log_count,
                    frequency.should_publish and frequency.publish == publish_count,
                )

                # Calculate log_count
                if frequency.should_log and log_count >= frequency.log:
                    log_count = 1
                else:
                    log_count += 1

                # Calculate publish_count
                if frequency.should_publish and publish_count >= frequency.publish:
                    publish_count = 1
                else:
                    publish_count += 1

                await asyncio.sleep(self.config.measurement.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Exception occured in resource monitoring",
                    exc_info=True,
                    extra={"json_fields": {"exc_details": extract_details(e)}},
                )
                print(f"Error in resource monitoring:\n{traceback.format_exc()}")
                await asyncio.sleep(self.config.measurement.interval)

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than max_age_seconds (default: 1 hour)."""
        if not self.measurement_history:
            return

        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(
            seconds=self.config.measurement.retention
        )

        # Remove old entries from the left
        while (
            self.measurement_history
            and self.measurement_history[0].measured_at < cutoff_time
        ):
            self.measurement_history.popleft()

    async def _measure(
        self, operation_id: UUID, log: bool = False, publish: bool = False
    ) -> SingleDataResponse[RegularMeasurement, None]:
        """Collect current resource usage and store in history."""
        executed_at = datetime.now(tz=timezone.utc)

        # Raw CPU usage since last call
        raw_cpu = self.process.cpu_percent(interval=None)

        # Update moving window for smoothing
        self.cpu_window.append(raw_cpu)
        smooth_cpu = sum(self.cpu_window) / len(self.cpu_window)

        # Memory usage in MB
        raw_memory = self.process.memory_info().rss / (1024 * 1024)

        timestamp = Timestamp.completed_now(executed_at)

        measurement = RegularMeasurement.new(
            measured_at=timestamp.completed_at,
            usage=Usage(
                cpu=CPUUsage.new(
                    raw=raw_cpu, smooth=smooth_cpu, config=self.config.usage.cpu
                ),
                memory=MemoryUsage.new(raw=raw_memory, config=self.config.usage.memory),
            ),
        )

        # Store in history with timestamp
        self.measurement_history.append(measurement)

        # Clean up old entries (older than max retention period)
        self._cleanup_old_entries()

        response = SingleDataResponse[RegularMeasurement, None].new(data=measurement)

        if log:
            SuccessfulSystemOperation[SingleDataResponse[RegularMeasurement, None]](
                application_context=self.application_context,
                id=operation_id,
                context=self.operation_context,
                action=self.operation_action,
                timestamp=timestamp,
                summary=(
                    f"Successfully measured resource usage - {measurement.status}"
                    f" - CPU | Status: {measurement.usage.cpu.status}"
                    f" | Raw: {measurement.usage.cpu.raw:.2f}%"
                    f" | Smooth: {measurement.usage.cpu.smooth:.2f}%"
                    f" - Memory | Status {measurement.usage.memory.status}"
                    f" | Raw: {measurement.usage.memory.raw:.2f}MB"
                    f" | Percentage: {measurement.usage.memory.percentage:.2f}%"
                ),
                connection_context=None,
                authentication=None,
                authorization=None,
                impersonation=None,
                response=response,
            ).log(self.logger, STATUS_LOG_LEVEL[measurement.status])

        if self.publish and publish and self.publisher is not None:
            topic_path = self.publisher.client.topic_path(
                self.publisher.project_id, self.publisher.topic_id
            )
            try:
                future: Future = self.publisher.client.publish(
                    topic=topic_path,
                    data=measurement.message_bytes,
                    **self.application_context.model_dump(mode="json"),
                )
                message_id: str = future.result()

                self.logger.info(
                    f"Successfully published resource measurement message {message_id} to {topic_path}",
                    extra={
                        "json_fields": {
                            "measurement": measurement.model_dump(mode="json"),
                            "message": {
                                "id": message_id,
                                "obj": measurement.message_obj,
                            },
                        }
                    },
                )

            except Exception as e:
                self.logger.error(
                    f"Failed publishing resource measurement message to {topic_path}",
                    exc_info=True,
                    extra={
                        "json_fields": {
                            "measurement": measurement.model_dump(mode="json"),
                            "message_obj": measurement.message_obj,
                            "exc_details": extract_details(e),
                        }
                    },
                )

        return response

    def get_last_measurement(
        self,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[RegularMeasurement, None] | None:
        """Get the most recent resource usage data."""
        if not self.measurement_history:
            return None

        data = self.measurement_history[-1]
        response = SingleDataResponse[RegularMeasurement, None].new(data=data)

        SuccessfulSystemOperation[SingleDataResponse[RegularMeasurement, None]](
            application_context=self.application_context,
            id=operation_id if operation_id is not None else uuid4(),
            context=self.operation_context,
            action=self.operation_action,
            timestamp=Timestamp.now(),
            summary="Successfully retrieved last resource usage measurement",
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=response,
        ).log(self.logger, Level.INFO)

        return response

    def clear_history(self) -> None:
        """Clear all stored resource usage history."""
        self.measurement_history.clear()

    def count_history(self) -> int:
        """Get the number of entries in history."""
        return len(self.measurement_history)

    def get_measurement_history(
        self,
        window: int = 60,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> MultipleDataResponse[RegularMeasurement, FlexiblePagination, None]:
        """
        Get resource usage data from the last X seconds.

        Args:
            window: Number of seconds to look back

        Returns:
            List of dicts with 'timestamp' and 'resource_usage' keys
        """
        operation_id = operation_id if operation_id is not None else uuid4()
        executed_at = datetime.now(tz=timezone.utc)

        if not self.measurement_history:
            data = []
        else:
            cutoff_time = executed_at - timedelta(seconds=window)
            data = [
                entry
                for entry in self.measurement_history
                if entry.measured_at >= cutoff_time
            ]

        timestamp = Timestamp.completed_now(executed_at)

        pagination = FlexiblePagination(
            page=1,
            limit=None,
            data_count=len(data),
            total_data=len(data),
            total_pages=1,
        )

        response = MultipleDataResponse[
            RegularMeasurement, FlexiblePagination, None
        ].new(data=data, pagination=pagination)

        SuccessfulSystemOperation[
            MultipleDataResponse[RegularMeasurement, FlexiblePagination, None],
        ](
            application_context=self.application_context,
            id=operation_id,
            context=self.operation_context,
            action=self.operation_action,
            timestamp=timestamp,
            summary=f"Retrieved {len(data)} resource measurement entries from the last {window} seconds",
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=response,
        ).log(
            self.logger, Level.INFO
        )

        return response

    def get_average_usage(
        self,
        window: int = 60,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[AverageMeasurement, None] | None:
        """
        Calculate average resource usage over the last X seconds.

        Args:
            window: Number of seconds to look back

        Returns:
            Measurement with averaged values, or None if no data
        """
        operation_id = operation_id if operation_id is not None else uuid4()
        executed_at = datetime.now(tz=timezone.utc)

        history_response = self.get_measurement_history(
            window,
            operation_id=operation_id,
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
        )
        history_data = history_response.data
        if not history_data:
            return None

        measured_at = datetime.now(tz=timezone.utc)

        # Calculate averages
        total_raw_cpu = sum(entry.usage.cpu.raw for entry in history_data)
        total_smooth_cpu = sum(entry.usage.cpu.smooth for entry in history_data)
        total_memory = sum(entry.usage.memory.raw for entry in history_data)
        count = len(history_data)

        timestamp = Timestamp.completed_now(executed_at)

        measurement = AverageMeasurement.new(
            measured_at=measured_at,
            window=window,
            usage=Usage(
                cpu=CPUUsage.new(
                    raw=total_raw_cpu / count,
                    smooth=total_smooth_cpu / count,
                    config=self.config.usage.cpu,
                ),
                memory=MemoryUsage.new(
                    raw=total_memory / count, config=self.config.usage.memory
                ),
            ),
        )

        response = SingleDataResponse[AverageMeasurement, None].new(data=measurement)

        SuccessfulSystemOperation[SingleDataResponse[AverageMeasurement, None]](
            application_context=self.application_context,
            id=operation_id,
            context=self.operation_context,
            action=self.operation_action,
            timestamp=timestamp,
            summary=(
                f"Successfully measured average resource usage of the last {window} seconds - {measurement.status}"
                f" - CPU | Status: {measurement.usage.cpu.status}"
                f" | Raw: {measurement.usage.cpu.raw:.2f}%"
                f" | Smooth: {measurement.usage.cpu.smooth:.2f}%"
                f" - Memory | Status: {measurement.usage.memory.status}"
                f" | Raw: {measurement.usage.memory.raw:.2f}MB"
                f" | Percentage: {measurement.usage.memory.percentage:.2f}%"
            ),
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=response,
        ).log(self.logger, Level.INFO)

        return response

    def get_peak_usage(
        self,
        window: int = 60,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[PeakMeasurement, None] | None:
        """
        Get peak resource usage over the last X seconds.

        Args:
            seconds: Number of seconds to look back

        Returns:
            Measurement with peak values, or None if no data
        """
        operation_id = operation_id if operation_id is not None else uuid4()
        executed_at = datetime.now(tz=timezone.utc)

        history_response = self.get_measurement_history(
            window,
            operation_id=operation_id,
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
        )
        history_data = history_response.data
        if not history_data:
            return None

        measured_at = datetime.now(tz=timezone.utc)

        # Find peaks
        peak_raw_cpu = max(entry.usage.cpu.raw for entry in history_data)
        peak_smooth_cpu = max(entry.usage.cpu.smooth for entry in history_data)
        peak_raw_memory = max(entry.usage.memory.raw for entry in history_data)

        timestamp = Timestamp.completed_now(executed_at)

        measurement = PeakMeasurement.new(
            measured_at=measured_at,
            window=window,
            usage=Usage(
                cpu=CPUUsage.new(
                    raw=peak_raw_cpu,
                    smooth=peak_smooth_cpu,
                    config=self.config.usage.cpu,
                ),
                memory=MemoryUsage.new(
                    raw=peak_raw_memory, config=self.config.usage.memory
                ),
            ),
        )

        response = SingleDataResponse[PeakMeasurement, None].new(data=measurement)

        SuccessfulSystemOperation[SingleDataResponse[PeakMeasurement, None]](
            application_context=self.application_context,
            id=operation_id,
            context=self.operation_context,
            action=self.operation_action,
            timestamp=timestamp,
            summary=(
                f"Successfully measured peak resource usage of the last {window} seconds - {measurement.status}"
                f" - CPU | Status: {measurement.usage.cpu.status}"
                f" | Raw: {measurement.usage.cpu.raw:.2f}%"
                f" | Smooth: {measurement.usage.cpu.smooth:.2f}%"
                f" - Memory | Status: {measurement.usage.memory.status}"
                f" | Raw: {measurement.usage.memory.raw:.2f}MB"
                f" | Percentage: {measurement.usage.memory.percentage:.2f}%"
            ),
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=response,
        ).log(self.logger, Level.INFO)

        return response

    async def get_instant_usage(
        self,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[RegularMeasurement, None]:
        """
        Get an instant resource usage reading without affecting the monitoring loop.
        This doesn't store the result in history.
        """
        operation_id = operation_id if operation_id is not None else uuid4()
        executed_at = datetime.now(tz=timezone.utc)

        raw_cpu = self.process.cpu_percent(interval=None)
        raw_memory = self.process.memory_info().rss / (1024 * 1024)

        # For instant reading, use the current smooth CPU from the window
        # or raw CPU if no history exists
        smooth_cpu = (
            sum(self.cpu_window) / len(self.cpu_window) if self.cpu_window else raw_cpu
        )

        timestamp = Timestamp.completed_now(executed_at)

        measurement = RegularMeasurement.new(
            measured_at=timestamp.completed_at,
            usage=Usage(
                cpu=CPUUsage.new(
                    raw=raw_cpu, smooth=smooth_cpu, config=self.config.usage.cpu
                ),
                memory=MemoryUsage.new(raw=raw_memory, config=self.config.usage.memory),
            ),
        )

        response = SingleDataResponse[RegularMeasurement, None].new(data=measurement)

        SuccessfulSystemOperation[SingleDataResponse[RegularMeasurement, None]](
            application_context=self.application_context,
            id=operation_id,
            context=self.operation_context,
            action=self.operation_action,
            timestamp=timestamp,
            summary=(
                f"Successfully measured instant resource usage - {measurement.status}"
                f" - CPU | Status: {measurement.usage.cpu.status}"
                f" | Raw: {measurement.usage.cpu.raw:.2f}%"
                f" | Smooth: {measurement.usage.cpu.smooth:.2f}%"
                f" - Memory | Status {measurement.usage.memory.status}"
                f" | Raw: {measurement.usage.memory.raw:.2f}MB"
                f" | Percentage: {measurement.usage.memory.percentage:.2f}%"
            ),
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=response,
        ).log(self.logger, Level.INFO)

        return response

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_monitoring()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_monitoring()
