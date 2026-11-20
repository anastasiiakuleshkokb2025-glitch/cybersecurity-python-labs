from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


def get_categories() -> list[dict[str, Any]]:
    """Отримати список усіх категорій, відсортований за id у зростаючому порядку."""
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name FROM categories ORDER BY id ASC;"
        ).fetchall()
        return [dict(row) for row in rows]


def get_category_by_id(category_id: int) -> dict[str, Any] | None:
    """Отримати категорію за її id."""
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name FROM categories WHERE id = ?;",
            (category_id,),
        ).fetchone()
        return dict(row) if row else None


def get_category_by_name(name: str) -> dict[str, Any] | None:
    """Отримати категорію за назвою."""
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name FROM categories WHERE name = ?;",
            (name.strip(),),
        ).fetchone()
        return dict(row) if row else None


def create_category(name: str) -> dict[str, Any]:
    """Створити нову категорію."""
    clean_name = name.strip()
    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute(
                "INSERT INTO categories (name) VALUES (?);",
                (clean_name,),
            )
            cat_id = cursor.lastrowid
        return {"id": cat_id, "name": clean_name}


def check_category_has_records(category_id: int) -> bool:
    """Перевірити, чи містить категорія хоча б один пов'язаний запис."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT 1 FROM records WHERE category_id = ? LIMIT 1;", (category_id,)
        ).fetchone()
        return row is not None


def delete_category(category_id: int) -> bool:
    """Видалити порожню категорію за id."""
    with closing(get_connection()) as conn:
        exists = conn.execute(
            "SELECT 1 FROM categories WHERE id = ?;", (category_id,)
        ).fetchone()
        if not exists:
            return False

        with conn:
            conn.execute("DELETE FROM categories WHERE id = ?;", (category_id,))
            return True


def get_record_by_id(record_id: int) -> dict[str, Any] | None:
    """Отримати один запис за id разом із назвою категорії (JOIN)."""
    sql = """
        SELECT
            r.id,
            r.code,
            r.title,
            r.category_id,
            c.name AS category_name,
            r.value,
            r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?;
    """
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, (record_id,)).fetchone()
        return dict(row) if row else None


def get_record_by_code(code: str) -> dict[str, Any] | None:
    """Отримати запис за його унікальним кодом."""
    sql = """
        SELECT
            r.id,
            r.code,
            r.title,
            r.category_id,
            c.name AS category_name,
            r.value,
            r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.code = ?;
    """
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, (code.strip(),)).fetchone()
        return dict(row) if row else None


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Створити новий запис і повернути його разом із category_name."""
    clean_code = str(data["code"]).strip()
    clean_title = str(data["title"]).strip()

    insert_sql = """
        INSERT INTO records (code, title, category_id, value, status)
        VALUES (?, ?, ?, ?, ?);
    """
    select_sql = """
        SELECT
            r.id,
            r.code,
            r.title,
            r.category_id,
            c.name AS category_name,
            r.value,
            r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?;
    """
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.execute(
                insert_sql,
                (
                    clean_code,
                    clean_title,
                    data["category_id"],
                    data["value"],
                    data["status"],
                ),
            )
            record_id = cursor.lastrowid

        row = conn.execute(select_sql, (record_id,)).fetchone()
        return dict(row)


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати список записів із фільтрами та пагінацією."""
    base_query = (
        "SELECT "
        "  r.id, r.code, r.title, r.category_id, c.name AS category_name, "
        "  r.value, r.status "
        "FROM records r "
        "JOIN categories c ON r.category_id = c.id "
    )
    conditions: list[str] = []
    params: list[Any] = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)

    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)

    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)

    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    if conditions:
        base_query += "WHERE " + " AND ".join(conditions) + " "

    base_query += "ORDER BY r.id ASC LIMIT ? OFFSET ?;"
    params.extend([limit, offset])

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(base_query, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def update_record(record_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Повністю замінити змінювані поля наявного запису (PUT)."""
    clean_code = str(data["code"]).strip()
    clean_title = str(data["title"]).strip()

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row

        exists = conn.execute(
            "SELECT 1 FROM records WHERE id = ?;", (record_id,)
        ).fetchone()
        if not exists:
            return None

        update_sql = """
            UPDATE records
            SET code = ?, title = ?, category_id = ?, value = ?, status = ?
            WHERE id = ?;
        """
        with conn:
            conn.execute(
                update_sql,
                (
                    clean_code,
                    clean_title,
                    data["category_id"],
                    data["value"],
                    data["status"],
                    record_id,
                ),
            )

        select_sql = """
            SELECT
                r.id,
                r.code,
                r.title,
                r.category_id,
                c.name AS category_name,
                r.value,
                r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id = ?;
        """
        row = conn.execute(select_sql, (record_id,)).fetchone()
        return dict(row) if row else None


def delete_record(record_id: int) -> bool:
    """Видалити запис за його id."""
    with closing(get_connection()) as conn:
        exists = conn.execute(
            "SELECT 1 FROM records WHERE id = ?;", (record_id,)
        ).fetchone()
        if not exists:
            return False

        with conn:
            conn.execute("DELETE FROM records WHERE id = ?;", (record_id,))
            return True


def create_records_bulk(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Пакетне створення записів з атомарним збереженням в одній транзакції."""
    if not items:
        return []

    insert_sql = """
        INSERT INTO records (code, title, category_id, value, status)
        VALUES (?, ?, ?, ?, ?);
    """
    created_ids: list[int] = []

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            for item in items:
                cursor = conn.execute(
                    insert_sql,
                    (
                        str(item["code"]).strip(),
                        str(item["title"]).strip(),
                        item["category_id"],
                        item["value"],
                        item["status"],
                    ),
                )
                if cursor.lastrowid is not None:
                    created_ids.append(cursor.lastrowid)

        placeholders = ",".join("?" for _ in created_ids)
        select_sql = f"""
            SELECT
                r.id,
                r.code,
                r.title,
                r.category_id,
                c.name AS category_name,
                r.value,
                r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id IN ({placeholders})
            ORDER BY r.id ASC;
        """
        rows = conn.execute(select_sql, tuple(created_ids)).fetchall()
        return [dict(row) for row in rows]
