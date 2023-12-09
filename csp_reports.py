#!/usr/bin/env python3
# coding: utf-8

""" Docker CSP Reports """

import json
import logging
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytz

# Global Variables
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
TIME_ZONE = os.environ.get("TIME_ZONE", "INFO").upper()

# Logging Configuration
try:
    pytz.timezone(TIME_ZONE)
    logging.Formatter.converter = lambda *args: datetime.now(
        tz=pytz.timezone(TIME_ZONE)
    ).timetuple()
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        level=LOG_LEVEL,
    )
except pytz.exceptions.UnknownTimeZoneError:
    logging.Formatter.converter = lambda *args: datetime.now(
        tz=pytz.timezone("Europe/Paris")
    ).timetuple()
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        level="INFO",
    )
    logging.error("TIME_ZONE invalid : %s !", TIME_ZONE)
    os._exit(1)
except ValueError:
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        level="INFO",
    )
    logging.error("LOG_LEVEL invalid !")
    os._exit(1)

# HTTP Port Verification
try:
    HTTP_PORT = int(os.environ.get("HTTP_PORT", "9999"))
except ValueError:
    logging.error("HTTP_PORT must be int !")
    sys.exit(1)


def handle(request):
    """Handle HTTP Request"""
    try:
        content_length = int(request.headers.get("Content-Length"))
        if request.headers.get("Content-Type") != "application/csp-report":
            response = {"exception": "Content-Type must be application/csp-report"}
            return 400, response
        response = json.loads(request.rfile.read(content_length))
    except TypeError:
        response = {"exception": "Empty POST data"}
        return 400, response
    except ValueError:
        response = {"exception": "Invalid JSON POST data"}
        return 400, response
    return 200, response


# Class Definition
class PostHandler(BaseHTTPRequestHandler):
    """POST Handler Class"""

    server_version = "CSP Reports"
    sys_version = "Docker"

    def _set_headers(self, code):
        """Manage HTTP Headers & HTTP Code"""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def log_message(self, format, *args):
        """Silent Default Logging"""
        return

    def do_POST(self):
        """Handle HTTP POST Request"""
        code, response = handle(self)
        self._set_headers(code)
        data = json.dumps(response)
        self.wfile.write(data.encode())
        logging.info(data)


# Main Program
if __name__ == "__main__":
    logging.info("Starting HTTP Server on port: %s.", HTTP_PORT)
    logging.debug("LOG LEVEL: %s", LOG_LEVEL)
    logging.debug("HTTP PORT: %s", HTTP_PORT)
    logging.debug("TIME ZONE: %s", TIME_ZONE)
    httpd = HTTPServer(("0.0.0.0", HTTP_PORT), PostHandler)  # nosec B104
    httpd.serve_forever()
