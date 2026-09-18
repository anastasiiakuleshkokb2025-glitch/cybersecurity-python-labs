import random
import string

from rich.console import Console
from rich.table import Table

passwords = [
    "ThreatH@nt3r", "weak123", "P3n3trat10n@Test", "visitor",
    "Cyber@Defense2023", "normal", "Incident@R3sp0nse", "standard", 
    "Risk@Analys1s", "typical"
]

criteria = {
    "min_length": 10,
    "require_digits": True, 
    "require_upper": True, 
    "require_special": True
}

forbidden_passwords = {"weak123", "visitor", "normal", "standard", "typical", "admin"}

console = Console()


def add_duplicates(password_list):
    indexes = random.sample(range(len(password_list)), 3)

    for index in indexes:
        password_list.append(password_list[index])


def check_criteria(password):
    return {
        "length": len(password) >= criteria["min_length"],
        "digit": any(char.isdigit() for char in password),
        "upper": any(char.isupper() for char in password),
        "special": any(char in string.punctuation for char in password),
        "lower": any(char.islower() for char in password),
    }


def analyze_password(password, password_list):
    if password in forbidden_passwords:
        return "Заборонений"

    if len(password) < criteria["min_length"]:
        return "Заборонений"

    checks = check_criteria(password)
    vsi_kryterii_vykonano = all(checks.values())

    vykonano_kryteriiv = sum(checks.values())

    if vykonano_kryteriiv == 1:
        return "Слабкий"

    if vykonano_kryteriiv < 5:
        return "Середній"

    if vsi_kryterii_vykonano:
        if len(password) < criteria["min_length"] + 4:
            return "Сильний"

        if password_list.count(password) == 1:
            return "Дуже сильний"

        return "Сильний"

    return "Середній"


def analyze_passwords(password_list):

    results = []

    for password in password_list:
        level = analyze_password(password, password_list)

        results.append({"password": password, "level": level})

    return results


def print_results(results):

    table = Table(title="Аналіз надійності паролів")

    table.add_column("Пароль")
    table.add_column("Рівень надійності")

    for result in results:
        table.add_row(result["password"], result["level"])

    console.print(table)


def run_task1():

    password_list = passwords.copy()
    add_duplicates(password_list)
    results = analyze_passwords(password_list)
    print_results(results)


if __name__ == "__main__":
    run_task1()
