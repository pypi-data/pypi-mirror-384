"""Библиотека для парсинга и валидации данных из Excel файлов.

Основные компоненты:
- ExcelParser: главный класс для парсинга Excel файлов
- VerticalSheetConfig, HorizontalSheetConfig: конфигурации для разных типов листов
- field_config: декоратор для настройки полей dataclass

Примеры использования см. в README.md
"""

from __future__ import annotations

from excel_to_dto.exceptions import (
    EmptyValueError,
    ExcelToDTOError,
    FieldNotFoundError,
    ParsingError,
    ValidationError,
)
from excel_to_dto.models import (
    ExcelFileConfig,
    FieldConfig,
    HorizontalSheetConfig,
    SheetOrientation,
    VerticalSheetConfig,
    field_config,
)
from excel_to_dto.parsers import ExcelParser

__version__ = "0.1.0"

__all__ = [
    # Main parser
    "ExcelParser",
    # Models
    "ExcelFileConfig",
    "FieldConfig",
    "VerticalSheetConfig",
    "HorizontalSheetConfig",
    "SheetOrientation",
    "field_config",
    # Exceptions
    "ExcelToDTOError",
    "ParsingError",
    "ValidationError",
    "FieldNotFoundError",
    "EmptyValueError",
]

