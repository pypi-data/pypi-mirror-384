import re
from parsers.date_parser import parse_date
from parsers.time_parser import parse_time
from parsers.ip_parser import parse_ip

_OCTET_RE = r"(25[0-5]|2[0-4]\d|1?\d{1,2})"
LOG_LINE_RE = re.compile(
    rf"^(\d{{2}}/\d{{2}}/\d{{4}})\s+(\d{{2}}:\d{{2}})\s+({_OCTET_RE}\.{_OCTET_RE}\.{_OCTET_RE}\.{_OCTET_RE}/(?:8|16|24))$"
)

def parse_log_entry(log_entry: str) -> tuple[str, str, str]:
    m = LOG_LINE_RE.match(log_entry.strip())
    if not m:
        return ("", "", "")
    return m.group(1), m.group(2), m.group(3)

def parse_log_file(file_path: str) -> list[dict]:
    results: list[dict] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                date_s, time_s, ip_s = parse_log_entry(line)
                if not date_s:
                    continue
                date_d = parse_date(date_s)
                time_d = parse_time(time_s)
                ip_d = parse_ip(ip_s)
                if date_d and time_d and ip_d:
                    results.append({
                        "log_date": date_d,
                        "log_timestamp": time_d,
                        "ip_info": ip_d
                    })
    except FileNotFoundError:
        return []
    return results
