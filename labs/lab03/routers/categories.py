import sqlite3
from fastapi import APIRouter, HTTPException, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryRead])
def get_categories():
    """Отримати список усіх категорій, відсортований за id."""
    return repository.get_categories()


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate):
    """Створити нову категорію."""

    if repository.get_category_by_name(category.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Категорія з назвою '{category.name}' вже існує.",
        )
    try:
        return repository.create_category(category.name)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категорія з такою назвою вже існує.",
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int):
    """Видалити порожню категорію."""
    if category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID має бути додатним числом.",
        )

    cat = repository.get_category_by_id(category_id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категорію не знайдено.",
        )

    if repository.check_category_has_records(category_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Неможливо видалити категорію, яка містить записи.",
        )

    repository.delete_category(category_id)
    return None