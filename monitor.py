# -*- coding: utf-8 -*-
from editor import EDITOR

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import sys, subprocess, threading, traceback
from os.path import join, splitext, basename, realpath
from functions.make_std_sta import *
from functions.errors import write_err_damp

class MONITOR(EDITOR):
  def __init__(self):
    pass
  
  def monitor_main(self):
    EDITOR.__init__(self,'',self.exepath)
    self.pvscript_path = join(realpath(self.root_dir),'open_pvtu.py')
    self.root.title("ジョブモニタ")
    self.root.geometry("600x450+100+100")
    self.quit_flag = False; self.back_to_editor = False
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
    backbtn = ttk.Button(frame_btn, text="エディタに戻る",command=self.back2editor)
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
      write_err_damp(join(self.dir_path,splitext(basename(self.inp_path))[0]), self.dt_now, log, self.inp_error_log)
      self.status.insert(tk.END,'領域分割中にエラーが発生しました\n解析は実行されませんでした\n'); return False

  def run_process(self, test_exe=False):
    orig = os.environ['PATH'].split(';')
    paraview_paths = [p for p in orig if 'paraview' in p.lower()]
    os.environ['PATH'] = ''
    os.environ['PATH'] = ';'.join(paraview_paths)
    os.environ['PATH'] += f';{self.exepath}'

    result = self.run_partition()
    if not result:
      if self.nogui: print('領域分割中にエラーが発生しました．error.logを確認してください．'); os._exit(0)
      self.status.see(tk.END); self.exebtn.configure(state='normal')
      self.cancel.configure(state='disabled'); return

    self.status.insert(tk.END,'FrontISTRを実行します...\n'); self.status.see(tk.END)
    if self.nogui: print('FrontISTRを実行します...\n 実行状況はrun.logまたは.staファイルで確認できます．')
    global process
    try:
      process = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True,
                creationflags=subprocess.CREATE_NO_WINDOW)
      self.process_pid = process.pid
    except Exception as e:
      self.status.insert(tk.END,f"{e}\n")
      self.exebtn.configure(state='normal'); self.cancel.configure(state='disabled')
      return
    
    count = 0
    sta_init(self.std_sta,test_exe)
    log = open(self.inp_path.replace('.inp','.cvg'), 'w+')
    log.write('run command: '+' '.join(self.command)+'\n')
    for sline in process.stdout:
      if count > 1000: self.monitor.delete(1.0, self.monitor.index('1.0+1lines')) 
      else: count += 1
      self.monitor.insert(tk.END, sline); self.monitor.see(tk.END)
      self.std_sta.see(tk.END); control_std_sta(sline,self.std_sta)
      self.root.update_idletasks()
      log.write(sline); log.flush()

    for line in process.stderr:
      log.write(line); log.flush()
      self.monitor.insert(tk.END, line); self.monitor.see(tk.END)
      self.root.update_idletasks()
    process.stdout.close()
    process.stderr.close()
    process.wait()
    log.close()

    self.convert_result()
    if self.nogui and not test_exe: print('解析が終了しました．実行結果を確認してください．'); os._exit(0)
    if test_exe: return
    
    root=tk.Tk(); root.withdraw()
    if self.quit_flag: return

    if 'FrontISTR Completed !!' in sline:
      msg = '解析ジョブは正常に実行されました'
      messagebox.showinfo('解析結果','解析ジョブは正常に実行されました')
    elif process.returncode == 1: msg = '解析が中断，あるいは実行されませんでした'
    else:
      msg = '解析中にエラーが発生しました'
      messagebox.showerror('解析結果','解析中にエラーが発生しました')
    self.status.insert(tk.END,msg+'\n')
    self.exebtn.configure(state='normal'); self.cancel.configure(state='disabled')
    self.status.see(tk.END)

  def kill_process(self):
    if 'process' in globals(): process.terminate()
    self.status.insert(tk.END,'terminate command sent...\n')

  def quit_session(self):
    self.quit_flag = True
    threading.Thread(target=self.kill_process, daemon=True).start()
    self.root.quit(); sys.exit()

  def open_directory(self):
    def open_exp(): subprocess.Popen(['explorer', self.out_dir], shell=True)
    threading.Thread(target=open_exp).start()

  def start_paraview(self):
    def parav_exe(): subprocess.Popen(['paraview.exe', '--script='+self.pvscript_path], shell=True)
    threading.Thread(target=parav_exe).start()
    self.status.insert(tk.END,'Paraviewを起動します...\n'); self.status.see(tk.END)

  def nogui_mode(self):
    for attr_name in ['root', 'status', 'exebtn', 'cancel', 'monitor', 'std_sta', 'progress_bar']:
        setattr(self, attr_name, noGUI_dummy())
    self.get_exe_command()
    self.command = [join(self.exepath, c) if '.exe' in c else c for c in self.command]

  def signal_handler(self, sig, frame):
    print("Ctrl+C (SIGINT) を受信しました。プロセスを終了します...")
    self.kill_process()
    sys.exit(0)

  def back2editor(self):
    self.quit_flag = True; self.back_to_editor = True
    self.kill_process()
    self.root.quit()

  def convert_result(self):
    self.status.insert(tk.END,'結果を変換します...\n'); self.status.see(tk.END)
    if self.nogui: print('結果を変換します...')
    try: self.make_frd(); out_text = '変換が完了しました'
    except Exception as e:
      out_path = os.path.join(self.dir_path,splitext(basename(self.inp_path))[0])
      write_err_damp(out_path,self.dt_now,traceback.format_exc(limit=None),self.inp_error_log)        
      out_text = f'結果変換でエラーが発生しました.\nerror.logを確認してください.'
    if not self.nogui: self.status.insert(tk.END,out_text+'\n'); self.status.see(tk.END)
    else: print(out_text)

class noGUI_dummy:
  def update_idletasks(self): pass
  def insert(self, index, text): pass
  def see(self, index): pass
  def delete(self, start, end=None): pass
  def index(self, text): return ""
  def configure(self, state): pass