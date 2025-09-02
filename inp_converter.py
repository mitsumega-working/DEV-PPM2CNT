# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser
from inp_converter.main import CONVERTER
from os.path import dirname, abspath

#╔══════════════════════════════════╗#
#║ Converter .inp file to FrontISTR ║#
#║   Developed by Ando (Structia)   ║#
#╚══════════════════════════════════╝#

ps = ArgumentParser()
ps.add_argument('input', type=str, help="INPファイルのパス")
args = ps.parse_args()

inp_path = abspath(args.input); dir_path = dirname(inp_path)
if not inp_path.endswith('.inp'): inp_path += '.inp'

convert = CONVERTER(inp_path,dir_path)
convert.main()
if convert.dflag: sys.exit(1)
print('header:'+convert.heading)