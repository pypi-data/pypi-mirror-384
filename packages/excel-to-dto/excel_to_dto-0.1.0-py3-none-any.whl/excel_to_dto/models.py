"""Модели данных для конфигурации парсинга Excel файлов."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class SheetOrientation(str, Enum):
    """Ориентация листа Excel.
    
    Attributes:
        VERTICAL: Вертикальный лист (ключ-значение)
        HORIZONTAL: Горизонтальный лист (табличный формат)
    """

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


@dataclass(frozen=True)
class FieldConfig:
    """Конфигурация поля dataclass для парсинга из Excel.
    
    Attributes:
        key: Ключ для вертикального листа (название строки)
        column: Название колонки для горизонтального листа
        required: Обязательное ли поле
        default: Значение по умолчанию
        converter: Кастомная функция преобразования типа
        validator: Кастомная функция валидации
    """

    key: Optional[str] = None
    column: Optional[str] = None
    required: bool = True
    default: Any = None
    converter: Optional[Callable[[Any], Any]] = None
    validator: Optional[Callable[[Any], bool]] = None


def field_config(
    key: Optional[str] = None,
    column: Optional[str] = None,
    required: bool = True,
    default: Any = None,
    converter: Optional[Callable[[Any], Any]] = None,
    validator: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """Создает метаданные для поля dataclass с конфигурацией парсинга.
    
    Args:
        key: Ключ для вертикального листа
        column: Название колонки для горизонтального листа
        required: Обязательное ли поле
        default: Значение по умолчанию
        converter: Кастомная функция преобразования
        validator: Кастомная функция валидации
        
    Returns:
        Field с метаданными для dataclass
        
    Example:
        >>> @dataclass
        >>> class DataModel:
        >>>     name: str = field_config(key="Название")
        >>>     value: float = field_config(key="Значение")
    """
    config = FieldConfig(
        key=key,
        column=column,
        required=required,
        default=default,
        converter=converter,
        validator=validator,
    )
    
    # Используем field из dataclasses с metadata
    return field(default=default if default is not None else ..., metadata={"excel_config": config})


@dataclass
class SheetConfig:
    """Базовая конфигурация листа Excel.
    
    Attributes:
        sheet_name: Имя листа в Excel файле
        model_class: Класс dataclass для маппинга данных
        orientation: Ориентация листа
    """

    sheet_name: str
    model_class: Type[Any]
    orientation: Optional[SheetOrientation] = None


@dataclass
class VerticalSheetConfig(SheetConfig):
    """Конфигурация вертикального листа (ключ-значение).
    
    Вертикальный лист имеет структуру:
    | Ключ        | Значение   |
    |-------------|------------|
    | Название    | Значение1  |
    | Параметр    | 100.0      |
    
    Attributes:
        key_column: Номер колонки с ключами (0-based)
        value_column: Номер колонки со значениями (0-based)
        start_row: Номер строки, с которой начинать чтение (0-based)
        skip_empty_rows: Пропускать ли пустые строки
    """

    key_column: int = 0
    value_column: int = 1
    start_row: int = 0
    skip_empty_rows: bool = True

    def __post_init__(self) -> None:
        """Установка ориентации после инициализации."""
        object.__setattr__(self, "orientation", SheetOrientation.VERTICAL)


@dataclass
class HorizontalSheetConfig(SheetConfig):
    """Конфигурация горизонтального листа (табличный формат).
    
    Горизонтальный лист имеет структуру:
    | ID | Название   | Значение |
    |----|------------|----------|
    | 1  | Элемент 1  | 100.0    |
    | 2  | Элемент 2  | 200.0    |
    
    Attributes:
        header_row: Номер строки с заголовками (0-based)
        start_row: Номер строки, с которой начинать чтение данных (0-based)
        end_row: Номер последней строки (опционально, None = до конца)
        skip_empty_rows: Пропускать ли пустые строки
    """

    header_row: int = 0
    start_row: int = 1
    end_row: Optional[int] = None
    skip_empty_rows: bool = True

    def __post_init__(self) -> None:
        """Установка ориентации после инициализации."""
        object.__setattr__(self, "orientation", SheetOrientation.HORIZONTAL)


@dataclass
class ExcelFileConfig:
    """Конфигурация Excel файла с несколькими листами.
    
    Attributes:
        sheets: Словарь конфигураций листов (ключ -> конфигурация)
        
    Example:
        >>> config = ExcelFileConfig(
        >>>     sheets={
        >>>         "info": VerticalSheetConfig(
        >>>             sheet_name="Информация",
        >>>             model_class=InfoModel,
        >>>         ),
        >>>         "data": HorizontalSheetConfig(
        >>>             sheet_name="Данные",
        >>>             model_class=DataRecord,
        >>>         ),
        >>>     }
        >>> )
    """

    sheets: Dict[str, SheetConfig] = field(default_factory=dict)

    def add_sheet(self, key: str, config: SheetConfig) -> None:
        """Добавляет конфигурацию листа.
        
        Args:
            key: Ключ для доступа к данным листа
            config: Конфигурация листа
        """
        self.sheets[key] = config

    def get_sheet(self, key: str) -> Optional[SheetConfig]:
        """Получает конфигурацию листа по ключу.
        
        Args:
            key: Ключ листа
            
        Returns:
            Конфигурация листа или None
        """
        return self.sheets.get(key)

