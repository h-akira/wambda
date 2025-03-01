#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2025-02-28 22:38:55

import os
import http.server
import socketserver
import urllib.request
from urllib.parse import urlparse

def run_static_server(static_url, static_dir, port=8080):
  class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
      if path.startswith('/static'):
        print("path:", path)
        return os.path.join(os.getcwd(),  path[1:])
      else:
        return None
    def do_GET(self):
      path = self.translate_path(self.path)
      if path:
        if os.path.exists(path) and os.path.isfile(path):
          super().do_GET()
        else:
          self.send_error(404, "File Not Found")
      else:
        self.send_error(403, "Forbidden")
  with socketserver.TCPServer(("localhost", port), MyHTTPRequestHandler) as httpd:
    print(f"serving at port {port}")
    httpd.serve_forever()

def run_proxy_server(static_url, port=8000, sam_port=3000, static_port=8080):
  class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
      parsed_url = urlparse(self.path)
      if parsed_url.path.startswith(static_url):
        target_url = f'http://localhost:{static_port}{self.path}'
      else:
        target_url = f'http://localhost:{sam_port}{self.path}'
      try:
        with urllib.request.urlopen(target_url) as response:
          self.send_response(response.status)
          self.send_header('Content-type', response.headers['Content-type'])
          self.end_headers()
          self.wfile.write(response.read())
      except urllib.error.URLError as e:
        self.send_error(500, str(e.reason))
  httpd = http.server.HTTPServer(('localhost', 8000), ReverseProxyHandler)
  print(f"serving at port {port}")
  httpd.serve_forever()
