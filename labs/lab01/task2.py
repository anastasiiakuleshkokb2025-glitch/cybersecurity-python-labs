users = {
    "crypto_specialist": {
        "role": "cryptographer",
        "clearance": 4,
        "department": "Cryptography",
        "active": True
    },
    "privacy_officer": {
        "role": "privacy_analyst",
        "clearance": 3,
        "department": "Privacy",
        "active": True
    },
    "data_scientist": {
        "role": "data_analyst",
        "clearance": 2,
        "department": "Analytics",
        "active": True
    },
    "field_engineer": {
        "role": "field_support",
        "clearance": 2,
        "department": "Field Ops",
        "active": True
    },
    "test_account": {
        "role": "testing",
        "clearance": 1,
        "department": "QA",
        "active": False
    }
}


resources = [
    ("encryption_keys", 4),
    ("privacy_policies", 3),
    ("anonymized_data", 2),
    ("field_reports", 2),
    ("crypto_algorithms", 4),
    ("consent_forms", 1),
    ("data_classification", 3),
    ("key_management", 4),
    ("statistical_models", 2),
    ("public_datasets", 1)
]

security_levels = (
    "Unclassified",
    "For Official Use",
    "Confidential",
    "Secret"
)

blocked_users = {
    "test_account",
    "gdpr_violation",
    "data_breach_user"
}


def get_security_level(level):
    """Повертає назву рівня безпеки ресурсу."""
    return security_levels[level - 1]


def print_resources():
    """Виводить список усіх ресурсів."""
    print("Ресурси системи:")

    for resource, level in resources:
        security_name = get_security_level(level)
        print(f"Ресурс {resource} - {security_name}")


def check_access(username, resource_level):
    """Перевіряє доступ користувача до ресурсу."""

    if username not in users:
        return "DENY", "User not found"

    if username in blocked_users:
        return "DENY", "User is blocked"

    user = users[username]

    if user["active"] is False:
        return "DENY", "Account inactive"

    if user["clearance"] >= resource_level:
        return "ALLOW", ""

    return "DENY", "Insufficient clearance"


def check_all_access():
    """Перевіряє доступ кожного користувача до кожного ресурсу."""

    for username in users:
        for resource_name, resource_level in resources:

            result, reason = check_access(
                username,
                resource_level
            )

            if result == "ALLOW":
                print(f"user={username} , resource={resource_name} -> ALLOW")
            else:
                print(f"user={username}, resource={resource_name} -> DENY ({reason})")


def main():
    print_resources()
    print()

    check_all_access()


if __name__ == "__main__":
    main()