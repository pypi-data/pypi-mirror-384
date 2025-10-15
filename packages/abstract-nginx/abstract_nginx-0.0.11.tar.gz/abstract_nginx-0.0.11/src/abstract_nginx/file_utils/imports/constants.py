import re

# === IP-only regex patterns ===
LOCAL_IP_RE   = r"127\.0\.0\.1"
PUBLIC_IP_RE  = r"0\.0\.0\.0"
GENERAL_IP_RE = r"(?:\d{1,3}\.){3}\d{1,3}"

# === Builder ===
def with_port(ip_pattern: str) -> str:
    """Append :{port} matcher to an IP regex pattern."""
    return rf"({ip_pattern}):(\d+)"

# === Composite host patterns ===
LOCAL_HOST_RE   = with_port(LOCAL_IP_RE)
PUBLIC_HOST_RE  = with_port(PUBLIC_IP_RE)
GENERAL_HOST_RE = with_port(GENERAL_IP_RE)

# === Search function ===
def find_host_and_port(text: str):
    """
    Search for any recognized host pattern and return (ip_type, ip, port) tuple.
    Returns None if no match found.
    """
    patterns = {
        "local": re.compile(LOCAL_HOST_RE),
        "public": re.compile(PUBLIC_HOST_RE),
        "general": re.compile(GENERAL_HOST_RE),
    }

    for ip_type, pattern in patterns.items():
        match = pattern.search(text)
        if match:
            ip, port = match.groups()
            return {"type": ip_type, "ip": ip, "port": int(port)}

    return None
def derive_port(text: str):
    host_and_port = find_host_and_port(text)
    if host_and_port == None:
        return extract_port_from_service(text)
    return host_and_port.get('port')
def derive_host(text: str):
    host_and_port = find_host_and_port(text)
    return host_and_port.get('host')
def derive_host_type(text: str):
    host_and_port = find_host_and_port(text)
    return host_and_port.get('type')
def extract_port_from_service(text: str):
    """
    Extract the port number from a systemd .service file content.
    Looks for Environment=PORT=XXXX in any format.
    Returns int(port) if found, else None.
    """
    # Handles:
    #   Environment=PORT=6050
    #   Environment="PORT=6050 NODE_ENV=production"
    #   Environment='PORT=6050'
    pattern = re.compile(r'Environment=.*?\bPORT\s*=\s*"?(\d+)"?')
    
    match = pattern.search(text)
    if match:
        return int(match.group(1))
    return None
