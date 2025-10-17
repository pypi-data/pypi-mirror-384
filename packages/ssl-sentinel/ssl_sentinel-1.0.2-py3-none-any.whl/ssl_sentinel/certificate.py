import ssl
import socket
import datetime

EXPIRING_DAYS_THRESHOLD = 30

class Certificate:
    def __init__(self, hostname):
        self.hostname = hostname
        self.cert = None
        self.context = ssl.create_default_context()

        try:
            with socket.create_connection((self.hostname, 443), timeout=5) as sock:
                with self.context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    self.cert = ssock.getpeercert()
        except (OSError, ssl.SSLError, ValueError) as e:
            raise ConnectionError(f"Could not retrieve certificate for {self.hostname}: {e}")

    def expiry_date(self):
        #Returns the expiry date of the certificate as a datetime object.
        try:
            if self.cert is None:
                raise ValueError("Certificate data is not available.")
    
            expiry_date_str = self.cert.get('notAfter')
    
            if not expiry_date_str:
                raise ValueError("Expiry date not found in certificate.")
            return datetime.datetime.strptime(str(expiry_date_str), '%b %d %H:%M:%S %Y %Z')
        except (ValueError, KeyError) as e:
            raise ValueError(f"Could not parse expiry date for {self.hostname}: {e}")
    
    def days_until_expiration(self):
        #Returns the number of days until the certificate expires.
        expiry_date = self.expiry_date()
        return (expiry_date - datetime.datetime.now()).days

    def get_expiry_status(self):
        #Returns a string indicating the expiry status of the certificate.
        try:
            days_left = self.days_until_expiration()
            expiry_date = self.expiry_date().strftime('%Y-%m-%d')

            if days_left <= 0:
                return f"Status: EXPIRED on {expiry_date}"
            elif days_left <= EXPIRING_DAYS_THRESHOLD:
                return f"Status: WARNING - Expires in {days_left} days (on {expiry_date})"
            return f"Status: OK - Valid for {days_left} more days (expires on {expiry_date})"
        except ValueError as e:
            return f"Status: ERROR - Could not determine expiry status: {e}"

    def is_expiring_soon(self, days_threshold=EXPIRING_DAYS_THRESHOLD):
        #Checks if the certificate is expired or expiring within the threshold.
        try:
            days_left = self.days_until_expiration()
            return days_left <= days_threshold
        except ValueError:
            # If we can't determine the days left, treat it as an issue to be reported.
            return True
