#!/usr/bin/env python3
"""Public, credential-free connectivity diagnostic for NYC Open Data SODA2.

This does not query any candidate or output personal data.
"""
import json
import socket
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_HOST = 'data.cityofnewyork.us'
CONTROL_HOST = 'example.com'
URL = ('https://data.cityofnewyork.us/resource/a9md-ynri.json'
       '?%24select=exam_no&%24limit=1')


def resolve(host):
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(
            host, 443, type=socket.SOCK_STREAM)})
        print('DNS OK:', host, '(%d address(es))' % len(addresses))
        return True
    except OSError as exc:
        print('DNS FAILED:', host, '(reason: %s)' % exc)
        return False


def check():
    official_ok = resolve(API_HOST)
    if not official_ok:
        control_ok = resolve(CONTROL_HOST)
        if not control_ok:
            print('DIAGNOSIS: Environment-wide DNS/network restriction is likely.')
        else:
            print('DIAGNOSIS: NYC Open Data host-specific DNS lookup failure.')
        return 2

    try:
        req = Request(URL, headers={'Accept': 'application/json',
                                    'User-Agent': 'nyc-dcas-cert-tracker-connectivity-test/1.0'})
        with urlopen(req, timeout=20) as response:
            status = response.status
            data = json.load(response)
        if status != 200 or not isinstance(data, list):
            print('API FAILED: unexpected status or JSON shape; status=%s' % status)
            return 3
        print('SODA2 OK: HTTP 200, JSON array, official dataset accessible.')
        return 0
    except HTTPError as exc:
        print('API HTTP ERROR:', exc.code, exc.reason)
        return 3
    except (URLError, OSError, ValueError) as exc:
        print('API TRANSPORT/JSON ERROR:', type(exc).__name__, str(exc))
        print('DIAGNOSIS: DNS resolved but TLS, outbound HTTPS or API response failed.')
        return 3


if __name__ == '__main__':
    sys.exit(check())
