# -*- coding: utf-8 -*-
import sys, gc
from argparse import ArgumentParser
from main import PrePoSTR
from os.path import dirname, abspath, join

#╔══════════════════════════════════╗#
#║ Converter .inp file to FrontISTR ║#
#║            for PrePoMax          ║#
#║      Version:1.0  (2025-07-11)   ║#
#║   Developed by Ando (Structia)   ║#
#╚══════════════════════════════════╝#

ps = ArgumentParser()
ps.add_argument('input', type=str, help="INPファイルのパス")
ps.add_argument('-nogui', nargs='?', type=str, const=True, metavar="/path/to/.s2f",
                help="設定ファイルのパス(指定しない場合はsession.rs2fを使用)")
args = ps.parse_args()

inp_path = abspath(args.input); dir_path = dirname(inp_path)
exepath = join(abspath(dirname(__file__)),r'FrontISTR-DEV250506')
if not inp_path.endswith('.inp'): inp_path += '.inp'
b2e = False

while True:
  convert = PrePoSTR(inp_path,dir_path,exepath,args.nogui,b2e)
  convert.main()
  convert.root.destroy()
  if convert.dflag: sys.exit()
  convert.run_exe()
  convert.root.destroy()
  b2e = convert.back_to_editor
  del convert
  gc.collect()