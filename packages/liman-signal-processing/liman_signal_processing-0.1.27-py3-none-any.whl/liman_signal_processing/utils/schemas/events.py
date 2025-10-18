from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    INSTANT = "instant"
    DURATION = "duration"


class EventStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ACKNOWLEDGED = "acknowledged"

class EventKind(str, Enum):
    TELEMETRY_EXCEEDED = "telemetry_exceeded"
    TELEMETRY_MISSING = "telemetry_missing"
    RAW_DATA_MISSING = "raw_data_missing"
    DEFECT_DETECTED = "defect_detected"
    OPERATING_MODE_ALARM = "operating_mode_alarm"

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class EventMessageFilter(BaseModel):
    # Основные временные фильтры
    start_date: Optional[datetime] = Field(None, description="Начальная дата периода")
    end_date: Optional[datetime] = Field(None, description="Конечная дата периода")

    # Фильтры по типу и статусу события
    event_type: Optional[EventType] = Field(None, description="Тип события: instant или duration")
    event_kind: Optional[EventKind] = Field(None, description="Вид события")
    status: Optional[EventStatus] = Field(None, description="Статус события: open, closed или acknowledged")

    # Фильтры по характеристикам
    severity: Optional[SeverityLevel] = Field(None, description="Уровень важности: critical, warning или info")
    acknowledged: Optional[bool] = Field(None, description="Флаг подтверждения события")

    # Фильтры по оборудованию
    equipment_id: Optional[int] = Field(None, description="ID оборудования")
    min_duration: Optional[int] = Field(None, ge=0, description="Минимальная длительность в секундах")
    max_duration: Optional[int] = Field(None, ge=0, description="Максимальная длительность в секундах")

    # Пагинация
    size: int = Field(100, ge=1, le=1000, description="Количество записей на страницу")
    page: int = Field(1, ge=1, description="Номер страницы")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def build_where_clause(self) -> tuple[str, dict]:
        """Строит WHERE-часть SQL запроса и параметры"""
        conditions = []
        params = {}

        # Базовые временные фильтры
        if self.start_date:
            conditions.append("created_at >= %(start_date)s")
            params["start_date"] = self.start_date
        if self.end_date:
            conditions.append("created_at <= %(end_date)s")
            params["end_date"] = self.end_date

        # Фильтры по типу и статусу
        if self.event_type:
            conditions.append("event_type = %(event_type)s")
            params["event_type"] = self.event_type

        if self.event_kind:
            conditions.append("event_kind = %(event_kind)s")
            params["event_kind"] = self.event_kind

        if self.status:
            conditions.append("status = %(status)s")
            params["status"] = self.status

        # Фильтры по характеристикам
        if self.acknowledged is not None:
            conditions.append("acknowledged = %(acknowledged)s")
            params["acknowledged"] = self.acknowledged
        if self.severity:
            conditions.append("severity = %(severity)s")
            params["severity"] = self.severity

        # Фильтры по оборудованию
        if self.equipment_id:
            conditions.append("equipment_id = %(equipment_id)s")
            params["equipment_id"] = self.equipment_id
        if self.min_duration is not None:
            conditions.append("duration_seconds >= %(min_duration)s")
            params["min_duration"] = self.min_duration
        if self.max_duration is not None:
            conditions.append("duration_seconds <= %(max_duration)s")
            params["max_duration"] = self.max_duration

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    def build_limit_offset(self) -> str:
        """Строит LIMIT-OFFSET часть запроса"""
        return f"LIMIT {self.size} OFFSET {(self.page - 1) * self.size}"