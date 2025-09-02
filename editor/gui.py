# -*- coding: utf-8 -*-
from editor.templates import EDITOR_templates

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, StringVar, BooleanVar, IntVar
from ttkthemes import ThemedTk, ThemedStyle
import os, sys
from os.path import dirname, abspath, join, normpath, isfile, splitext
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

class EDITOR(EDITOR_templates):
  def __init__(self, inp_path, setting):
    self.root_dir = dirname(abspath(__file__))
    self.inc_dir = os.path.join(inp_path.rstrip('.inp'), 'include')
    self.inp_path = inp_path
    self.select_theme = 'alt'
    self.root = ThemedTk(self.select_theme)
    if splitext(sys.argv[0])[-1] == '.exe':
      self.root.iconbitmap(True,join(sys.prefix,'icon.ico'))
      self.img = tk.PhotoImage(file=join(sys.prefix,'file.png'))
    else:
      self.root.iconbitmap(True,join(self.root_dir,'icon.ico'))
      self.img = tk.PhotoImage(file=join(self.root_dir,'file.png'))
    self.root.title("エディタ")
    self.style = ThemedStyle()
    self.editing_files = set()
    self.version = 'Ver: 1.1\n2025.09.02'
    self.setting = setting
    EDITOR_templates.__init__(self,'job')
  
  def editor(self,header,exepath):
    if not self.setting is None:
      if isfile(self.setting): self.update_from_xml(self.setting)
    self.header = header
    self.exepath = abspath(exepath)
    self.root.geometry("580x500+100+100")
    self.make_window()
    self.root.mainloop()
    self.write_part_dat()
    self.save_to_xml(self.setting)

  def make_window(self):
    self.notebook = ttk.Notebook(self.root)
    self.edit_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.edit_tab, text='ファイル編集')

    self.main_frame = ttk.Frame(self.edit_tab)
    self.main_frame.pack(fill="both", expand=True)

    self.make_filetree()
    self.make_texteditor()

    self.text.bind("<<Modified>>", self.on_text_modified)
    self.root.bind("<Control-s>", self.ctrl_s_save)

    self.setting_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.setting_tab, text='実行環境')
    self.make_setting()

    self.exe_quit_button()
    self.notebook.pack(expand=1, fill='both')
    self.fix_appearance(); self.fix_editor_apperance()

#### making tab1
  def make_filetree(self):
    # 左：ファイル一覧 (Treeview)
    self.filetree = ttk.Frame(self.main_frame)
    self.filetree.pack(side="left", fill="y", padx=5, pady=5)

    self.file_tree = ttk.Treeview(self.filetree, show="tree")
    self.file_tree.pack(fill="y", expand=True)
    self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
    self.file_tree.column("#0", width=120, stretch=False)
    self.refresh_file_list()
    # スタイル（赤色表示用）
    self.file_tree.tag_configure('red', foreground='red')

  def make_texteditor(self):
    # 右：テキストエディタ
    self.text_frame = ttk.Frame(self.main_frame)
    self.text_frame.pack(side="right", fill="both", expand=True)

    self.text = tk.Text(self.text_frame, wrap=tk.WORD, font=("Consolas", 10), undo=True)
    self.text.pack(expand=True, fill="both", padx=5, pady=5)
    self.scrollbar = ttk.Scrollbar(self.text, command=self.text.yview)
    self.text.configure(yscrollcommand=self.scrollbar.set)
    self.scrollbar.pack(side="right", fill="y")

#### functions for tab1
  def refresh_file_list(self):
    self.file_tree.delete(*self.file_tree.get_children())
    # self.text.delete("1.0", tk.END)
    self.current_file = None
    self.editing_files.clear()
    msh_files = [f for f in os.listdir(self.inc_dir) if f.endswith('.msh')]
    for f in sorted(msh_files):
      self.file_tree.insert("", tk.END, iid=f, text=f, tags=("normal",))

  def on_file_select(self, event):
    selection = self.file_tree.selection()
    if not selection: return
    filename = selection[0]
    try:
      with open(join(self.inc_dir,filename), "r", encoding="utf-8") as f:
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, f.read())
        self.current_file = filename
        self.text.edit_modified(False)  # 変更フラグをリセット
        self.root.title(f"Editing: {filename}")
        self.text.edit_reset()
        self.highlight_syntax()
    except Exception as e: messagebox.showerror("Error", f"ファイルを開けませんでした:\n{e}")

  def highlight_syntax(self, event=None):
    self.text.tag_remove("header", "1.0", tk.END)
    self.text.tag_remove("comment", "1.0", tk.END)

    lines = self.text.get("1.0", tk.END).splitlines()
    for i, line in enumerate(lines):
      index = f"{i + 1}.0"
      if line.startswith("!"):
        self.text.tag_add("header", index, f"{index} lineend")
      elif line.startswith("#"):
        self.text.tag_add("comment", index, f"{index} lineend")

  def on_text_modified(self, event=None):
    if self.current_file and self.text.edit_modified():
      self.set_editing_flag(self.current_file)
      self.highlight_syntax()
      self.text.edit_modified(False)
    return

  def ctrl_s_save(self, event=None):
    self.save_file()
    return
  
  def save_file(self):
    if not self.current_file:
      messagebox.showwarning("Warning", "ファイルが選択されていません。")
      return
    try:
      with open(join(self.inc_dir,self.current_file),"w",encoding="utf-8") as f:
        f.write(self.text.get("1.0", tk.END).rstrip())
      self.clear_editing_flag(self.current_file)
      self.text.edit_modified(False)  # フラグリセット
    except Exception as e: messagebox.showerror("Error", f"保存中にエラー:\n{e}")

  def set_editing_flag(self, filename):
    if filename not in self.editing_files:
      self.editing_files.add(filename)
      self.file_tree.item(filename, text=f"{filename} [編集中]")
      self.file_tree.item(filename, tags="red")

  def clear_editing_flag(self, filename):
    if filename in self.editing_files:
      self.editing_files.remove(filename)
      self.file_tree.item(filename, text=filename)
      self.file_tree.item(filename, tags="normal")

#### making tab2
  def make_setting(self):
    def switch_mode():
      if self.select_theme == 'alt': self.select_theme = 'black'
      else: self.select_theme = 'alt'
      self.fix_appearance(); self.fix_editor_apperance()
    
    modebtn = ttk.Button(self.setting_tab, text='Switch Dark/Light Mode', command=switch_mode)
    modebtn.pack(pady=(5,0),anchor=tk.N)
    
    #parallel frame
    para_frame = ttk.LabelFrame(self.setting_tab, relief='groove',text='並列設定')
    para_frame.pack(fill='both', padx=10, pady=2.5)

    def switch_part():
      if self.part_select.get():
        pnum_spin.configure(state='normal',foreground='')
        self.tnum_var = StringVar(value='1'); tnum_spin.configure(textvariable=self.tnum_var)
      else: pnum_spin.configure(state='disable',foreground='gray')
      update_label()
  
    def update_label(*args):
      global l_ncore; n_core = int(self.tnum_var.get())
      if self.part_select.get(): n_core *= int(self.pnum_var.get())
      l_ncore.config(text=f'必要なコア数：{n_core:4d}')
      self.get_exe_command(); sub_command = ' '.join(self.command)
      if self.part_select.get(): sub_command = 'hecmw_part1.exe\n' + sub_command
      exe_path.configure(text=self.exepath)
      exe_command.configure(text=sub_command)

    partition = ttk.Checkbutton(para_frame,text='領域分割する',width=11,variable=self.part_select,command=switch_part)
    partition.grid(row=0,column=0,padx=(10,0), pady=(0,2.5),columnspan=2)

    self.make_label(para_frame,'分割数：',1,0,8,xpad=(10,0),ypad=(0,2.5),anc=tk.E)
    pnum_spin = ttk.Spinbox(para_frame,width=5,from_=1,to=100,textvariable=self.pnum_var)
    pnum_spin.grid(row=1, column=1, padx=(0,5), pady=(0,2.5))
    self.pnum_var.trace_add('write', update_label)

    self.make_label(para_frame,'スレッド並列数：',1,2,14,xpad=(10,0),ypad=(0,2.5),anc=tk.E)
    tnum_spin = ttk.Spinbox(para_frame,width=5,from_=1,to=100,textvariable=self.tnum_var)
    tnum_spin.grid(row=1, column=3, padx=(0,5), pady=(0,2.5))
    self.tnum_var.trace_add('write', update_label)
    
    global l_ncore
    l_ncore = self.make_label(para_frame,'',1,4,17,xpad=5,ypad=(0,2.5))

    #execution frame
    exe_frame = ttk.LabelFrame(self.setting_tab, relief='groove',text='実行環境・コマンド')
    exe_frame.pack(fill='both', padx=10, pady=2.5)

    self.make_label(exe_frame,'fistr1.exeのパス：',0,0,'',xpad=(10,0),ypad=0,anc=tk.W)
    def dir_read(): self.exepath = normpath(filedialog.askdirectory(initialdir=self.exepath)); update_label()
    filevtn = ttk.Button(exe_frame, command=dir_read, image=self.img, width=5)
    filevtn.grid(row=0, column=1, sticky='W')
    exe_path = self.make_label(exe_frame,'',1,0,50,xpad=(10,0),ypad=2.5,anc=tk.E,cspan=2)
    exe_path.grid(row=1, column=0,sticky=tk.EW)
    exe_path.configure(relief="solid",anchor='center')

    self.make_label(exe_frame,'実行コマンド：',2,0,'',xpad=(10,0),ypad=0,anc=tk.W)
    exe_command = self.make_label(exe_frame,'',3,0,50,xpad=(10,0),ypad=2.5,anc=tk.E,cspan=2)
    exe_command.grid(row=3, column=0,sticky=tk.EW)
    exe_command.configure(relief="solid",anchor='center')
    exe_frame.grid_columnconfigure(1, weight=1)
    
    # ttk.Checkbutton(exe_frame,text='標準出力をリアルタイムでモニタしない',width=30
    #                 ,variable=self.mon_out).grid(row=3,column=0,padx=(10,0))

    # switch_part()
    update_label()

    setting_tab_bottom = ttk.Frame(self.setting_tab); setting_tab_bottom.pack(fill='both',expand=True)
    
    # version frame
    version_frame = ttk.Frame(setting_tab_bottom)
    version_frame.pack(fill='both',side='bottom',expand=True)
    ver_label = ttk.Label(version_frame,width=10,text=self.version,relief="ridge",anchor='center')
    ver_label.pack(padx=12.5,pady=5,side='bottom',anchor='se')

  def make_label(self,frame,word,r,c,w,xpad,ypad,anc=tk.CENTER,cspan=1):
    label = ttk.Label(frame,width=w,text=word,anchor=anc)
    label.grid(row=r, column=c, padx=xpad, pady=ypad, columnspan=cspan)
    return label

  def fix_appearance(self):
    self.style.theme_use(self.select_theme)
    self.style.configure('TNotebook.Tab', font=('Meiryo',12))
    self.style.configure('TCheckbutton', font=('Meiryo',10))
    self.style.configure('TButton', font=('Meiryo',9),anchor='n')
    self.style.configure('TLabel', font=('Meiryo',10))
    self.style.configure('TLabelframe.Label', font=('Meiryo',8))

    if self.select_theme == 'black': bcolor = 'black'; fcolor = 'white'
    else:                            bcolor = 'white'; fcolor = 'black'
    
    self.style.map('TCombobox', fieldbackground=[("readonly", "!focus", bcolor),("readonly", "focus", bcolor),("!readonly", "!focus", bcolor)])
    self.style.map('TCombobox', foreground=[("readonly", "!focus", fcolor),("readonly", "focus", fcolor),("!readonly", "!focus", 'gray')])

    self.style.configure('wstyle.TEntry', fieldbackground=bcolor, foreground=fcolor, insertcolor=fcolor)
    self.style.configure('wstyle.TSpinbox', fieldbackground=bcolor, foreground=fcolor, insertcolor=fcolor)

    self.style.configure('rstyle.TEntry', fieldbackground="lightcoral")
    self.style.configure('rstyle.TSpinbox', fieldbackground="lightcoral")

    self.style.configure("Horizontal.TProgressbar", troughcolor="#dcdad5", background="#93c47d")
    self.style.configure("Treeview", font=('Meiryo', 10), background=bcolor, foreground=fcolor, fieldbackground=bcolor)
    
    def get_values(widget):
      for child in widget.winfo_children():
        if child.winfo_children(): get_values(child)
        elif isinstance(child, ttk.Combobox):
          if str(child['state']) == 'normal': child.configure(state='readonly')
          child.configure(font=('Meiryo',10), width=14)
          child.option_add('*TCombobox*Listbox.font', ('Meiryo',10))
        elif isinstance(child, ttk.Entry):
          if isinstance(child, ttk.Spinbox):
            child.configure(font=('Meiryo',9), justify='right',style='wstyle.TSpinbox',foreground=fcolor)
          else: child.configure(font=('Meiryo',9), justify='right',style='wstyle.TEntry')
    get_values(self.root)

  def fix_editor_apperance(self):
    if self.select_theme == 'black': bcolor = 'black'; fcolor = 'white'; hcolor = 'pink'; ccolor = 'green yellow'
    else:                            bcolor = 'white'; fcolor = 'black'; hcolor = 'purple'; ccolor = 'green'
    self.text.configure(bg=bcolor, fg=fcolor, insertbackground=fcolor)
    self.text.tag_configure("header", foreground=hcolor)
    self.text.tag_configure("comment", foreground=ccolor)
    self.file_tree.tag_configure("normal", foreground=fcolor)

#### buttons
  def exe_quit_button(self):
    #### Create Execution or Quit Button ####
    frame_cvtbtn = ttk.Frame(self.root)
    frame_cvtbtn.pack(side=tk.BOTTOM, fill=tk.X, pady=0)

    cvtbtn = ttk.Button(frame_cvtbtn, text="実行",command=self.root.quit)
    quitbtn = ttk.Button(frame_cvtbtn, text="閉じる",command=self.exit)

    cvtbtn.pack(fill = "x", padx=5, side = "left", pady=10)
    quitbtn.pack(fill = "x", padx=5, side = "right", pady=10)

#### export settings
  def save_to_xml(self, filename):
    def get_val(var,parent,level=''):
      parent.set('type', type(var).__name__)
      if isinstance(var, list):
        for val in var:
          if isinstance(var, list):
            child = ET.SubElement(parent,'inner'+level)
            get_val(val,child,level+'_in')
      elif isinstance(var, (IntVar, StringVar, BooleanVar)):
        parent.text = str(var.get())
      elif isinstance(var, str):
        parent.text = var

    xml_root = ET.Element(self.__class__.__name__)
    for key, value in self.__dict__.items():
      if ('select' in key) or ('var' in key) or ('exepath' in key) or ('command' in key) or ('header' in key):
        child = ET.SubElement(xml_root, key)
        get_val(value,child)
  
    xml_str = ET.tostring(xml_root, encoding='utf-8')
    xml_pretty_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    with open(join(dirname(abspath(__file__)),filename), 'w', encoding='utf-8') as f: f.write(xml_pretty_str)

#### import settings
  def update_from_xml(self,filename):
    tree = ET.parse(filename)
    for child in tree.getroot():
      var_type = child.get('type', 'str')
      if var_type == 'list':
        items = []
        for item in child.iter('inner'):
          if item.get('type', 'str') != 'list':
            items.append(StringVar(value=item.text))
          else:
            items.append([])
            for val in item.iter('inner_in'):
              items[-1].append(StringVar(value=val.text))
        setattr(self, child.tag, items)
      elif var_type == 'StringVar': setattr(self, child.tag, StringVar(value=child.text))
      elif var_type == 'IntVar': setattr(self, child.tag, IntVar(value=int(child.text)))
      elif var_type == 'BooleanVar': setattr(self, child.tag, BooleanVar(value=bool(child.text=='True')))
      elif var_type == 'str': setattr(self, child.tag, child.text)

### hecmw_part_ctrl.dat file ###
  def write_part_dat(self):
    self.make_ctrl_files()
    ### .dat file ###
    f = open(os.path.join(self.inp_path.rstrip('.inp'),'hecmw_ctrl.dat'),'w', encoding='utf-8')
    f.write(self.dat_format); f.close()

    if self.part_select.get():
      f = open(os.path.join(self.inp_path.rstrip('.inp'),'hecmw_part_ctrl.dat'),'w', encoding='utf-8')
      f.write(self.pdat_format); f.close()

  def exit(self): sys.exit(1)