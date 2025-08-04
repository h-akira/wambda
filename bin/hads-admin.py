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


def print_usage():
  print("Usage: hads-admin <function>")
  print("Functions:")
  print("  init: create hads project")
  print("  proxy: run proxy server")
  print("  static: run static server")


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
This is a command line tool for managing hads project.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-n", "--name", metavar="name", help="project name", required=True)
  parser.add_argument("-d", "--deploy", action="store_true", help="exec sam deploy")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  return None

def static():
  parser = argparse.ArgumentParser(description="""\
This is a command line tool for managing hads project.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-n", "--name", metavar="name", help="project name", required=True)
  parser.add_argument("-d", "--deploy", action="store_true", help="exec sam deploy")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()
  return None

def get():
  parser = argparse.ArgumentParser(description="""\
This is a command line tool for managing hads project.
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-n", "--name", metavar="name", help="project name", required=True)
  parser.add_argument("-d", "--deploy", action="store_true", help="exec sam deploy")
  parser.add_argument("function", metavar="function", help="function to run")
  options = parser.parse_args()

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
    else:
      print(f"Unknown function: {sys.argv[1]}")
      print()
      print_usage()
      sys.exit()


if __name__ == '__main__':
  main()
