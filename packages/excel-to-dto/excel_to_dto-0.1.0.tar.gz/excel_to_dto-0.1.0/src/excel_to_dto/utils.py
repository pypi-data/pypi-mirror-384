"""Утилиты для преобразования типов и работы с данными."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_args, get_origin

from excel_to_dto.exceptions import TypeConversionError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TypeConverter:
    """Конвертер типов для преобразования значений из Excel.
    
    Поддерживает стандартные типы Python и позволяет регистрировать
    кастомные конвертеры для специфичных типов.
    """

    def __init__(self) -> None:
        """Инициализация конвертера с предустановленными конвертерами."""
        self._converters: Dict[Type[Any], Callable[[Any], Any]] = {
            str: self._to_str,
            int: self._to_int,
            float: self._to_float,
            bool: self._to_bool,
            datetime: self._to_datetime,
        }

    def register(
        self,
        target_type: Type[T],
        converter: Callable[[Any], T],
    ) -> None:
        """Регистрирует кастомный конвертер для типа.
        
        Args:
            target_type: Целевой тип
            converter: Функция преобразования
            
        Example:
            >>> converter = TypeConverter()
            >>> converter.register(datetime, lambda x: datetime.strptime(x, "%d.%m.%Y"))
        """
        self._converters[target_type] = converter
        logger.debug("Зарегистрирован конвертер для типа %s", target_type.__name__)

    def convert(
        self,
        value: Any,
        target_type: Type[T],
        field_name: Optional[str] = None,
    ) -> T:
        """Преобразует значение к целевому типу.
        
        Args:
            value: Значение для преобразования
            target_type: Целевой тип
            field_name: Имя поля (для ошибок)
            
        Returns:
            Преобразованное значение
            
        Raises:
            TypeConversionError: Если преобразование невозможно
        """
        # Если значение None и тип Optional
        if value is None:
            if self._is_optional(target_type):
                return None  # type: ignore
            if field_name:
                raise TypeConversionError(value, target_type, field_name)
            raise TypeConversionError(value, target_type)

        # Получаем реальный тип для Optional
        actual_type = self._unwrap_optional(target_type)

        # Если значение уже нужного типа
        if isinstance(value, actual_type):
            return value  # type: ignore

        # Ищем конвертер
        converter = self._converters.get(actual_type)
        if converter is None:
            logger.warning(
                "Конвертер для типа %s не найден, используется конструктор",
                actual_type.__name__,
            )
            try:
                return actual_type(value)  # type: ignore
            except (ValueError, TypeError) as e:
                raise TypeConversionError(value, actual_type, field_name) from e

        # Применяем конвертер
        try:
            return converter(value)  # type: ignore
        except (ValueError, TypeError) as e:
            raise TypeConversionError(value, actual_type, field_name) from e

    @staticmethod
    def _is_optional(tp: Type[Any]) -> bool:
        """Проверяет, является ли тип Optional.
        
        Args:
            tp: Тип для проверки
            
        Returns:
            True если тип Optional
        """
        return get_origin(tp) is type(None) or (
            get_origin(tp) is type(None).__class__.__bases__[0]  # Union
            and type(None) in get_args(tp)
        )

    @staticmethod
    def _unwrap_optional(tp: Type[T]) -> Type[T]:
        """Извлекает тип из Optional.
        
        Args:
            tp: Тип (возможно Optional)
            
        Returns:
            Реальный тип
        """
        origin = get_origin(tp)
        if origin is type(None).__class__.__bases__[0]:  # Union
            args = get_args(tp)
            # Фильтруем None из Union
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return non_none_args[0]  # type: ignore
        return tp

    @staticmethod
    def _to_str(value: Any) -> str:
        """Преобразует значение в строку.
        
        Args:
            value: Значение
            
        Returns:
            Строка
        """
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _to_int(value: Any) -> int:
        """Преобразует значение в int.
        
        Args:
            value: Значение
            
        Returns:
            Целое число
            
        Raises:
            ValueError: Если преобразование невозможно
        """
        if isinstance(value, bool):
            raise ValueError("Cannot convert bool to int in this context")
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Убираем пробелы
            value = value.strip()
            # Пробуем преобразовать через float для обработки "1000.0"
            try:
                return int(float(value))
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to int")
        raise ValueError(f"Cannot convert {type(value).__name__} to int")

    @staticmethod
    def _to_float(value: Any) -> float:
        """Преобразует значение в float.
        
        Args:
            value: Значение
            
        Returns:
            Число с плавающей точкой
            
        Raises:
            ValueError: Если преобразование невозможно
        """
        if isinstance(value, bool):
            raise ValueError("Cannot convert bool to float in this context")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip()
            # Заменяем запятую на точку для русского формата
            value = value.replace(",", ".")
            return float(value)
        raise ValueError(f"Cannot convert {type(value).__name__} to float")

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Преобразует значение в bool.
        
        Поддерживает различные форматы: True/False, Да/Нет, 1/0, +/-
        
        Args:
            value: Значение
            
        Returns:
            Boolean значение
            
        Raises:
            ValueError: Если преобразование невозможно
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            value_lower = value.strip().lower()
            true_values = {"true", "да", "yes", "y", "1", "+", "т"}
            false_values = {"false", "нет", "no", "n", "0", "-", "н"}
            
            if value_lower in true_values:
                return True
            if value_lower in false_values:
                return False
            
            raise ValueError(f"Cannot convert '{value}' to bool")
        
        raise ValueError(f"Cannot convert {type(value).__name__} to bool")

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        """Преобразует значение в datetime.
        
        Поддерживает различные форматы дат.
        
        Args:
            value: Значение
            
        Returns:
            Объект datetime
            
        Raises:
            ValueError: Если преобразование невозможно
        """
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            
            # Список распространённых форматов
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"Cannot convert '{value}' to datetime. Supported formats: {formats}")
        
        # Для Excel datetime (число дней с 1900-01-01)
        if isinstance(value, (int, float)):
            # Excel базовая дата: 1900-01-01 (но с багом 1900 високосный год)
            from datetime import timedelta
            
            excel_base_date = datetime(1899, 12, 30)
            return excel_base_date + timedelta(days=value)
        
        raise ValueError(f"Cannot convert {type(value).__name__} to datetime")


def is_empty_value(value: Any) -> bool:
    """
        Проверяет, является ли значение пустым или None.
    """
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def clean_key(key: str) -> str:
    """
        Очищает ключ от лишних пробелов и символов.
    """
    if not isinstance(key, str):
        return str(key)
    return key.strip()

