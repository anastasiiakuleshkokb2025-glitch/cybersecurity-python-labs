import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from shared.student import VARIANT_NUMBER

hash_algorithm = "sha256"
min_length = 11
personal_salt = str(VARIANT_NUMBER).zfill(5)

data = Path("labs/lab01/data")
users_file = data / "users.csv"
log_file = data / "log.json"

console = Console()

users_to_register = (
    ("Alice", "CyberSecurity8"),
    ("Bob", "PasswordTest8"),
    ("Charlie", "SecureAccess8"),
    ("Diana", "StrongPass88"),
    ("Eve", "MySecretKey8"),
    ("Frank", "DataProtect8"),
    ("Grace", "NetworkSafe8"),
    ("Henry", "CryptoSecure8"),
    ("Irene", "SafePassword8"),
    ("Jack", "Information8"),
)

users_db = []

class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім")

    if salt is None or salt == "":
        raise ValueError("Сіль не може бути порожньою")

    if len(password) < min_length:
        raise ValidationError(f"Пароль має містити щонайменше {min_length} символів")

    password_with_salt = password + salt

    hash_object = hashlib.sha256(
        password_with_salt.encode("utf-8")
    )

    return hash_object.hexdigest()


def create_user(username: str, password: str) -> tuple[str, str]:
    hash_value = generate_hash(password, personal_salt)
    return username, hash_value


def create_users(users_list: tuple) -> None:
    try:
        data.mkdir(parents=True, exist_ok=True)

        with open(users_file, "w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            for username, password in users_list:
                try:
                    user = create_user(username, password)
                    writer.writerow(user)

                except ValidationError as error:
                    print(f"Помилка реєстрації {username}: {error}")

                except ValueError as error:
                    print(f"Помилка реєстрації {username}: {error}")

    except FileNotFoundError:
        print("Помилка: файл не знайдено.")

    except PermissionError:
        print("Помилка: немає дозволу на роботу з файлом.")

    except OSError as error:
        print(f"Помилка введення/виведення: {error}")


def read_users() -> list[tuple[str, str]]:
    try:
        users = []

        with open(users_file, "r" , newline="", encoding="utf-8") as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) == 2:
                    users.append((row[0], row[1]))

        return users

    except FileNotFoundError:
        print("Помилка: файл users.csv не знайдено.")

    except PermissionError:
        print("Помилка: немає дозволу на читання файлу.")

    except OSError as error:
        print(f"Помилка введення/виведення: {error}")

    return []


def print_users(users: list[tuple[str, str]]) -> None:

    table = Table(title="База користувачів")

    table.add_column("Логін")
    table.add_column("Хеш пароля")

    for username, hash_value in users:
        table.add_row(username, hash_value)

    console.print(table)


def log_event(function):

    @wraps(function)
    def wrapper(username: str, password: str) -> bool:

        result = "failure"

        try:
            success = function(username, password)

            if success:
                result = "success"

            return success

        except (ValidationError, ValueError):
            result = "failure"
            raise

        finally:
            event = {
                "event": "login",
                "user": username,
                "result": result,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "args": [],
                "kwargs": {}
            }

            try:
                data.mkdir(parents=True, exist_ok=True)

                if log_file.exists():
                    with open(log_file, "r", encoding="utf-8") as file:
                        logs = json.load(file)
                else:
                    logs = []

                logs.append(event)

                with open(log_file, "w", encoding="utf-8") as file:
                    json.dump(logs, file, indent=4, ensure_ascii=False)

            except FileNotFoundError:
                print("Помилка: файл log.json не знайдено.")

            except PermissionError:
                print("Помилка: немає дозволу на запис журналу.")

            except OSError as error:
                print(f"Помилка журналювання: {error}")

            except ValueError:
                print("Помилка: некоректний JSON-файл.")

    return wrapper


@log_event
def login(username: str, password: str) -> bool:
    if username is None or username == "":
        raise ValueError("Логін не може бути порожнім")

    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім")
    try:
        hash_value = generate_hash(password, personal_salt)
    except ValidationError:
        return False

    for db_username, db_hash in users_db:
        if db_username == username:
            return hash_value == db_hash

    return False


def run_task3() -> None:
    global users_db

    create_users(users_to_register)
    users_db = read_users()
    print_users(users_db)


if __name__ == "__main__":
    run_task3()