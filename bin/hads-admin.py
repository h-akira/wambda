#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2025-02-28 20:34:16

import sys
import os
import subprocess
import json
import argparse
import importlib
import shutil
import http.server
import socketserver
import urllib.request
from urllib.parse import urlparse
import tempfile


def run_static_server(static_url, static_dir, port=8080):
  """
  静的ファイルを提供するサーバーを実行します。
  
  Args:
      static_url: 静的ファイルのURLパス（例: '/static'）
      static_dir: 静的ファイルのディレクトリパス
      port: サーバーのポート番号（デフォルト: 8080）
  """
  class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
      if path.startswith(static_url):
        return os.path.join(os.getcwd(), path[1:])
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
    print(f"静的ファイルサーバーを起動しました: http://localhost:{port}{static_url}")
    httpd.serve_forever()

def run_proxy_server(static_url, port=8000, sam_port=3000, static_port=8080):
  """
  リバースプロキシサーバーを実行します。
  
  静的ファイルリクエストは static_port に、その他のリクエストは sam_port に転送します。
  
  Args:
      static_url: 静的ファイルのURLパス（例: '/static'）
      port: プロキシサーバーのポート番号（デフォルト: 8000）
      sam_port: SAM Localサーバーのポート番号（デフォルト: 3000）
      static_port: 静的ファイルサーバーのポート番号（デフォルト: 8080）
  """
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
          self.send_header('Content-type', response.headers.get('Content-type', 'text/html'))
          self.end_headers()
          self.wfile.write(response.read())
      except urllib.error.URLError as e:
        self.send_error(500, str(e.reason))
        
  httpd = http.server.HTTPServer(('localhost', port), ReverseProxyHandler)
  print(f"プロキシサーバーを起動しました: http://localhost:{port}")
  print(f"- 静的ファイル ({static_url}*) は port {static_port} に転送")
  print(f"- その他のリクエストは port {sam_port} に転送")
  httpd.serve_forever()

def print_usage():
  print("Usage: hads-admin <function>")
  print("Functions:")
  print("  init: create hads project")
  print("  proxy: run proxy server")
  print("  static: run static server")
  print("  get: test GET request using SAM local invoke")


def init():
  templates = {
    "SSR001": "Server Side Rendering Template",
    "API001": "API Template (For Vue, React, Angular, etc.)",
  }
  parser = argparse.ArgumentParser(description="""\

""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-n", "--name", metavar="name", help="project name", required=True)
  parser.add_argument("-t", "--template", metavar="template", choices = templates.keys(), help="project name")
  # parser.add_argument("-d", "--deploy", action="store_true", help="exec sam deploy")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  if options.template is None:
    print("Available templates:")
    for key, value in templates.items():
      print(f"  {key}: {value}")
    print()
    options.template = input("Please select a template: ").strip()
    if options.template not in templates.keys():
      print(f"Invalid template: {options.template}")
      sys.exit()
  DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib/hads/templates", options.template)
  if not os.path.isdir(DIR):
    print(f"Template directory does not exist: {DIR}")
    sys.exit()
  shutil.copytree(DIR, options.name)



def proxy():
  parser = argparse.ArgumentParser(description="""\
Run proxy server that forwards requests to SAM local API server and static file server.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-p", "--proxy-port", type=int, default=8000, help="proxy server port")
  parser.add_argument("-s", "--sam-port", type=int, default=3000, help="SAM local API server port")
  parser.add_argument("--static-port", type=int, default=8080, help="static file server port")
  parser.add_argument("--static-url", default="/static", help="static files URL prefix")
  parser.add_argument("-d", "--static-dir", default="static", help="static files directory")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  
  # Use the proxy server function directly
  try:
    print(f"Starting proxy server on port {options.proxy_port}")
    print(f"  - Static files ({options.static_url}*) -> port {options.static_port}")
    print(f"  - API requests -> port {options.sam_port}")
    run_proxy_server(
      static_url=options.static_url,
      port=options.proxy_port,
      sam_port=options.sam_port,
      static_port=options.static_port
    )
  except KeyboardInterrupt:
    print("\nProxy server stopped.")
  except Exception as e:
    print(f"Error starting proxy server: {e}")
    sys.exit(1)

def static():
  parser = argparse.ArgumentParser(description="""\
Run static file server for local development.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-p", "--port", type=int, default=8080, help="static file server port")
  parser.add_argument("--static-url", default="/static", help="static files URL prefix")
  parser.add_argument("-d", "--static-dir", default="static", help="static files directory")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  
  # Check if static directory exists
  if not os.path.exists(options.static_dir):
    print(f"Warning: Static directory '{options.static_dir}' does not exist")
    print(f"Creating directory '{options.static_dir}'...")
    os.makedirs(options.static_dir, exist_ok=True)
  
  # Use the static server function directly
  try:
    print(f"Starting static file server on port {options.port}")
    print(f"  - Serving files from: {os.path.abspath(options.static_dir)}")
    print(f"  - URL prefix: {options.static_url}")
    run_static_server(
      static_url=options.static_url,
      static_dir=options.static_dir,
      port=options.port
    )
  except KeyboardInterrupt:
    print("\nStatic file server stopped.")
  except Exception as e:
    print(f"Error starting static file server: {e}")
    sys.exit(1)

def get():
  parser = argparse.ArgumentParser(description="""\
Test GET request to Lambda function locally using SAM local invoke.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-p", "--path", default="/", help="path to test (default: /)")
  parser.add_argument("-m", "--method", default="GET", help="HTTP method (default: GET)")
  parser.add_argument("-e", "--event-file", help="custom event JSON file to use for testing")
  parser.add_argument("-t", "--template", default="template.yaml", help="SAM template file")
  parser.add_argument("-f", "--function-name", default="MainFunction", help="Lambda function name in template")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  
  if options.event_file:
    # Use custom event file
    if not os.path.exists(options.event_file):
      print(f"Error: Event file '{options.event_file}' does not exist")
      sys.exit(1)
    
    print(f"Testing with custom event file: {options.event_file}")
    cmd = ["sam", "local", "invoke", options.function_name, "-e", options.event_file]
    if options.template != "template.yaml":
      cmd.extend(["-t", options.template])
  else:
    # Generate simple event for the specified path and method
    event_data = {
      "path": options.path,
      "requestContext": {
        "httpMethod": options.method
      },
      "body": None,
      "headers": {}
    }
    
    # Create temporary event file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(event_data, f, indent=2)
      temp_event_file = f.name
    
    print(f"Testing {options.method} request to {options.path}")
    cmd = ["sam", "local", "invoke", options.function_name, "-e", temp_event_file]
    if options.template != "template.yaml":
      cmd.extend(["-t", options.template])
  
  try:
    # Check if SAM CLI is available
    result = subprocess.run(["sam", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
      print("Error: SAM CLI is not installed or not available")
      print("Please install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html")
      sys.exit(1)
    
    # Check if template file exists
    if not os.path.exists(options.template):
      print(f"Error: Template file '{options.template}' does not exist")
      sys.exit(1)
    
    # Run the SAM local invoke command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True)
    
    # Clean up temporary event file if created
    if not options.event_file and 'temp_event_file' in locals():
      os.unlink(temp_event_file)
    
    if result.returncode != 0:
      print(f"SAM local invoke failed with return code {result.returncode}")
      sys.exit(1)
      
  except FileNotFoundError:
    print("Error: SAM CLI is not installed or not in PATH")
    print("Please install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html")
    sys.exit(1)
  except Exception as e:
    print(f"Error running SAM local invoke: {e}")
    sys.exit(1)

def main():
  if len(sys.argv) == 1:
    print("You must specify a function.")
    print()
    print_usage()
    sys.exit()
  else:
    if sys.argv[1] == "help":
      print_usage()
      sys.exit()
    elif sys.argv[1] == "init":
      init()
    elif sys.argv[1] == "proxy":
      proxy()
    elif sys.argv[1] == "static":
      static()
    elif sys.argv[1] == "get":
      get()
    else:
      print(f"Unknown function: {sys.argv[1]}")
      print()
      print_usage()
      sys.exit()


if __name__ == '__main__':
  main()
