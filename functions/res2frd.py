# -*- coding: utf-8 -*-
import numpy as np

class res2frd:
  def __init__(self):
    self.ttime = 0
    self.totalnum = 0
    self.newstep = True
    self.nres_dict = {}
    self.eres_dict = {}
    self.nflags = []
    self.eflags = []
    self.node_res = ''
    self.elem_res = ''
    self.res_dict = {'DISPLACEMENT':'DISP','REACTION_FORCE':'FORC',
                     'ElementalSTRAIN':'STRESS','ElementalSTRESS':'TOSTRAIN'}

  def allocate_resarray(self,num,mode):#,cres):
    if not self.newstep: return
    tgt_flag = [self.nflags,self.eflags][mode]
    dnum = [3,6][mode]
    nres = len(tgt_flag)*dnum

    if mode == 0: #node
      self.node_res = np.full([num,nres],0.0)
    elif mode == 1: #elem
      self.elem_res = np.full([num,nres],0.0)
    # self.cont_res = np.full([nnode,cres],0.0)

  def get_result_dict(self,nums,results,mode):
    target = [self.nres_dict, self.eres_dict][mode]

    count = 0
    for i, result in enumerate(results):
      target[result] = count
      count += nums[i]
  
  def extract_result(self, mode):
    n_names = ['DISPLACEMENT','REACTION_FORCE']
    e_names = ['ElementalSTRAIN','ElementalSTRESS']
    names = [n_names,e_names][mode]
    tgt_flag = [self.nflags,self.eflags][mode]
    tgt_dict = [self.nres_dict, self.eres_dict][mode]

    for name in names:
      if name in tgt_dict: tgt_flag.append(name)

  def get_data(self,data,mode,idx):
    tgt_flag = [self.nflags,self.eflags][mode]
    tgt_dict = [self.nres_dict, self.eres_dict][mode]
    tgt_res = [self.node_res, self.elem_res][mode]
    num = [3,6][mode]
    
    for i, name in enumerate(tgt_flag):
      start = tgt_dict[name]
      tgt_res[idx,num*i:num*(i+1)] = np.array(data[start:start+num])

  def frd_head(self,step,nnode):
    self.totalnum += 1
    text = f'''\
    1PSTEP              {self.totalnum:>12}{step:>12}           1          
  100CL  {100+step}{self.ttime:12.9f}{nnode:>12}                     0{step:>5}           1\n'''
    
    return text
