import sqlite3
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Records"])


@router.get("", response_model=list[RecordRead])
def get_records(
    category_id: int | None = Query(None, gt=0),
    status_val: Literal["new", "in_progress", "done"] | None = Query(
        None, alias="status"
    ),
    min_value: float | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Отримати список записів із фільтрами та пагінацією."""
    return repository.get_records(
        category_id=category_id,
        status=status_val,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=RecordRead)
def get_record(record_id: int):
    """Отримати один запис за id."""
    if record_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID має бути додатним числом.",
        )
    record = repository.get_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    return record


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_record(record_data: RecordCreate):
    """Створити один запис."""

    if not repository.get_category_by_id(record_data.category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з id={record_data.category_id} не знайдено.",
        )

    if repository.get_record_by_code(record_data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Запис із кодом '{record_data.code}' вже існує.",
        )

    try:
        return repository.create_record(record_data.model_dump())
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Помилка цілісності даних: {e}",
        )


@router.post(
    "/bulk", response_model=list[RecordRead], status_code=status.HTTP_201_CREATED
)
def create_records_bulk(items: list[RecordCreate]):
    """Пакетне створення записів (1-100) у межах однієї атомарної транзакції."""
    if not (1 <= len(items) <= 100):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пакет має містити від 1 до 100 елементів.",
        )

    codes_in_bulk = [item.code for item in items]
    if len(codes_in_bulk) != len(set(codes_in_bulk)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пакет містить дубльовані коди.",
        )

    for item in items:
        if not repository.get_category_by_id(item.category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Категорію з id={item.category_id} не знайдено.",
            )
        if repository.get_record_by_code(item.code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Запис із кодом '{item.code}' вже існує в базі.",
            )

    try:
        raw_items = [item.model_dump() for item in items]
        return repository.create_records_bulk(raw_items)
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Помилка транзакції пакета: {e}",
        )


@router.put("/{record_id}", response_model=RecordRead)
def update_record(record_id: int, record_data: RecordReplace):
    """Повна заміна наявного запису."""
    if record_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID має бути додатним числом.",
        )

    if not repository.get_record_by_id(record_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )

    if not repository.get_category_by_id(record_data.category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з id={record_data.category_id} не знайдено.",
        )

    existing = repository.get_record_by_code(record_data.code)
    if existing and existing["id"] != record_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Код '{record_data.code}' вже використовується іншим записом.",
        )

    updated = repository.update_record(record_id, record_data.model_dump())
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    return updated


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int):
    """Видалити запис."""
    if record_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID має бути додатним числом.",
        )

    deleted = repository.delete_record(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    return None