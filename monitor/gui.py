# -*- coding: utf-8 -*-
from .errors import *
from .make_std_sta import *

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BooleanVar, IntVar
from tkinter.scrolledtext import ScrolledText
from ttkthemes import ThemedTk, ThemedStyle

import sys, subprocess, threading
from os.path import join, dirname, abspath, isfile, splitext
import xml.etree.ElementTree as ET

class MONITOR():
  def __init__(self, inp_path, setting, nogui):
    self.nogui = nogui
    self.dir_path = inp_path
    self.select_theme = 'alt'; self.exepath = ''; self.command = []
    self.root = ThemedTk(self.select_theme)
    if splitext(sys.argv[0])[-1] == '.exe':
      self.root.iconbitmap(True,join(sys.prefix,'icon.ico'))
      self.root_dir = dirname(abspath(sys.argv[0]))
    else:
      self.root_dir = dirname(abspath(__file__))
      self.root.iconbitmap(True,join(self.root_dir,'icon.ico'))
    self.style = ThemedStyle()
    self.header = ''
    if setting is None: setting = join(self.root_dir, 'session.xml')
    self.get_setting(setting)
    self.style.theme_use(self.select_theme)
    self.partition = self.part_select.get()
    self.res2frd_path = join(self.root_dir,'res2frd.exe')

  def get_setting(self,filename):
    if not isfile(filename):
      print(filename+' is not exist...')
      self.part_select = BooleanVar(value=False)
      self.command = ['fistr1.exe']
      self.exepath = join(self.root_dir,'..\FrontISTR-DEV250506')
      return

    tree = ET.parse(filename)
    for child in tree.getroot():
      var_type = child.get('type', 'str')
      if var_type == 'list':
        items = []
        for item in child.iter('inner'): items.append(item.text)
        setattr(self, child.tag, items)
      elif var_type == 'StringVar': setattr(self, child.tag, StringVar(value=child.text))
      elif var_type == 'IntVar': setattr(self, child.tag, IntVar(value=int(child.text)))
      elif var_type == 'BooleanVar': setattr(self, child.tag, BooleanVar(value=bool(child.text=='True')))
      elif var_type == 'str': setattr(self, child.tag, child.text)

  def monitor_main(self):
    self.pvscript_path = join(self.root_dir,'..\open_pvtu.py')
    self.root.title("ジョブモニタ")
    self.root.geometry("600x450+100+100")
    self.quit_flag = False
    self.make_monitor()
    self.make_buttons()
    self.fix_appearance()
    self.style.configure('TNotebook.Tab', font=('Meiryo',10))
    self.root.after(1, self.exebtn.invoke)
    self.root.mainloop()
  
  def make_buttons(self):
    #### Create Buttons ####
    frame_btn = ttk.Frame(self.root)
    frame_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=0)

    self.exebtn  = ttk.Button(frame_btn, text="解析実行",command=self.start_frontistr)
    self.cancel  = ttk.Button(frame_btn, text="解析実行を中断",state='disable',command=self.kill_process)
    backbtn = ttk.Button(frame_btn, text="エディタに戻る",command=self.back2editor,state='disable')
    openbtn = ttk.Button(frame_btn, text="モデルを開く",command=self.open_directory)
    self.quitbtn = ttk.Button(frame_btn, text="閉じる",command=self.quit_session)
    resbtn  = ttk.Button(frame_btn, text="結果を開く",command=self.start_paraview)

    self.exebtn.pack(fill = "x", padx=(5,2.5), side = "left", pady=10)
    self.cancel.pack(fill = "x", padx=2.5, side = "left", pady=10)
    resbtn.pack(fill = "x", padx=2.5, side = "left", pady=10)
    self.quitbtn.pack(fill = "x", padx=(2.5,5), side = "right", pady=10)
    backbtn.pack(fill = "x", padx=2.5, side = "right", pady=10)
    openbtn.pack(fill = "x", padx=2.5, side = "right", pady=10)
    self.root.protocol("WM_DELETE_WINDOW", self.quit_session)

  def make_monitor(self):
    if self.select_theme == 'black': bcolor = 'black'; fcolor = 'white'
    else:                            bcolor = 'white'; fcolor = 'black'

    #### Create Monitor ####
    frame_mnt = ttk.Frame(self.root)
    frame_mnt.pack(side=tk.TOP, fill='both', pady=0, expand=True)

    status_label = ttk.Label(frame_mnt,text='ジョブの状況')
    status_label.pack(anchor='w', padx=10)
    self.status = ScrolledText(frame_mnt,wrap='word',height=5,bg=bcolor,fg=fcolor,insertbackground=fcolor)
    self.status.pack(fill="x", padx=10)
    self.status.insert(tk.END,'モデルは正常に変換されました\n')
    self.status.see(tk.END)

    self.notebook = ttk.Notebook(frame_mnt)
    ### Create monitor Tab ###
    self.tab1 = ttk.Frame(self.notebook)
    self.tab2 = ttk.Frame(self.notebook)
    self.notebook.add(self.tab1, text='ジョブ状況')
    self.notebook.add(self.tab2, text='FrontISTRの出力')

    self.monitor = ScrolledText(self.tab2,wrap='word',height=10,bg=bcolor,fg=fcolor,insertbackground=fcolor)
    self.monitor.pack(fill='both', padx=10, expand=True)

    self.std_sta = ScrolledText(self.tab1,wrap='word',height=10,font=('Consolas',10),bg=bcolor,fg=fcolor,insertbackground=fcolor)
    self.std_sta.pack(fill='both', padx=10, expand=True)
    for color in ["red","blue", "limegreen"]:
      self.std_sta.tag_configure(color, foreground=color)

    self.notebook.pack(fill='both', expand=True)

  def start_frontistr(self):
    self.exebtn.configure(state='disabled'); self.cancel.configure(state='normal')
    self.command = [join(self.exepath, c) if '.exe' in c else c for c in self.command]
    threading.Thread(target=self.run_process, daemon=True).start()
    # self.wait_action()

  def run_partition(self):
    if not self.partition: return True
    log = ''
    part_proc = subprocess.Popen(join(self.exepath,'hecmw_part1.exe'), 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW)
    for line in part_proc.stderr:
      log += line
      self.monitor.insert(tk.END, line); self.monitor.see(tk.END)
      self.root.update_idletasks()
    part_proc.stdout.close(); part_proc.wait()
    if part_proc.returncode == 0: self.status.insert(tk.END,'領域分割が完了しました\n'); return True
    else:
      self.status.insert(tk.END,'領域分割中にエラーが発生しました\n解析は実行されませんでした\n'); return False

  def run_process(self, test_exe=False):
    orig = os.environ.get('PATH', '').split(';')
    paraview_paths = [p for p in orig if 'paraview' in p.lower()]
    if paraview_paths == []: paraview_paths = self.get_pv_path()
    os.environ['PATH'] = ';'.join(paraview_paths)

    result = self.run_partition()
    if not result:
      if self.nogui: print('領域分割中にエラーが発生しました．error.logを確認してください．'); os._exit(0)
      self.status.see(tk.END); self.exebtn.configure(state='normal')
      self.cancel.configure(state='disabled'); return

    self.status.insert(tk.END,'FrontISTRを実行します...\n'); self.status.see(tk.END)
    if self.nogui: print('FrontISTRを実行します...\n 実行状況は.cvgまたは.staファイルで確認できます．')
    global process
    
    try:
      process = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,text=True,stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW)
      self.process_pid = process.pid
    except Exception as e:
      self.status.insert(tk.END,f"{e}\n")
      self.exebtn.configure(state='normal'); self.cancel.configure(state='disabled')
      return
    
    count = 0; completed = False
    sta_init(self.std_sta,test_exe)
    log = open(self.dir_path+'.cvg', 'w+')
    log.write('run command: '+' '.join(self.command)+'\n')
    for sline in process.stdout:
      if 'Please check contact surface definition !' in sline:
        self.check_contactdup_line(sline,log); continue
      if count > 1000: self.monitor.delete(1.0, self.monitor.index('1.0+1lines')) 
      else: count += 1
      if 'FrontISTR Completed !!' in sline: completed = True
      self.monitor.insert(tk.END, sline); self.monitor.see(tk.END)
      self.std_sta.see(tk.END); control_std_sta(sline,self.std_sta)
      self.root.update_idletasks()
      log.write(sline); log.flush()

    process.stdout.close()
    process.wait()
    log.close()

    if self.nogui and not test_exe: 
      print('解析が終了しました．実行結果を確認してください．'); os._exit(0)
    if test_exe: return
    
    root=tk.Tk(); root.withdraw()
    if self.quit_flag: return
    if completed: msg = '解析ジョブは正常に実行されました'; messagebox.showinfo('解析結果',msg)
    elif process.returncode == 1: msg = '解析が中断，あるいは実行されませんでした'
    else: msg = '解析中にエラーが発生しました'; messagebox.showerror('解析結果',msg)
    self.status.insert(tk.END,msg+'\n')
    self.exebtn.configure(state='normal'); self.cancel.configure(state='disabled')
    self.status.see(tk.END)

    self.status.insert(tk.END,'結果を変換します．\n'); self.start_res2frd()
    self.status.see(tk.END)

  def check_contactdup_line(self,sline,log):
    process.stdin.write('y\n'); process.stdin.flush()
    self.monitor.insert(tk.END, sline, 'error'); self.monitor.see(tk.END)
    self.root.update_idletasks()
    log.write(sline); log.flush()

  def kill_process(self):
    if 'process' in globals(): process.terminate()
    self.status.insert(tk.END,'terminate command sent...\n')

  def quit_session(self):
    self.quit_flag = True
    threading.Thread(target=self.kill_process, daemon=True).start()
    self.root.quit(); sys.exit()

  def open_directory(self):
    def open_exp(): subprocess.Popen([r'C:\Windows\explorer.exe', self.dir_path], shell=True)
    threading.Thread(target=open_exp).start()

  def start_paraview(self):
    def parav_exe(): subprocess.Popen(['paraview.exe', '--script='+self.pvscript_path], shell=True)
    threading.Thread(target=parav_exe).start()
    self.status.insert(tk.END,'Paraviewを起動します...\n'); self.status.see(tk.END)

  def nogui_mode(self):
    for attr_name in ['root', 'status', 'exebtn', 'cancel', 'monitor', 'std_sta', 'progress_bar']:
        setattr(self, attr_name, noGUI_dummy())
    self.command = [join(self.exepath, c) if '.exe' in c else c for c in self.command]

  def signal_handler(self, sig, frame):
    print("Ctrl+C (SIGINT) を受信しました。プロセスを終了します...")
    self.kill_process()
    sys.exit(0)

  def back2editor(self):
    self.quit_flag = True; self.back_to_editor = True
    self.kill_process()
    self.root.quit()

  def start_res2frd(self):
    def exe_res2frd():
      try:
        proc = subprocess.run([self.res2frd_path,self.dir_path,'-heading',self.header],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True)
        if proc.returncode == 0: self.status.insert(tk.END,f"変換が完了しました．\n")
        else: self.status.insert(tk.END,f"変換に失敗しました．\n")
      except Exception as e:
        self.status.insert(tk.END,f"変換に失敗しました，res2frd.exeの場所などを確認して下さい：{e}\n")
    threading.Thread(target=exe_res2frd).start()

  def fix_appearance(self):
    self.style.theme_use(self.select_theme)
    self.style.configure('TButton', font=('Meiryo',9),anchor='n')
    self.style.configure('TLabel', font=('Meiryo',10))
    self.style.configure('TLabelframe.Label', font=('Meiryo',8))
    self.style.configure('TNotebook.Tab', font=('Meiryo',12))
    self.style.configure("Horizontal.TProgressbar", troughcolor="#dcdad5", background="#93c47d")

  def get_pv_path(self):
    from pathlib import Path
    paths = []
    for ppath in Path(r"C:\Program Files").iterdir():
      if 'ParaView' in ppath.name:
        paths.append(join(ppath,'bin'))
    paths.reverse()
    return paths

class noGUI_dummy:
  def update_idletasks(self): pass
  def insert(self, index, text): pass
  def see(self, index): pass
  def delete(self, start, end=None): pass
  def index(self, text): return ""
  def configure(self, state): pass