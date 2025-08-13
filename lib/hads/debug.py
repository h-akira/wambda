#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import argparse


def create_test_event(path="/", method="GET", body=None, headers=None, query_params=None):
  """
  テスト用のLambdaイベントオブジェクトを生成
  
  Args:
    path: リクエストパス
    method: HTTPメソッド
    body: リクエストボディ
    headers: リクエストヘッダー
    query_params: クエリパラメータ
  
  Returns:
    dict: Lambdaイベント形式の辞書
  """
  if headers is None:
    headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'hads-debug/1.0'
    }
  
  event = {
    "path": path,
    "requestContext": {
      "httpMethod": method
    },
    "body": body,
    "headers": headers,
    "queryStringParameters": query_params,
    "pathParameters": None
  }
  
  return event


def run_lambda_handler(lambda_handler_func, path="/", method="GET", body=None, headers=None, query_params=None, verbose=True):
  """
  lambda_handlerを直接実行してテスト
  
  Args:
    lambda_handler_func: lambda_handler関数
    path: テスト対象のパス
    method: HTTPメソッド
    body: リクエストボディ
    headers: リクエストヘッダー
    query_params: クエリパラメータ
    verbose: 詳細ログを出力するか
  
  Returns:
    dict: レスポンス辞書
  """
  # テストイベントを生成
  event = create_test_event(path, method, body, headers, query_params)
  
  if verbose:
    print(f"=== HADS Debug Mode ===")
    print(f"Testing {method} {path}")
    if body:
      print(f"Body: {body}")
    if query_params:
      print(f"Query params: {query_params}")
    print(f"Event: {json.dumps(event, indent=2)}")
    print("-" * 50)
  
  try:
    # lambda_handlerを実行
    response = lambda_handler_func(event, None)
    
    if verbose:
      print("Response:")
      print(json.dumps(response, indent=2, ensure_ascii=False))
      print("-" * 50)
      print(f"Status Code: {response.get('statusCode', 'N/A')}")
      
      if 'headers' in response:
        print("Headers:")
        for key, value in response['headers'].items():
          print(f"  {key}: {value}")
      
      if 'multiValueHeaders' in response:
        print("Multi-Value Headers:")
        for key, values in response['multiValueHeaders'].items():
          for value in values:
            print(f"  {key}: {value}")
    
    return response
    
  except Exception as e:
    if verbose:
      print(f"Error executing lambda_handler: {e}")
      import traceback
      traceback.print_exc()
    raise


def parse_debug_args():
  """
  デバッグ用のコマンドライン引数を解析
  
  Returns:
    argparse.Namespace: 解析された引数
  """
  parser = argparse.ArgumentParser(
    description="HADS Lambda Function Debug Tool",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  
  parser.add_argument("-p", "--path", default="/", 
                     help="path to test (default: /)")
  parser.add_argument("-m", "--method", default="GET", 
                     help="HTTP method (default: GET)")
  parser.add_argument("-b", "--body", 
                     help="request body for POST/PUT requests")
  parser.add_argument("-H", "--header", action="append", 
                     help="add header (format: 'Key: Value')")
  parser.add_argument("-q", "--query", 
                     help="query parameters (format: 'key1=value1&key2=value2')")
  parser.add_argument("--json", action="store_true", 
                     help="parse body as JSON")
  parser.add_argument("-v", "--verbose", action="store_true", default=True,
                     help="verbose output")
  parser.add_argument("--quiet", action="store_true",
                     help="quiet mode (minimal output)")
  
  return parser.parse_args()


def prepare_debug_environment():
  """
  デバッグ実行環境を準備
  - 必要なパスの追加
  - 環境変数の設定など
  """
  # 現在のディレクトリをPythonパスに追加
  current_dir = os.path.dirname(os.path.abspath(__file__))
  if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
  
  # Lambda実行ディレクトリをPythonパスに追加
  lambda_dir = os.getcwd()
  if lambda_dir not in sys.path:
    sys.path.insert(0, lambda_dir)
  
  # AWS_SAM_LOCALフラグを設定（ローカル環境であることを示す）
  os.environ['AWS_SAM_LOCAL'] = 'true'


def main_debug_handler(lambda_handler_func):
  """
  デバッグ用のメインハンドラー
  lambda_function.pyの if __name__ == "__main__": ブロックから呼び出される
  
  Args:
    lambda_handler_func: lambda_handler関数
  """
  # 環境準備
  prepare_debug_environment()
  
  # 引数解析
  args = parse_debug_args()
  
  # クエリパラメータの解析
  query_params = None
  if args.query:
    query_params = {}
    for param in args.query.split('&'):
      if '=' in param:
        key, value = param.split('=', 1)
        query_params[key] = value
  
  # ヘッダーの解析
  headers = {
    'Content-Type': 'application/json' if args.json else 'text/html',
    'User-Agent': 'hads-debug/1.0'
  }
  if args.header:
    for header in args.header:
      if ':' in header:
        key, value = header.split(':', 1)
        headers[key.strip()] = value.strip()
  
  # ボディの処理
  body = args.body
  if body and args.json:
    try:
      # JSONとして解析できるかチェック
      json.loads(body)
    except json.JSONDecodeError:
      print("Warning: --json specified but body is not valid JSON")
  
  # 詳細出力の設定
  verbose = args.verbose and not args.quiet
  
  # lambda_handlerを実行
  try:
    response = run_lambda_handler(
      lambda_handler_func,
      path=args.path,
      method=args.method,
      body=body,
      headers=headers,
      query_params=query_params,
      verbose=verbose
    )
    
    if args.quiet:
      # クワイエットモードではステータスコードのみ出力
      print(response.get('statusCode', 500))
    
    return response
    
  except KeyboardInterrupt:
    print("\nDebug session interrupted by user")
    sys.exit(1)
  except Exception as e:
    print(f"Debug execution failed: {e}")
    sys.exit(1)


if __name__ == "__main__":
  print("This module should be imported and used with main_debug_handler()")
  print("Example usage in lambda_function.py:")
  print("  if __name__ == '__main__':")
  print("    from hads.debug import main_debug_handler")
  print("    main_debug_handler(lambda_handler)")
