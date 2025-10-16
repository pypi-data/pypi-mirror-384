import sys
from .check import check_ips  # updated import

def print_usage():
    print("""
Usage: aws-ip-check <IP1> [IP2] [IP3 ...]
Check if the given IPs belong to AWS ranges.

Options:
  --help      Show this help message and exit
""")

def main():
    if "--help" in sys.argv or len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    ips_to_check = [arg for arg in sys.argv[1:] if arg != "--help"]
    results = check_ips(ips_to_check)
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
