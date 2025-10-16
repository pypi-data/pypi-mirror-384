# Excel to DTO

Библиотека для парсинга и валидации данных из Excel файлов с автоматическим преобразованием в dataclass модели.

## Особенности

- 📊 **Поддержка двух типов листов:**
  - Вертикальные (ключ-значение): одна колонка - ключи, вторая - значения
  - Горизонтальные (табличные): первая строка - заголовки, остальные - данные

- 🔒 **Автоматическая валидация** данных с помощью Pydantic
- 🚀 **Простой и понятный API** для быстрой интеграции
- 📝 **Декларативное описание** структуры Excel файлов через dataclasses
- ⚡ **Детальные сообщения об ошибках** для упрощения отладки

## Установка

```bash
pip install excel-to-dto
```

Или с помощью Poetry:

```bash
poetry add excel-to-dto
```

## Быстрый старт

### Пример 1: Вертикальный лист (ключ-значение)

```python
from dataclasses import dataclass
from datetime import datetime
from excel_to_dto import ExcelParser, field_config

@dataclass
class ProductInfo:
    """Информация о продукте."""
    
    name: str = field_config(key="Название")
    price: float = field_config(key="Цена")
    created_date: datetime = field_config(key="Дата создания")
    is_active: bool = field_config(key="Активен")

# Парсинг файла
parser = ExcelParser()
product_info = parser.parse_vertical_sheet(
    file_path="products.xlsx",
    sheet_name="Информация",
    model_class=ProductInfo,
    key_column=0,  # Первая колонка - ключи
    value_column=1  # Вторая колонка - значения
)

print(f"Продукт: {product_info.name}")
print(f"Цена: {product_info.price}")
```

### Пример 2: Горизонтальный лист (табличный)

```python
from dataclasses import dataclass
from excel_to_dto import ExcelParser, field_config

@dataclass
class DataRecord:
    """Запись данных."""
    
    record_id: int = field_config(column="ID")
    title: str = field_config(column="Название")
    value: float = field_config(column="Значение")
    status: str = field_config(column="Статус")

# Парсинг табличного листа
parser = ExcelParser()
records = parser.parse_horizontal_sheet(
    file_path="data.xlsx",
    sheet_name="Записи",
    model_class=DataRecord,
    header_row=0,  # Первая строка - заголовки
    start_row=1    # Данные начинаются со второй строки
)

for record in records:
    print(f"Запись {record.record_id}: {record.title}")
```

### Пример 3: Комплексный файл с несколькими листами

```python
from dataclasses import dataclass
from typing import Sequence
from excel_to_dto import ExcelParser, ExcelFileConfig, VerticalSheetConfig, HorizontalSheetConfig

@dataclass
class ProjectInfo:
    name: str
    budget: float

@dataclass
class TaskRecord:
    description: str
    priority: float

@dataclass
class ProjectReport:
    """Полный отчет по проекту."""
    info: ProjectInfo
    tasks: Sequence[TaskRecord]

# Конфигурация файла
config = ExcelFileConfig(
    sheets={
        "info": VerticalSheetConfig(
            sheet_name="Информация",
            model_class=ProjectInfo,
            key_column=0,
            value_column=1
        ),
        "tasks": HorizontalSheetConfig(
            sheet_name="Задачи",
            model_class=TaskRecord,
            header_row=0,
            start_row=1
        )
    }
)

# Парсинг всего файла
parser = ExcelParser()
report = parser.parse_file("project_report.xlsx", config, ProjectReport)

print(f"Проект: {report.info.name}")
print(f"Найдено задач: {len(report.tasks)}")
```

## Валидация данных

Библиотека использует Pydantic для автоматической валидации:

```python
from dataclasses import dataclass
from pydantic import Field, validator
from excel_to_dto import ExcelParser, field_config

@dataclass
class ProductInfo:
    name: str = field_config(key="Название", validators=[Field(min_length=1, max_length=255)])
    price: float = field_config(key="Цена", validators=[Field(gt=0, le=1000000)])
    
    @validator('price')
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Цена не может быть отрицательной')
        return v

# При парсинге автоматически будут применены валидаторы
parser = ExcelParser()
try:
    product = parser.parse_vertical_sheet("products.xlsx", "Info", ProductInfo)
except ValueError as e:
    print(f"Ошибка валидации: {e}")
```

## Обработка ошибок

```python
from excel_to_dto import ExcelParser, ParsingError, ValidationError

parser = ExcelParser()

try:
    data = parser.parse_vertical_sheet("data.xlsx", "Sheet1", MyModel)
except FileNotFoundError:
    print("Файл не найден")
except ParsingError as e:
    print(f"Ошибка парсинга: {e}")
    print(f"Лист: {e.sheet_name}, Строка: {e.row}, Колонка: {e.column}")
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
    print(f"Поле: {e.field_name}, Значение: {e.value}")
```

## Расширенные возможности

### Кастомные преобразователи типов

```python
from excel_to_dto import ExcelParser, TypeConverter

def parse_custom_date(value: str) -> datetime:
    """Кастомный парсер для специфичного формата даты."""
    return datetime.strptime(value, "%d.%m.%Y %H:%M")

parser = ExcelParser()
parser.register_converter(datetime, parse_custom_date)
```

### Пропуск пустых строк

```python
records = parser.parse_horizontal_sheet(
    file_path="data.xlsx",
    sheet_name="Данные",
    model_class=DataRecord,
    skip_empty_rows=True  # Пропустить пустые строки
)
```

## Требования

- Python >= 3.10
- openpyxl >= 3.1.2
- pydantic >= 2.5.0


## Лицензия

MIT
