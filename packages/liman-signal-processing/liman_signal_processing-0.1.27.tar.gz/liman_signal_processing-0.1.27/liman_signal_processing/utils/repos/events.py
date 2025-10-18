import json
import uuid
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
import logging
from datetime import datetime

from clickhouse_driver import Client
from clickhouse_driver.errors import Error as ClickHouseError

from liman_signal_processing.utils.schemas.events import (EventMessageFilter, EventStatus, EventType, SeverityLevel,
                                                          EventKind)


class EventMessageRepository:
    def __init__(self, host, port, database, user, password):
        self.client = Client(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            settings={'mutations_sync': 1}  # Ожидаем завершения мутаций синхронно
        )
        self.table_name = 'event_journal'
        self.logger = logging.getLogger(__name__)

    def _execute_query(self, query: str, params: dict = None) -> List[Dict[str, Any]]:
        """Выполняет запрос и возвращает результат в виде списка словарей"""
        try:
            self.logger.debug(f"Executing query: {query} with params: {params}")
            result = self.client.execute(
                query,
                params or {},
                with_column_types=True
            )
            columns = [col[0] for col in result[1]]
            return [dict(zip(columns, row)) for row in result[0]]
        except ClickHouseError as e:
            self.logger.error(f"ClickHouse error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_open_event_ids(self) -> Set[UUID]:
        """
        Получает UUID всех открытых событий (со статусом 'open' или 'acknowledged')

        Returns:
            Множество UUID открытых событий
        """
        query = f"""
        SELECT uuid
        FROM {self.table_name}
        WHERE status IN ('open', 'acknowledged')
        """

        try:
            result = self._execute_query(query)
            return {UUID(item['uuid']) for item in result}
        except Exception as e:
            self.logger.error(f"Error getting open event IDs: {str(e)}")
            return set()

    def get_messages(self, filter: EventMessageFilter) -> Dict[str, Any]:
        """Получает сообщения с применением фильтра"""
        where_clause, params = filter.build_where_clause()
        limit_offset = filter.build_limit_offset()

        data_query = f"""
        SELECT 
            uuid,
            event_type,
            event_kind,
            created_at,
            resolved_at,
            resolved_by,
            equipment_id,
            severity,
            message,
            acknowledged,
            acknowledged_at,
            acknowledged_by,
            additional_data,
            status,
            duration_seconds
        FROM {self.table_name}
        WHERE {where_clause}
        ORDER BY created_at DESC
        {limit_offset}
        """

        count_query = f"""
        SELECT count() as total
        FROM {self.table_name}
        WHERE {where_clause}
        """

        messages = self._execute_query(data_query, params)
        total_result = self._execute_query(count_query, params)
        total = total_result[0]['total'] if total_result else 0

        return {
            "items": messages,
            "total": total,
            "page": filter.page,
            "size": filter.size,
            "pages": (total + filter.size - 1) // filter.size if filter.size > 0 else 0
        }

    def get_count(self, filter: EventMessageFilter) -> int:
        """Возвращает общее количество событий по фильтру"""
        where_clause, params = filter.build_where_clause()
        query = f"SELECT count() as total FROM {self.table_name} WHERE {where_clause}"
        result = self._execute_query(query, params)
        return result[0]['total'] if result else 0

    def create_event(
            self,
            event_type: EventType,
            equipment_id: str,
            severity: SeverityLevel,
            message: str,
            event_kind: Optional[EventKind] = None,
            additional_data: Optional[Dict[str, Any]] = None,
            status: EventStatus = EventStatus.OPEN,
            created_at: Optional[datetime] = None
    ) -> UUID:
        """
        Создает новое событие в ClickHouse

        Args:
            event_type: Тип события
            event_kind: Вид события
            equipment_id: ID оборудования
            severity: Уровень важности
            message: Текст сообщения
            additional_data: Дополнительные данные в формате JSON
            status: Статус события (по умолчанию 'open')
            created_at: Время создания (по умолчанию текущее время)

        Returns:
            UUID созданного события

        Raises:
            ClickHouseError: В случае ошибки при работе с ClickHouse
        """
        event_uuid = uuid.uuid4()
        created_at = created_at or datetime.utcnow()

        query = f"""
        INSERT INTO {self.table_name} (
            uuid,
            event_type,
            event_kind,
            created_at,
            equipment_id,
            severity,
            message,
            additional_data,
            status
        ) VALUES (
            %(uuid)s,
            %(event_type)s,
            %(event_kind)s,
            %(created_at)s,
            %(equipment_id)s,
            %(severity)s,
            %(message)s,
            %(additional_data)s,
            %(status)s
        )
        """

        params = {
            "uuid": str(event_uuid),
            "event_type": event_type.value,
            "event_kind": event_kind.value if event_kind else None,
            "created_at": created_at,
            "equipment_id": equipment_id,
            "severity": severity.value,
            "message": message,
            "additional_data": json.dumps(additional_data or {}),
            "status": status.value
        }

        try:
            self.client.execute(query, params)
            return event_uuid
        except ClickHouseError as e:
            self.logger.error(f"Error creating event: {str(e)}")
            raise

    def confirm_event(self, event_uuid: UUID, user_id: str) -> bool:
        """Подтверждает сообщение"""
        query = f"""
        ALTER TABLE {self.table_name}
        UPDATE 
            acknowledged = true,
            acknowledged_at = %(acknowledged_at)s,
            acknowledged_by = %(acknowledged_by)s,
            status = 'acknowledged'
        WHERE uuid = %(uuid)s
        SETTINGS mutations_sync = 1
        """
        params = {
            "uuid": str(event_uuid),
            "acknowledged_at": datetime.utcnow(),
            "acknowledged_by": user_id
        }
        try:
            self.client.execute(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error confirming message: {str(e)}")
            return False

    def resolve_event(self, event_uuid: UUID, user_id: str) -> bool:
        """Закрывает длительное событие"""
        query = f"""
        ALTER TABLE {self.table_name}
        UPDATE 
            resolved_at = now(),
            resolved_by = %(resolved_by)s,
            duration_seconds = dateDiff('second', created_at, now()),
            status = 'closed'
        WHERE uuid = %(uuid)s AND event_type = 'duration' AND status != 'closed'
        SETTINGS mutations_sync = 1
        """
        params = {
            "uuid": str(event_uuid),
            "resolved_by": user_id
        }
        try:
            self.client.execute(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error resolving event: {str(e)}")
            return False

    def get_stats_by_field(self, field: str, filter: EventMessageFilter) -> Dict[str, int]:
        """Получает статистику по указанному полю"""
        where_clause, params = filter.build_where_clause()
        query = f"""
        SELECT 
            {field},
            count() as count
        FROM {self.table_name}
        WHERE {where_clause}
        GROUP BY {field}
        """
        result = self._execute_query(query, params)
        return {item[field]: item['count'] for item in result}

    def get_avg_duration(self, filter: EventMessageFilter) -> Optional[float]:
        """Средняя длительность событий в секундах"""
        where_clause, params = filter.build_where_clause()
        query = f"""
        SELECT avg(duration_seconds) as avg_duration
        FROM {self.table_name}
        WHERE {where_clause} AND duration_seconds IS NOT NULL
        """
        result = self._execute_query(query, params)
        return result[0]['avg_duration'] if result else None

    def get_max_duration(self, filter: EventMessageFilter) -> Optional[int]:
        """Максимальная длительность событий в секундах"""
        where_clause, params = filter.build_where_clause()
        query = f"""
        SELECT max(duration_seconds) as max_duration
        FROM {self.table_name}
        WHERE {where_clause} AND duration_seconds IS NOT NULL
        """
        result = self._execute_query(query, params)
        return result[0]['max_duration'] if result else None

    def get_min_duration(self, filter: EventMessageFilter) -> Optional[int]:
        """Минимальная длительность событий в секундах"""
        where_clause, params = filter.build_where_clause()
        query = f"""
        SELECT min(duration_seconds) as min_duration
        FROM {self.table_name}
        WHERE {where_clause} AND duration_seconds IS NOT NULL
        """
        result = self._execute_query(query, params)
        return result[0]['min_duration'] if result else None

    def get_event_by_uuid(self, event_uuid: UUID) -> Optional[Dict[str, Any]]:
        """Получает событие по UUID"""
        query = f"""
        SELECT * FROM {self.table_name}
        WHERE uuid = %(uuid)s
        LIMIT 1
        """
        result = self._execute_query(query, {"uuid": str(event_uuid)})
        return result[0] if result else None

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Получает все активные (не закрытые) события.

        Returns:
            Список словарей с информацией о событиях, содержащий:
            - event_id: UUID события
            - measurement_point_id: ID точки измерения (из additional_data)
            - param_name: Имя параметра (из additional_data)
            - created_at: Время создания события
            - message: Текст сообщения
            - severity: Уровень важности
        """
        query = f"""
        SELECT 
            uuid as event_id,
            additional_data,
            created_at,
            message,
            severity
        FROM {self.table_name}
        WHERE status != 'closed' AND event_type = 'duration'
        ORDER BY created_at DESC
        """

        try:
            result = self._execute_query(query)
            active_events = []

            for row in result:
                try:
                    additional_data = json.loads(row['additional_data']) if row['additional_data'] else {}
                    event = {
                        'event_id': row['event_id'],
                        'measurement_point_id': additional_data.get('measurement_point_id'),
                        'param_name': additional_data.get('param_name'),
                        'created_at': row['created_at'],
                        'message': row['message'],
                        'severity': row['severity']
                    }
                    active_events.append(event)
                except json.JSONDecodeError:
                    self.logger.warning(f"Не удалось распарсить additional_data для события {row['event_id']}")
                    continue

            return active_events
        except ClickHouseError as e:
            self.logger.error(f"Ошибка при получении активных событий: {str(e)}")
            raise