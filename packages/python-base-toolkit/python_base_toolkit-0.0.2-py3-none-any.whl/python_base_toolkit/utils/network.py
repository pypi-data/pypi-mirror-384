import ipaddress
import os
import re

from custom_python_logger import get_logger

from python_base_toolkit.consts.operating_system import Platform

logger = get_logger(__name__)


def is_ip_address(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_ip_version(ip: str) -> int | None:
    """
    Returns the type of the IP address as integer (IPv4, IPv6 or None in case of an invalid IP address)
    :param ip: IP address (String)
    """
    try:
        _ip = ipaddress.ip_address(ip)
        return _ip.version
    except ValueError:
        return None


def normalize_connection_string(ip: str, port: int | None = None) -> str:
    """
    Returns a normalized connection string (IPv4:port or [IPv6]:port)
    :param ip: IP address (String)
    :param port: Port (Integer or None) - Optional for cases where the port is not needed (E.G. for SCP)

    Output:
    w/ Port - IPv4:port or [IPv6]:port
    w/o Port - IPv4: or [IPv6]:
    """
    _operation = "Normalize connection string"

    _ip_version = get_ip_version(ip)
    if _ip_version == 4:
        return f'{ip}:{port or ""}'
    if _ip_version == 6:
        return f'[{ip}]:{port or ""}'
    raise ValueError(f"Invalid IP address: {ip} - {_operation}")


def normalize_http_url(ip: str, port: int | None = None, https: bool = True) -> str:
    """
    Returns a normalized HTTP URL (http://IPv4:port or http://[IPv6]:port)
    :param ip: IP address (String)
    :param port: Port (Integer)
    :param https: Use HTTPS (Boolean)
    """
    url_schema = "https" if https else "http"
    return f"{url_schema}://{normalize_connection_string(ip, port)}"


def parse_ifconfig_to_json(ifconfig_output: str) -> dict:
    """
    Output Example:
    {
        'interface_name': {
            'mac_address': <String>,
            'ipv4_address': <String>,
            'ipv4_netmask': <String>,
            'ipv6_address': <String>
            'ipv6_prefixlen': <String>
        }
    }
    """
    interfaces = {}
    current_interface = None

    for line in ifconfig_output.splitlines():
        if match_interface := re.match("^(\\S+):\\s", line):
            current_interface = match_interface.group(1)
            interfaces[current_interface] = {}

        match_mac = re.search(r"ether\s([0-9a-f:]+)", line)
        if match_mac and current_interface:
            interfaces[current_interface]["mac_address"] = match_mac.group(1)

        match_ipv4 = re.search(r"inet\s(\d+\.\d+\.\d+\.\d+)", line)
        if match_ipv4 and current_interface:
            interfaces[current_interface]["ipv4_address"] = match_ipv4.group(1)

        # Try different netmask patterns
        match_netmask = re.search(r"netmask\s+(0x[0-9a-f]+|(?:\d+\.){3}\d+)", line, re.IGNORECASE)
        if match_netmask and current_interface:
            netmask = match_netmask.group(1)
            if netmask.startswith("0x"):
                # Handle hex format
                netmask_int = int(netmask, 16)
            else:
                # Handle decimal format (255.255.255.0)
                octets = [int(x) for x in netmask.split(".")]
                netmask_int = sum(octet << (24 - 8 * i) for i, octet in enumerate(octets))

            binary_netmask = f"{netmask_int:032b}"
            interfaces[current_interface]["ipv4_netmask"] = binary_netmask.count("1")

        match_ipv6 = re.search(r"inet6\s([0-9a-fA-F:]+)", line)
        if match_ipv6 and current_interface:
            interfaces[current_interface]["ipv6_address"] = match_ipv6.group(1)

        match_subnet_mask = re.search(r"prefixlen\s([0-9a-f:]+)", line)
        if match_subnet_mask and current_interface:
            interfaces[current_interface]["ipv6_prefixlen"] = match_subnet_mask.group(1)

    return interfaces


def check_ping_from_linux(ip_address: str, number_of_ping: int = 4) -> bool:
    try:
        if os.system(f"ping -c {number_of_ping} {ip_address}") == 0:
            return True
        return False
    except Exception as e:
        logger.exception(f"ping to {ip_address} failed: {e}")
        return False


def check_ping_from_windows(ip_address: str, number_of_ping: int = 4) -> bool:
    try:
        if os.system(f"ping -c {number_of_ping} {ip_address}") == 0:
            return True
        return False
    except Exception as e:
        logger.exception(f"ping to {ip_address} failed: {e}")
        return False


def check_ping_status(platform: Platform, ip_address: str, number_of_ping: int = 4) -> bool:
    """
    Check the ping status of an IP address based on the operating system platform.
    """
    if platform in [Platform.LINUX, Platform.MACOS]:
        return check_ping_from_linux(ip_address, number_of_ping)
    if platform == Platform.WINDOWS:
        return check_ping_from_windows(ip_address, number_of_ping)
    raise ValueError(f"Unsupported platform: {platform}")
