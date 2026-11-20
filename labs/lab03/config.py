"""Конфігурація параметрів та обмежень для варіанта 8.

Варіант 8: Облік часу відновлення сервісів.
Одиниця вимірювання: хвилини (minutes).
Поріг: 60.0.
"""

DOMAIN_NAME: str = "Облік часу відновлення сервісів"
UNIT: str = "minutes"
UNIT_UKR: str = "хвилини"
THRESHOLD: float = 60.0

MIN_VALUE: float = 0.0
MAX_VALUE: float = 1.7976931348623157e308

ALLOWED_STATUSES: tuple[str, ...] = ("new", "in_progress", "done")
DEFAULT_CATEGORIES: tuple[str, ...] = ("database", "web_service", "file_storage")
RECORD_TITLE_PREFIX: str = "Вимірювання відновлення"
