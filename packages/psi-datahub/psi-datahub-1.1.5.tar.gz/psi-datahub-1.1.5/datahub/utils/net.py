########################################################################################################################
# HTTP Utilities
########################################################################################################################

import datahub
import json
from http.client import HTTPSConnection, HTTPConnection
import ssl
import urllib
import re
import sys
import logging
import socket

_logger = logging.getLogger(__name__)

def get_host_port_from_stream_address(stream_address):
    if stream_address.startswith("ipc"):
        return stream_address.split("//")[1], -1
    source_host, source_port = stream_address.rsplit(":", maxsplit=1)
    if "//" in source_host:
        source_host = source_host.split("//")[1]
    return source_host, int(source_port)

def create_http_conn(up, timeout=None):
    if type(up) == str:
        up = urllib.parse.urlparse(up)
    if timeout is None:
        timeout = socket._GLOBAL_DEFAULT_TIMEOUT
    if up.scheme == "https":
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ctx.check_hostname = False
        port = up.port
        if port is None:
            port = 443
        conn = HTTPSConnection(up.hostname, port, context=ctx, timeout=timeout)
    else:
        port = up.port
        if port is None:
            port = 80
        conn = HTTPConnection(up.hostname, port, timeout=timeout)
    return conn


def http_req(method, url, conn=None, timeout=None):
    headers = {
        "X-PythonDataAPIPackageVersion": datahub.version(),
        "X-PythonDataAPIModule": __name__,
        "X-PythonVersion": re.sub(r"[\t\n]", " ", str(sys.version)),
        "X-PythonVersionInfo": str(sys.version_info),
    }
    up = urllib.parse.urlparse(url)
    if conn is None:
        conn = create_http_conn(up, timeout)
    conn.request(method, up.path, None, headers)
    #return conn.getresponse()
    return conn



def get_default_header():
    return {   "User-Agent": datahub.package_name(),
               "Accept-Encoding": "gzip, deflate, br",
               "Accept": "*/*",
               "Content-Type": "application/json",
               "Connection": "keep-alive",
            }


def http_data_query(query, url, method = "POST", content_type="application/json", accept="application/octet-stream", add_headers={}, conn=None, timeout=None):
    headers = get_default_header()
    headers["Content-Type"] = content_type
    headers["Accept"] = accept
    headers.update(add_headers)

    up = urllib.parse.urlparse(url)
    if conn is None:
        conn = create_http_conn(up, timeout)
    if method == "GET":
        params = urllib.parse.urlencode(query)
        url = f'{url}?{params}'
        conn.request("GET", url, headers=headers)
    else:
        body = json.dumps(query)
        conn.request(method, up.path, body, headers)
    return conn

def get_json(url, timeout=None):
    conn = http_req("GET", url, timeout=timeout)
    try:
        res = conn.getresponse()
        body = res.read().decode()
        try:
            return json.loads(body)
        except:
            _logger.error(f"can not parse request status as json\n" + body)
            return body
    finally:
        conn.close()

def save_raw(query, url, fname, timeout=None):
    conn = http_data_query(query, url, timeout)
    try:
        s = conn.getresponse()
        with open(fname, "wb") as f1:
            while True:
                buf = s.read()
                if buf is None:
                    break
                if len(buf) < 0:
                    raise RuntimeError()
                if len(buf) == 0:
                    break
                f1.write(buf)
    finally:
        conn.close()

