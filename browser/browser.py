import sys
import json
import socket
import requests
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox

# DNS address (domain) to look up IPs for
DNS_ADDRESS = "example.com"

# Cache file path
CACHE_FILE_PATH = "ip_cache.json"

class Browser(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Web Browser with IP Fetcher')
        self.setGeometry(100, 100, 800, 600)

        # Input field for URL/JSON path
        self.url_field = QLineEdit(self)
        self.go_button = QPushButton('Go', self)
        self.go_button.clicked.connect(self.navigate_to_url)

        self.view = QWebEngineView(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.url_field)
        layout.addWidget(self.go_button)
        layout.addWidget(self.view)

        self.show()

    def get_ip_from_web(self, url):
        """Fetches IPs from a web address (expects JSON response)."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("ips", [])
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Error fetching from {url}: {e}")
            return []

    def get_ip_from_cache(self):
        """Fetches IPs from a cached JSON file."""
        if os.path.exists(CACHE_FILE_PATH):
            try:
                with open(CACHE_FILE_PATH, 'r') as f:
                    data = json.load(f)
                return data.get(DNS_ADDRESS, [])
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", f"Error decoding JSON from cache")
                return []
        return []

    def cache_ip_addresses(self, ips):
        """Caches the fetched IP addresses in a JSON file."""
        try:
            cache_data = {}
            if os.path.exists(CACHE_FILE_PATH):
                with open(CACHE_FILE_PATH, 'r') as f:
                    cache_data = json.load(f)
            cache_data[DNS_ADDRESS] = ips  # Update cache with new IPs
            with open(CACHE_FILE_PATH, 'w') as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error writing to cache: {e}")

    def fetch_file_from_ip(self, ip, port=8080):
        """Connects to the server at the given IP to retrieve a file."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                request = "GET /file.txt HTTP/1.1\r\nHost: {}\r\n\r\n".format(ip)
                sock.sendall(request.encode())
                response = sock.recv(4096)
                return response.decode()
        except (socket.error, ConnectionRefusedError) as e:
            QMessageBox.critical(self, "Error", f"Error connecting to {ip}: {e}")
            return None

    def resolve_dns_to_ip(self):
        """Looks up IP addresses for the DNS address by querying an API or DNS server."""
        url = f"https://dns-api.org/ANY/{DNS_ADDRESS}"  # You can replace this with any working DNS API
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Extracting IP addresses from the DNS response
            ips = [record['value'] for record in data if 'value' in record]
            return ips
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Error resolving DNS {DNS_ADDRESS}: {e}")
            return []

    def navigate_to_url(self):
        address = self.url_field.text()

        # First, try to use cached IP addresses
        ips = self.get_ip_from_cache()

        # If no cached IPs, resolve the DNS address
        if not ips:
            ips = self.resolve_dns_to_ip()
            if ips:
                # Cache the new IP addresses
                self.cache_ip_addresses(ips)

        if ips:
            QMessageBox.information(self, "IPs Found", f"Found IPs: {ips}")
            for ip in ips:
                content = self.fetch_file_from_ip(ip)
                if content:
                    # Create an HTML display of the content in the web view
                    self.view.setHtml(content)
                    break
        else:
            QMessageBox.warning(self, "No IPs Found", "No IPs were found from the provided source.")

# Application start
app = QApplication(sys.argv)
browser = Browser()
sys.exit(app.exec_())
