import requests
import ipaddress

def fetch_aws_ip_ranges():
    """Download the latest AWS IP ranges JSON"""
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def check_ip_in_aws(ip_str, aws_data):
    """Check a single IP against AWS ranges"""
    try:
        ip_addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return f"{ip_str} → Invalid IP"

    for prefix in aws_data['prefixes']:
        network = ipaddress.ip_network(prefix['ip_prefix'])
        if ip_addr in network:
            return f"{ip_str} → {prefix['ip_prefix']} ({prefix['service']}, {prefix['region']})"
    return f"{ip_str} → Not found in AWS ranges"

def check_ips(ips_list):
    """Check multiple IPs and return results"""
    aws_data = fetch_aws_ip_ranges()
    return [check_ip_in_aws(ip, aws_data) for ip in ips_list]
