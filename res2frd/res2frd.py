# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser
from main import res2frd
from os.path import dirname, abspath

#╔═════════════════════════════════╗#
#║ Converter res files to frd file ║#
#║   Developed by Ando (Structia)  ║#
#╚═════════════════════════════════╝#

ps = ArgumentParser()
ps.add_argument('input', type=str, help="INPファイルのパス")
ps.add_argument('-heading', nargs='?', type=str, const=True)
args = ps.parse_args()

inp_path = abspath(args.input); dir_path = dirname(inp_path)
if not inp_path.endswith('.inp'): inp_path += '.inp'

convert = res2frd(inp_path,args.heading)
convert.get_mesh()
convert.make_frd()
