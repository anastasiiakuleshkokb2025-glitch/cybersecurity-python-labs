"""labs/lab02/task2.py

Варіант 8: Фільтр та аналізатор журналів DNS-запитів.
"""

import csv
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("dns_analyzer")

# Регулярні вирази для евристики виявлення аномальних та DGA доменів
SUSPICIOUS_TLDS = {".xyz", ".top", ".club", ".buzz", ".work", ".cfd", ".ru", ".tk"}
SUBDOMAIN_DGA_REGEX = re.compile(
    r"^(?P<subdomain>[a-z0-9]{10,})\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$",
    re.IGNORECASE,
)


@dataclass
class DNSAlert:
    """Клас даних для збереження інформації про виявлену аномалію."""

    timestamp: str
    client_ip: str
    domain: str
    query_type: str
    alert_type: str
    reason: str


def calculate_entropy(s: str) -> float:
    """Обчислення ентропії Шеннона для визначення випадковості рядка (DGA)."""
    if not s:
        return 0.0
    freq = Counter(s.lower())
    length = len(s)
    return -sum((cnt / length) * math.log2(cnt / length) for cnt in freq.values())


def load_blacklist(blacklist_path: Path) -> set[str]:
    """Зчитування локального чорного списку доменів із обробкою винятків."""
    blacklist = set()
    try:
        with blacklist_path.open("r", encoding="utf-8") as f:
            for line in f:
                domain = line.strip().lower()
                if domain and not domain.startswith("#"):
                    blacklist.add(domain)
    except FileNotFoundError:
        logger.error("Blacklist file not found: %s", blacklist_path)
        raise
    except PermissionError:
        logger.error(
            "Permission denied when accessing blacklist file: %s", blacklist_path
        )
        raise
    except OSError as err:
        logger.error("OS error reading blacklist file %s: %s", blacklist_path, err)
        raise
    return blacklist


def parse_dns_line(line: str) -> dict[str, str] | None:
    """Парсинг рядка логу (CSV або текстовий формат)."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = [part.strip().strip('"') for part in line.split(",")]
    if len(parts) >= 4 and parts[0].lower() != "timestamp":
        return {
            "timestamp": parts[0],
            "client_ip": parts[1],
            "domain": parts[2],
            "query_type": parts[3].upper(),
        }

    tokens = line.split()
    if len(tokens) >= 4:
        return {
            "timestamp": tokens[0],
            "client_ip": tokens[1],
            "domain": tokens[2],
            "query_type": tokens[3].upper(),
        }

    return None


def analyze_dns_logs(
    dns_log_path: Path,
    blacklist_path: Path,
    output_csv_path: Path,
    min_domain_len: int = 30,
) -> None:
    """Головна функція аналізу DNS-запитів."""
    # 1. Завантаження чорного списку
    blacklist = load_blacklist(blacklist_path)

    query_counter: Counter[str] = Counter()
    alerts: list[DNSAlert] = []
    total_records = 0

    # 2. Зчитування та обробка лог-файлу
    try:
        with dns_log_path.open("r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                try:
                    entry = parse_dns_line(raw_line)
                    if not entry:
                        continue

                    total_records += 1
                    domain = entry["domain"].lower()
                    qtype = entry["query_type"]
                    client_ip = entry["client_ip"]
                    ts = entry["timestamp"]

                    query_counter[qtype] += 1

                    # Перевірка 1: Чорний список (Blacklist)
                    if domain in blacklist:
                        alerts.append(
                            DNSAlert(
                                timestamp=ts,
                                client_ip=client_ip,
                                domain=domain,
                                query_type=qtype,
                                alert_type="BLACKMATCH",
                                reason=f"Client {client_ip} queried blacklisted domain: {domain}",
                            )
                        )
                        continue

                    # Перевірка 2: Аномальна довжина (DGA / тунелювання)
                    if len(domain) >= min_domain_len:
                        if qtype == "TXT":
                            reason = f"Abnormally long TXT query domain: {domain} (Length: {len(domain)})"
                        else:
                            reason = f"Suspicious long domain: {domain} (Length: {len(domain)}) (Client: {client_ip})"

                        alerts.append(
                            DNSAlert(
                                timestamp=ts,
                                client_ip=client_ip,
                                domain=domain,
                                query_type=qtype,
                                alert_type="DGA-DETECT",
                                reason=reason,
                            )
                        )
                        continue

                    # Перевірка 3: Випадковий піддомен з високою ентропією
                    match = SUBDOMAIN_DGA_REGEX.match(domain)
                    subdomain = (
                        match.group("subdomain") if match else domain.split(".")[0]
                    )
                    entropy = calculate_entropy(subdomain)

                    if len(subdomain) >= 12 and entropy >= 3.4:
                        alerts.append(
                            DNSAlert(
                                timestamp=ts,
                                client_ip=client_ip,
                                domain=domain,
                                query_type=qtype,
                                alert_type="DGA-DETECT",
                                reason=f"High entropy / suspicious subdomain: {domain} (Client: {client_ip})",
                            )
                        )
                        continue

                    # Перевірка 4: Підозрілі зони TLD
                    if any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
                        alerts.append(
                            DNSAlert(
                                timestamp=ts,
                                client_ip=client_ip,
                                domain=domain,
                                query_type=qtype,
                                alert_type="SUSPICIOUS-TLD",
                                reason=f"Suspicious TLD query: {domain} (Client: {client_ip})",
                            )
                        )

                except (ValueError, IndexError, KeyError) as line_err:
                    logger.debug(
                        "Skipping invalid record at line %d: %s", line_no, line_err
                    )

    except FileNotFoundError:
        logger.error("DNS log file not found: %s", dns_log_path)
        raise
    except PermissionError:
        logger.error("Permission denied when reading %s", dns_log_path)
        raise
    except OSError as err:
        logger.error("OS error reading log file %s: %s", dns_log_path, err)
        raise

    # 3. Виведення у консоль точно за прикладом із методички
    print(f"[INFO] Parsing DNS log file {dns_log_path}...")
    print(f"[INFO] Processed {total_records:,} DNS query records.\n")

    print("=== Query Type Breakdown ===")
    for qtype, count in query_counter.most_common():
        pct = (count / total_records * 100) if total_records > 0 else 0.0
        print(f"{qtype:<5}: {count:,} ({pct:.1f}%)")

    print("\n=== Suspicious DNS Activity ===")
    for alert in alerts:
        print(f"[{alert.alert_type}] {alert.reason}")

    # 4. Збереження результатів у CSV
    try:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with output_csv_path.open("w", newline="", encoding="utf-8") as out_f:
            writer = csv.writer(out_f)
            writer.writerow(
                ["Timestamp", "ClientIP", "Domain", "QueryType", "AlertType", "Reason"]
            )
            for alert in alerts:
                writer.writerow(
                    [
                        alert.timestamp,
                        alert.client_ip,
                        alert.domain,
                        alert.query_type,
                        alert.alert_type,
                        alert.reason,
                    ]
                )
        print(f"\n[INFO] Suspicious records exported to {output_csv_path}")
    except PermissionError:
        logger.error("Permission denied when writing CSV to %s", output_csv_path)
        raise
    except OSError as err:
        logger.error("Failed to write CSV output %s: %s", output_csv_path, err)
        raise
