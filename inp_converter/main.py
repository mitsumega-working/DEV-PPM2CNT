# -*- coding: utf-8 -*-
from .writer import WRITER
from .errors import *

import os,datetime,traceback
from os.path import basename, splitext, isdir
from shutil import rmtree

class CONVERTER(WRITER):
  def __init__(self, inp_path,dir_path):
    self.dt_now = datetime.datetime.now().replace(microsecond=0)
    WRITER.__init__(self,inp_path,dir_path, self.dt_now)
    self.inp_path = inp_path
    self.dir_path = dir_path
    self.dflag = False
    
    name = splitext(basename(self.inp_path))[0]
    self.out_dir = os.path.join(self.dir_path,name)
    os.makedirs(self.out_dir,exist_ok=True)
    
    self.out_inc = os.path.join(self.out_dir,'include')
    os.makedirs(self.out_inc,exist_ok=True)

  def convert(self):
    log_path = os.path.join(self.out_dir,'convert.log')
    self.log_file = open(log_path, 'w', encoding='utf-8')
    self.log_file.write(f'### convert {self.dt_now} ###\n')
    self.log_file.write(f'# inp_file: "{self.inp_path}"\n')
    self.log_file.write(f'# FSTR_dir: "{self.out_dir}"\n')
    self.log_file.write('\n---- CONVERT LOG ----\n')

    f = open(self.inp_path); texts = f.readlines()
    f.close()

    self.main_process(texts) # input .inp file
    self.get_SGROUP()
    self.get_order()
    self.redirect_set()
    if len(self.transform) != 0: self.calc_t(); self.rot_condition()
    self.del_empty_cond()


  def main(self):
    for num, function in enumerate([self.convert,self.out_msh]):
      func = ['.inpファイル読み込み','FrontISTRモデル書き出し'][num]

      try: function(); print(f'正常に終了：{func}')
      except ExpectedError as e:
        error_text = f'[{e.__class__.__name__}]{e}'
        out_path = os.path.join(self.dir_path,splitext(basename(self.inp_path))[0])
        write_err_damp(out_path,self.dt_now,error_text,self.inp_error_log)
        self.dflag = True
      except Exception as e:
        out_path = os.path.join(self.dir_path,splitext(basename(self.inp_path))[0])
        write_err_damp(out_path,self.dt_now,traceback.format_exc(limit=None),self.inp_error_log)        
        error_text = f'予期しないエラーが発生しました.\nerror.logを確認してください.'
        self.dflag = True

      if num == 0:
        if self.dflag: self.log_file.write(error_text)
        self.log_file.write('\n-- CONVERT LOG END --\n'); self.log_file.close()
      if self.dflag:
        print('エラー：'+error_text)
        return
    
    # if isdir(os.path.join(self.out_dir,'vis_out')): rmtree(os.path.join(self.out_dir,'vis_out'))
    # if isdir(os.path.join(self.out_dir,'fstrRES')): rmtree(os.path.join(self.out_dir,'fstrRES'))

