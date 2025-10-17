from .certificate import Certificate
from .__about__ import __version__
import argparse
import sys

def process_hostname(hostname, expiring_soon=False):        
        if not hostname:
            print("Error: No hostname provided.", file=sys.stderr)
            return
        
        try:
            cert = Certificate(hostname)
            
            # check if expiring_soon is set and if the certificate is not expiring soon, skip output
            if expiring_soon and not cert.is_expiring_soon():
                return False
            
            print(f"--> Checking certificate for {hostname}")
            print(cert.get_expiry_status())

            return True
        except (ConnectionError, ValueError) as e:
            print(f"--> Checking certificate for {hostname}")
            print(f"Error checking certificate for {hostname}: {e}", file=sys.stderr)
            return True

def main():
    parser = argparse.ArgumentParser(description='Check the SSL certificate for a domain name.', prog='ssl-sentinel')
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--expiring-soon',
        dest='expiring_soon',
        action='store_true',
        help='Show only certificates that are expiring within 30 days or are already expired'
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-H",
        "--hostname",
        dest="hostname",
        type=str,
        help="Domain name to check the SSL certificate for"
    )
    group.add_argument(
        "-f",
        "--file",
        dest="file",
        type=str,
        help="File containing a list of domain names to check"
    )

    args = parser.parse_args()

    if args.hostname:
        process_hostname(args.hostname, expiring_soon=args.expiring_soon)
    elif args.file:
        try: 
            with open(args.file, 'r') as f:
                for line in f:

                    hostname = line.strip()

                    if not hostname:
                        # Skip empty lines
                        continue

                    output = process_hostname(hostname, expiring_soon=args.expiring_soon)
                    
                    # Print separator only if there was output for the previous hostname
                    if output:
                        print("--"*30)

        except FileNotFoundError:
            print(f"Error: The file '{args.file}' was not found.", file=sys.stderr)
            sys.exit(1)  
    else:
        hostname = input("Enter the domain name to check the SSL certificate for: ").strip()
        process_hostname(hostname)

if __name__ == "__main__":
    main()
