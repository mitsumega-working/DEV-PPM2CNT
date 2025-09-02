# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from monitor.gui import MONITOR
from os.path import dirname, abspath, join
from os import chdir

#╔══════════════════════════════════╗#
#║      Monitor for FrontISTR       ║#
#║   Developed by Ando (Structia)   ║#
#╚══════════════════════════════════╝#

ps = ArgumentParser()
ps.add_argument('input', type=str, help="hecmw_ctrl.datのフォルダパス")
ps.add_argument('-setting', type=str, metavar="/path/to/setting.xml",
                help="設定ファイルのパス(指定しない場合はdefault.xmlを使用)")
ps.add_argument('-nogui',action='store_true')
args = ps.parse_args()

inp_path = abspath(args.input)
if args.setting: setting = abspath(args.setting)
else: setting = abspath('session.xml')
chdir(inp_path)

monitor = MONITOR(inp_path,setting,args.nogui)
if monitor.nogui:
  monitor.nogui_mode()
  monitor.done = False
  import signal, time, threading
  threading.Thread(target=monitor.run_process, daemon=True).start()
  signal.signal(signal.SIGINT, monitor.signal_handler)
  while True:
    time.sleep(1)
    if monitor.done: break
else: monitor.monitor_main()