#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2025-02-28 20:34:16

import sys
import os
import subprocess
import json

def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description="""\
This is a command line tool for managing hads project.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-p", "--profile", metavar="profile", help="aws profile, this takes precedence over admin file")
  parser.add_argument("-s", "--static-sync2s3", action="store_true", help="sync static files to s3")
  parser.add_argument("-b", "--build", action="store_true", help="exec sam build")
  parser.add_argument("-d", "--deploy", action="store_true", help="exec sam deploy")
  parser.add_argument("-i", "--init", action="store_true", help="create hads project")
  parser.add_argument(
    "-l", "--local-server-run", metavar="profile", choices=["sam", "static", "proxy"],
    help="aws profile, this takes precedence over admin file"
  )
  parser.add_argument("file", metavar="admin-file", nargs="?", help="input file")
  options = parser.parse_args()
  if options.file is None:
    if options.profile or options.build or options.deploy or options.static_sync2s3 or options.local_server_run:
      print("Error: missing admin file")
      sys.exit()
  else:
    if not os.path.exists(options.file):
      print(f"Error: file '{options.file}' does not exist")
      sys.exit()
  return options

def main():
  options = parse_args()
  if options.file is None:
    pass
  else:
    # adminファイルを読み込む
    with open(options.file) as f:
      admin = json.load(f)
    sys.path.append(os.path.join(os.path.dirname(options.file),"Lambda"))
    CWD = os.path.dirname(options.file)
    from project import settings
    # 環境変数を設定
    env = os.environ.copy()
    if options.profile:
      env["AWS_PROFILE"] = options
    else:
      if admin.get("profile"):
        env["AWS_PROFILE"] = admin["profile"]
    # 各オプションの処理
    if options.local_server_run:
      if options.local_server_run == "sam":
        subprocess.run(["sam", "local", "start-api", "--port", str(admin["local_server"]["port"]["sam"])], env=env, cwd=CWD)
      elif options.local_server_run == "static":
        from hads.local_server import run_static_server 
        run_static_server(
          settings.STATIC_URL, 
          os.path.join(CWD, ,admin["static"]["local"]),
          admin["local_server"]["port"]["static"]
        )
      elif options.local_server_run == "proxy":
        from hads.local_server import run_proxy_server 
        run_proxy_server(
          settings.STATIC_URL,
          admin["local_server"]["port"]["proxy"],
          admin["local_server"]["port"]["sam"],
          admin["local_server"]["port"]["static"]
        )
      sys.exit()
    if options.static_sync2s3:
      if admin.get("static") and admin["static"].get("local") and admin["static"].get("s3"):
        subprocess.run(["aws", "s3", "sync", admin["static"]["local"], admin["static"]["s3"]], env=env, cwd=CWD)
      else:
        print("Error: static.local or static.s3 is not defined")
        sys.exit()
    if options.build:
      subprocess.run(["sam", "build"], env=env, cwd=CWD)
    if options.deploy:
      subprocess.run(["sam", "deploy"], env=env, cwd=CWD)

if __name__ == '__main__':
  main()
