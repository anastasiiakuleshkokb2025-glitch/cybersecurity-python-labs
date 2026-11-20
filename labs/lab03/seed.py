import json
import logging
import sqlite3
from contextlib import closing

from labs.lab03.database import BASE_DIR, get_connection, initialize_database

SEED_FILE = BASE_DIR / "data" / "seed.json"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def seed_database() -> None:
    initialize_database()

    if not SEED_FILE.exists():
        logger.error(f"Файл {SEED_FILE} не знайдено.")
        return

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with closing(get_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories;")
        cat_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM records;")
        rec_count = cursor.fetchone()[0]

        if cat_count > 0 or rec_count > 0:
            print("База даних вже містить записи. Пропущено заповнення.")
            return

        try:
            with conn:
                for cat in data.get("categories", []):
                    conn.execute(
                        "INSERT INTO categories (id, name) VALUES (?, ?);",
                        (cat["id"], cat["name"]),
                    )
                for rec in data.get("records", []):
                    conn.execute(
                        """
                        INSERT INTO records (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        (
                            rec["code"],
                            rec["title"],
                            rec["category_id"],
                            rec["value"],
                            rec["status"],
                        ),
                    )
            print("Базу успішно заповнено початковими даними.")
        except sqlite3.Error as e:
            logger.error(f"Помилка при заповненні бази: {e}")
            print("Транзакцію скасовано через помилку.")


if __name__ == "__main__":
    seed_database()
