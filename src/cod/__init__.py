# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
from .workspace import Workspace

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    parser_build = subparsers.add_parser('build')
    parser_build.add_argument('-p', '--profile', default='dev')
    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('-p', '--profile', default='dev')
    parser_install.add_argument('package', nargs='+')
    parser_package = subparsers.add_parser('package')

    args = parser.parse_args()
    ws = Workspace()

    if args.command == 'build':
        ws.build(args.profile)
    elif args.command == 'install':
        ws.install(args.profile, args.package)
    elif args.command == 'package':
        ws.package()
    else:
        parser.print_help()
