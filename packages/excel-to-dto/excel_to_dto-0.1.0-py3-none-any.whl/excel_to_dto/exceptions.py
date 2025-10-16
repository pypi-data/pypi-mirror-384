"""Исключения для библиотеки excel_to_dto."""

from __future__ import annotations

from typing import Any, Optional


class ExcelToDTOError(Exception):
    """Базовое исключение для всех ошибок библиотеки."""

    pass


class ParsingError(ExcelToDTOError):
    """Ошибка при парсинге Excel файла.
    
    Attributes:
        message: Описание ошибки
        file_path: Путь к файлу
        sheet_name: Имя листа
        row: Номер строки (опционально)
        column: Номер колонки (опционально)
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        sheet_name: Optional[str] = None,
        row: Optional[int] = None,
        column: Optional[int] = None,
    ) -> None:
        """Инициализация ошибки парсинга.
        
        Args:
            message: Описание ошибки
            file_path: Путь к файлу
            sheet_name: Имя листа
            row: Номер строки
            column: Номер колонки
        """
        self.message = message
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.row = row
        self.column = column

        error_parts = [message]
        if file_path:
            error_parts.append(f"Файл: {file_path}")
        if sheet_name:
            error_parts.append(f"Лист: {sheet_name}")
        if row is not None:
            error_parts.append(f"Строка: {row}")
        if column is not None:
            error_parts.append(f"Колонка: {column}")

        super().__init__(", ".join(error_parts))


class ValidationError(ExcelToDTOError):
    """Ошибка валидации данных.
    
    Attributes:
        message: Описание ошибки
        field_name: Имя поля
        value: Значение, которое не прошло валидацию
        expected_type: Ожидаемый тип (опционально)
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[type] = None,
    ) -> None:
        """Инициализация ошибки валидации.
        
        Args:
            message: Описание ошибки
            field_name: Имя поля
            value: Значение
            expected_type: Ожидаемый тип
        """
        self.message = message
        self.field_name = field_name
        self.value = value
        self.expected_type = expected_type

        # Не дублируем информацию - она уже в message
        super().__init__(message)


class SheetNotFoundError(ParsingError):
    """Лист не найден в Excel файле."""

    def __init__(self, sheet_name: str, file_path: str) -> None:
        """Инициализация ошибки.
        
        Args:
            sheet_name: Имя листа
            file_path: Путь к файлу
        """
        super().__init__(
            f"Лист '{sheet_name}' не найден в файле",
            file_path=file_path,
            sheet_name=sheet_name,
        )


class FieldNotFoundError(ParsingError):
    """Ключ не найден в листе."""

    def __init__(
        self,
        field_name: str,
        sheet_name: str,
        file_path: Optional[str] = None,
    ) -> None:
        """Инициализация ошибки.
        
        Args:
            field_name: Имя поля (ключа)
            sheet_name: Имя листа
            file_path: Путь к файлу
        """
        super().__init__(
            f"Ключ '{field_name}' не найден в листе",
            file_path=file_path,
            sheet_name=sheet_name,
        )


class TypeConversionError(ValidationError):
    """Ошибка преобразования типа."""

    def __init__(
        self,
        value: Any,
        target_type: type,
        field_name: Optional[str] = None,
    ) -> None:
        """Инициализация ошибки.
        
        Args:
            value: Значение
            target_type: Целевой тип
            field_name: Имя поля
        """
        super().__init__(
            f"Не удалось преобразовать значение '{value}' к типу {target_type.__name__}",
            field_name=field_name,
            value=value,
            expected_type=target_type,
        )


class EmptyValueError(ParsingError):
    """Ошибка пустого значения для обязательного поля."""

    def __init__(
        self,
        field_name: str,
        key_name: str,
        sheet_name: str,
        file_path: Optional[str] = None,
    ) -> None:
        """Инициализация ошибки.
        
        Args:
            field_name: Имя поля в модели
            key_name: Ключ в Excel файле
            sheet_name: Имя листа
            file_path: Путь к файлу
        """
        super().__init__(
            f"Значение для ключа '{key_name}' пустое",
            file_path=file_path,
            sheet_name=sheet_name,
        )

