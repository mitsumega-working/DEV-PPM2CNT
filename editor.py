# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from editor.gui import EDITOR
from os.path import abspath

#╔══════════════════════════════════╗#
#║ Editor for FrontISTR input files ║#
#║   Developed by Ando (Structia)   ║#
#╚══════════════════════════════════╝#

ps = ArgumentParser()
ps.add_argument('input', type=str, help="INPファイルのパス")
ps.add_argument('exepath', type=str, metavar="/path/to/FrontISTR")
ps.add_argument('-setting', type=str, metavar="/path/to/setting.xml")
ps.add_argument('-header', type=str, metavar="/path/to/FrontISTR")
args = ps.parse_args()

inp_path = abspath(args.input)
if not inp_path.endswith('.inp'): inp_path += '.inp'

editor = EDITOR(inp_path,args.setting)
editor.editor(args.header,args.exepath)