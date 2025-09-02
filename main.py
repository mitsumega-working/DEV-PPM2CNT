# -*- coding: utf-8 -*-
import sys
from os import chdir, getcwd
from os.path import dirname, abspath, join, splitext

class PrePoSTR:
  def __init__(self,inp_path,dir_path,exepath):
    self.inp_path = inp_path
    self.dir_path = dir_path
    self.exepath = exepath
    if splitext(sys.argv[0])[-1] == '.exe': self.exe_type = 'exe_file'
    else: self.exe_type = 'python'
  
  def python_exe(self):
    from inp_converter.main import CONVERTER
    from editor.gui import EDITOR
    from monitor.gui import MONITOR

    self.root_dir = dirname(abspath(__file__))
    init_dir = getcwd()
    self.setting = join(self.root_dir,'session.xml')
    ## inp convert
    convert = CONVERTER(self.inp_path,self.dir_path)
    convert.main()
    if convert.dflag: sys.exit(1)
    header = convert.heading
    del convert

    chdir(init_dir)
    ## model editor
    editor = EDITOR(self.inp_path,self.setting)
    editor.editor(header,self.exepath)
    editor.root.destroy()
    del editor

    ## execution and monitor
    chdir(self.inp_path.rstrip('.inp'))

    monitor = MONITOR(self.inp_path.rstrip('.inp'),self.setting,None)
    monitor.res2frd_path = join(join(self.root_dir,'exes'),'res2frd.exe')
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
    del monitor

  def file_exe(self):
    import subprocess

    self.root_dir = dirname(abspath(sys.argv[0]))
    self.setting = join(self.root_dir,'session.xml')
    exe_dir = join(self.root_dir,'tools')

    convert = subprocess.run([join(exe_dir,'inp_converter.exe'), self.inp_path],stdout=subprocess.PIPE, text=True)
    if convert.returncode != 0: sys.exit(1)
    header = convert.stdout.splitlines()[-1].lstrip('header:').rstrip('\n')
    del convert

    editor = subprocess.run([join(exe_dir,'editor.exe'), self.inp_path,self.exepath,'-setting', self.setting,'-header',header])
    if editor.returncode != 0: sys.exit(2)
    del editor

    monitor = subprocess.run([join(exe_dir,'monitor.exe'), self.inp_path.rstrip('.inp'), '-setting', self.setting])
    if monitor.returncode != 0: sys.exit(3)
    del monitor

  def main(self):
    if self.exe_type == 'python': self.python_exe()
    else: self.file_exe()
