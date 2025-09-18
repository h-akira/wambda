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
import importlib.util
import shutil
import http.server
import socketserver
import urllib.request
from urllib.parse import urlparse
import tempfile
import boto3
from datetime import datetime, timedelta


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
    def log_message(self, format, *args):
      """HTTPサーバーのログメッセージをカスタマイズ"""
      print(f"[PROXY] {format % args}")
    
    def _handle_request(self):
      """すべてのHTTPメソッドを処理する汎用メソッド"""
      parsed_url = urlparse(self.path)
      if parsed_url.path.startswith(static_url):
        target_url = f'http://localhost:{static_port}{self.path}'
      else:
        target_url = f'http://localhost:{sam_port}{self.path}'
      
      print(f"[PROXY] {self.command} {self.path} -> {target_url}")
      
      # リクエストヘッダーをログ出力
      print(f"[PROXY] Request headers:")
      for header_name, header_value in self.headers.items():
        print(f"[PROXY]   {header_name}: {header_value}")
      
      try:
        # リクエストボディを読み取り
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length) if content_length > 0 else None
        
        if request_body:
          print(f"[PROXY] Request body: {request_body.decode('utf-8', errors='ignore')[:200]}...")
        
        # リクエストを作成
        req = urllib.request.Request(target_url, data=request_body, method=self.command)
        
        # ヘッダーをコピー（Hostヘッダーは除く）
        copied_headers = []
        for header_name, header_value in self.headers.items():
          if header_name.lower() not in ['host', 'connection']:
            req.add_header(header_name, header_value)
            copied_headers.append(f"{header_name}: {header_value}")
        
        print(f"[PROXY] Forwarded headers: {len(copied_headers)} headers")
        
        # リダイレクト無効化のカスタムErrorHandlerを作成
        class NoRedirectErrorHandler(urllib.request.HTTPErrorProcessor):
          def http_response(self, request, response):
            # 3xxレスポンスでもエラーとして扱わない
            return response
          
          def https_response(self, request, response):
            return self.http_response(request, response)
        
        # カスタムopenerを作成（リダイレクト追跡なし）
        opener = urllib.request.build_opener(NoRedirectErrorHandler)
        opener.add_handler(urllib.request.HTTPHandler())
        opener.add_handler(urllib.request.HTTPSHandler())
        
        # リクエストを送信
        try:
          response = opener.open(req)
        except urllib.error.HTTPError as e:
          # HTTPErrorも通常のレスポンスとして扱う（3xxリダイレクトのため）
          response = e
        
        print(f"[PROXY] Response status: {response.status}")
        self.send_response(response.status)
        
        # レスポンスヘッダーをログ出力
        print(f"[PROXY] Response headers from SAM Local:")
        for header_name, header_value in response.headers.items():
          print(f"[PROXY]   {header_name}: {header_value}")
        
        # レスポンスヘッダーをコピー（Set-Cookieヘッダーを特別処理）
        set_cookie_headers = []
        forwarded_headers = []
        for header_name, header_value in response.headers.items():
          if header_name.lower() not in ['connection', 'transfer-encoding']:
            if header_name.lower() == 'set-cookie':
              set_cookie_headers.append(header_value)
            else:
              self.send_header(header_name, header_value)
              forwarded_headers.append(f"{header_name}: {header_value}")
        
        print(f"[PROXY] Forwarded {len(forwarded_headers)} response headers")
        
        # 複数のSet-Cookieヘッダーを個別に送信
        if set_cookie_headers:
          print(f"[PROXY] Found {len(set_cookie_headers)} Set-Cookie headers:")
          for i, cookie_header in enumerate(set_cookie_headers):
            print(f"[PROXY]   Cookie {i+1}: {cookie_header}")
            self.send_header('Set-Cookie', cookie_header)
        else:
          print(f"[PROXY] No Set-Cookie headers found")
        
        self.end_headers()
        
        response_body = response.read()
        print(f"[PROXY] Response body length: {len(response_body)} bytes")
        self.wfile.write(response_body)
          
      except urllib.error.URLError as e:
        self.send_error(500, str(e.reason))
      except Exception as e:
        self.send_error(500, f"Proxy error: {str(e)}")
    
    def do_GET(self):
      self._handle_request()
    
    def do_POST(self):
      self._handle_request()
    
    def do_PUT(self):
      self._handle_request()
    
    def do_DELETE(self):
      self._handle_request()
    
    def do_PATCH(self):
      self._handle_request()
    
    def do_HEAD(self):
      self._handle_request()
    
    def do_OPTIONS(self):
      self._handle_request()
        
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
  print("  log: retrieve recent Lambda function logs from CloudWatch")


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


def log():
  parser = argparse.ArgumentParser(description="""\
Retrieve recent Lambda function logs from CloudWatch.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-f", "--function-name", help="Lambda function name (required)")
  parser.add_argument("-l", "--limit", type=int, default=50, help="maximum number of log events to retrieve (default: 50)")
  parser.add_argument("--hours", type=int, default=1, help="number of hours to look back for logs (default: 1)")
  parser.add_argument("-r", "--region", default="ap-northeast-1", help="AWS region (default: ap-northeast-1)")
  parser.add_argument("-p", "--profile", help="AWS profile name to use")
  parser.add_argument("--start-time", help="start time in ISO format (e.g., 2025-01-01T00:00:00)")
  parser.add_argument("--end-time", help="end time in ISO format (e.g., 2025-01-01T23:59:59)")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  
  if not options.function_name:
    print("Error: Lambda function name is required. Use -f/--function-name to specify it.")
    sys.exit(1)
  
  try:
    # Initialize CloudWatch Logs client
    session = boto3.Session(profile_name=options.profile) if options.profile else boto3.Session()
    logs_client = session.client('logs', region_name=options.region)
    
    # Construct log group name (Lambda functions use /aws/lambda/<function-name>)
    log_group_name = f"/aws/lambda/{options.function_name}"
    
    # Calculate time range
    if options.start_time and options.end_time:
      start_time = datetime.fromisoformat(options.start_time)
      end_time = datetime.fromisoformat(options.end_time)
    else:
      end_time = datetime.now()
      start_time = end_time - timedelta(hours=options.hours)
    
    # Convert to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    print(f"Retrieving logs for Lambda function: {options.function_name}")
    print(f"Log group: {log_group_name}")
    print(f"Time range: {start_time.isoformat()} to {end_time.isoformat()}")
    print(f"Region: {options.region}")
    print(f"Limit: {options.limit} events")
    print("-" * 80)
    
    # Get log events
    try:
      response = logs_client.filter_log_events(
        logGroupName=log_group_name,
        startTime=start_time_ms,
        endTime=end_time_ms,
        limit=options.limit
      )
      
      events = response.get('events', [])
      
      if not events:
        print("No log events found in the specified time range.")
        print("\nTroubleshooting:")
        print(f"1. Check if the Lambda function '{options.function_name}' exists")
        print(f"2. Verify the log group '{log_group_name}' exists")
        print(f"3. Ensure your AWS credentials have CloudWatch Logs read permissions")
        print(f"4. Try extending the time range with --hours option")
        return
      
      print(f"Found {len(events)} log events:\n")
      
      for event in events:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        message = event['message'].rstrip('\n')
        
        print(f"[{timestamp.isoformat()}] {message}")
      
      print("-" * 80)
      print(f"Retrieved {len(events)} log events from {log_group_name}")
      
      # Check if there might be more logs
      if len(events) == options.limit:
        print(f"Note: Result limited to {options.limit} events. There might be more logs available.")
        print("Use --limit option to retrieve more events.")
        
    except logs_client.exceptions.ResourceNotFoundException:
      print(f"Error: Log group '{log_group_name}' not found.")
      print(f"Make sure the Lambda function '{options.function_name}' exists and has been invoked at least once.")
    except Exception as e:
      print(f"Error retrieving logs: {e}")
      sys.exit(1)
      
  except Exception as e:
    print(f"Error initializing AWS client: {e}")
    print("Make sure your AWS credentials are configured correctly.")
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
    elif sys.argv[1] == "log":
      log()
    else:
      print(f"Unknown function: {sys.argv[1]}")
      print()
      print_usage()
      sys.exit()


if __name__ == '__main__':
  main()
