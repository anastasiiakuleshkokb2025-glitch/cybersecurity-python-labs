import argparse
import sys
from datetime import timedelta
from pathlib import Path

from labs.lab02.task1 import SESSION_TIMEOUT_SEC, Admin, User, UserAccount
from labs.lab02.task2 import analyze_dns_logs


def demo() -> None:
    print("Завдання 1")

    user = User("student", "student@example.com", "user")
    user.set_password("Password123!")

    account = UserAccount(user)

    print("\nУспішний вхід:")
    print(account.login("student", "Password123!", "192.168.1.10"))

    print("\nНевдалий вхід:")
    print(account.login("student", "WrongPassword", "192.168.1.10"))

    print("\nЗміна email:")
    account["user"].email = "new_email@example.com"
    print(account["user"].email)

    print("\nПеревірка неправильного email:")
    try:
        account["user"].email = "wrongemail"
    except ValueError as error:
        print("Помилка:", error)

    print("\nПрава адміністратора:")
    admin = Admin("admin", "admin@example.com")
    admin.grant_permission("read_users")
    admin.grant_permission("delete_users")
    print(admin)

    print("delete_users:", admin.has_permission("delete_users"))

    admin.revoke_permission("delete_users")
    print("delete_users після видалення:", admin.has_permission("delete_users"))

    print("\nПеревірка таймауту:")
    account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    print("Сесія активна:", account.is_authenticated())

    print("\nВихід із системи:")
    account.logout()
    print("Сесія:", account.session)

    print("\nAuditLog:")
    account["audit_log"].show_all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Лабораторна робота №2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. demo (Завдання 1)
    subparsers.add_parser("demo")

    # 2. analyze (Завдання 2, Варіант 8)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--dns-log", required=True)
    analyze_parser.add_argument("--blacklist", required=True)
    analyze_parser.add_argument("--out-csv", required=True)
    analyze_parser.add_argument("--min-domain-len", type=int, default=30)

    args = parser.parse_args()

    if args.command == "demo":
        demo()
    elif args.command == "analyze":
        try:
            analyze_dns_logs(
                dns_log_path=Path(args.dns_log),
                blacklist_path=Path(args.blacklist),
                output_csv_path=Path(args.out_csv),
                min_domain_len=args.min_domain_len,
            )
        except (FileNotFoundError, PermissionError, OSError) as err:
            print(f"[ERROR] Помилка роботи з файлами: {err}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
