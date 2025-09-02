# -*- coding: utf-8 -*-
from .reader import READER
from .templates import templates
from .errors import *

import os
from glob import glob
from os.path import basename, splitext

##########################################
###### Output FrontISTR input Files ######
##########################################
class WRITER(templates, READER):
  def __init__(self, inp_path, dir_path, dt_now):
    READER.__init__(self)
    templates.__init__(self, 'job')
    self.inp_path = inp_path
    self.dir_path = dir_path
    self.dflag = False
    self.date_now = dt_now

    name = splitext(basename(self.inp_path))[0]
    self.out_dir = os.path.join(self.dir_path,name)
    os.makedirs(self.out_dir,exist_ok=True)
    
    self.out_inc = os.path.join(self.out_dir,'include')
    os.makedirs(self.out_inc,exist_ok=True)

  def out_msh(self):
    os.chdir(self.out_inc)

    ### NODE ###
    with open('node.msh','w', encoding='utf-8') as f:
      count = 0
      for i, key in enumerate(self.node_key):
        f.write(key+'\n')
        for id in self.node_id[i]:
          f.write(f' {id}, {",".join(map(str,self.nodes_coord[count]))}\n')
          count += 1
      f.close()

    ### ELEMENT ###
    with open('elem.msh','w', encoding='utf-8') as f:
      for i, key in enumerate(self.elem_key):
        f.write(key+'\n')
        for line in self.elems[i]:
          f.write(' '+line+'\n')
      f.close()

    ### NODE GROUP ###
    if len(self.ngrp) != 0:
      with open('NGRP.msh','w', encoding='utf-8') as f:
        for order, header in self.ngrp_dict.values():
          if header == '': continue
          f.write(f'{header}\n')
          for count in range(0,len(self.ngrp[order]), 10):
            temp = self.ngrp[order][count:count+10]
            f.write(' '+','.join(str(n) for n in temp)+'\n')
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/NGRP.msh\n'

    ### ELEMENT GROUP ###
    if len(self.egrp) != 0:
      with open('EGRP.msh','w', encoding='utf-8') as f:
        for order, header in enumerate(self.egrp_header):
          if header == '':continue
          f.write(header+'\n')
          for count in range(0,len(self.egrp[order]), 10):
            temp = self.egrp[order][count:count+10]
            f.write(' '+','.join(str(n) for n in temp)+'\n')
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/EGRP.msh\n'

    ### SURFACE GROUP ###
    if len(self.sgrp) != 0:
      with open('SGRP.msh','w', encoding='utf-8') as f:
        for sgrp_name, order in self.sgrp_dict.items():
          f.write('!SGROUP, SGRP='+sgrp_name+'\n')
          for count in range(0,len(self.sgrp[order]), 10):
            temp = self.sgrp[order][count:count+10]
            temp = sum(temp, [])
            f.write(' '+','.join(str(n) for n in temp)+'\n')
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/SGRP.msh\n'

    ### CONTACT PAIR ###
    if len(self.cpairs) != 0:
      with open('CPAIR.msh','w', encoding='utf-8') as f:
        for i, cpair in enumerate(self.cpairs):
          f.write(f'!CONTACT PAIR, NAME=CP{i+1}, TYPE=SURF-SURF\n ')
          f.write(cpair[1]+'\n')
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/CPAIR.msh\n'
      self.control_files += '!INCLUDE, INPUT=include/CONTACT.msh\n'

    ### TIED PAIR ###
    if len(self.tied) != 0:
      f1 = open('TPAIR.msh','w', encoding='utf-8')
      f2 = open('TIED.msh','w', encoding='utf-8'); f2.write(self.tied_cparam)
      f2.write('!CONTACT, GRPID=2, INTERACTION = TIED, CONTACTPARAM=CPARAM_TIED\n')
      for i, tpair in enumerate(self.tied):
        f1.write(f'!CONTACT PAIR, NAME=TP{i+1}, TYPE=SURF-SURF\n ')
        f1.write(tpair+'\n')
        f2.write(f' TP{i+1}, 0.3, 1.0e3\n')
      f1.close();f2.close()
      self.model_files += '!INCLUDE, INPUT=include/TPAIR.msh\n'
      self.control_files += '!INCLUDE, INPUT=include/TIED.msh\n'

    ### MATERIAL & SECTION ###
    with open('MATSEC.msh','w', encoding='utf-8') as f:
      for mat_name, order in self.mat_dict.items():
        mat = self.materials[order]; nitem = 1
        if '!DENSITY' in mat: nitem = 2
        f.write(f'!MATERIAL, NAME={mat_name}, ITEM={nitem}\n')
        f.write('!ITEM=1, SUBITEM=2\n ')
        for data in mat['!ELASTIC']:
          f.write(' '+','.join(data)+'\n')
        if '!DENSITY' in mat:
          f.write('!ITEM=2, SUBITEM=1\n ')
          for data in mat['!DENSITY']:
            f.write(' '+','.join(data)+'\n')
      for section in self.sections:
        f.write(section+'\n')
      f.close()

    ### PLASTIC ###
    with open('PLASTIC.msh','w', encoding='utf-8') as f:
      for mat_name, order in self.mat_dict.items():
        mat = self.materials[order]
        f.write('!MATERIAL, NAME='+mat_name+'\n')
        for key, datas in mat.items():
          if key == '!ELASTIC': key +=',CAUCHY'
          if key == '!PLASTIC': 
            key +=',YIELD=MISES,HARDEN=MULTILINEAR'
            if len(datas[0]) == 3: key += ',DEPENDENCIES=1'
          elif len(datas) > 1: key += ',DEPENDENCIES=1'
          f.write(key+'\n')
          for data in datas: f.write(' '+','.join(data)+'\n')
      f.write('#!SECTION,SECNUM=1,FORM341=FI/SELECTIVE_ESNS\n#!SECTION,SECNUM=1,FORM361=FI/IC/FBAR/BBAR\n')
      f.close()
    self.control_files += '!INCLUDE, INPUT=include/PLASTIC.msh\n'

    ### TEMPERATURE ###
    if len(self.temperature) != 0:
      with open('TEMP.msh','w', encoding='utf-8') as f:
        for load in self.temperature:
          f.write(load[0]+'\n ')
          for data in load[1]:
            if data[0] == '': data[0] = 'ALL'
            line = data[0] + ',' + data[-1]
            f.write(line+'\n')
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/TEMP.msh\n'

    ### BOUNDARY ###
    if len(self.boundary) != 0:
      with open('BC.msh','w', encoding='utf-8') as f:
        for bc in self.boundary:
          f.write(bc[0]+'\n')
          for data in bc[1]:
            f.write(' '+','.join(data)+'\n')
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/BC.msh\n'
      self.step += ' BOUNDARY, 1\n'

    ### CLOAD ###
    if len(self.cload) != 0:
      with open('CLOAD.msh','w', encoding='utf-8') as f:
        for load in self.cload:
          f.write(load[0]+'\n')
          for data in load[1]:
            if data[0] == '': data[0] = 'ALL'
            f.write(' '+','.join(data)+'\n')
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/CLOAD.msh\n'

    ### DLOAD ###
    if len(self.dload) != 0:
      with open('DLOAD.msh','w', encoding='utf-8') as f:
        for load in self.dload:
          if '!DSLOAD' in load[0]: 
            load[0] = load[0].replace('!DSLOAD','!DLOAD')
            load[1][1] = 'S'
          f.write(load[0]+'\n')
          if load[1][0] == '': load[1][0] = 'ALL'
          if load[1][1] == 'CENTRIF': load[1][1] = 'CENT'
          f.write(' '+','.join(load[1])+'\n')
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/DLOAD.msh\n'

    ### AMPLITUDE ###
    if len(self.amp) != 0:
      with open('AMP.msh','w', encoding='utf-8') as f:
        for header, order in self.amp_dict.items():
          f.write(header+'\n')
          for count in range(0,len(self.amp[order]), 2):
            temp = self.amp[order][count:count+2]
            f.write(f' {temp[1]},{temp[0]}\n')
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/AMP.msh\n'

    ### TIMEPOINTS ###
    if self.timepoints != [0,1]:
      with open('TPOINTS.msh','w', encoding='utf-8') as f:
        f.write(self.tpoint_format)
        text = '\n '.join([str(t) for t in self.timepoints[1:-1]])
        f.write(text)
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/TPOINTS.msh\n'

    ### INITIAL CONDITIONS ###
    if len(self.initial_conditions) != 0:
      with open('INIT.msh','w', encoding='utf-8') as f:
        for cond in self.initial_conditions:
          f.write(cond[0]+'\n ')
          text = '\n '.join(cond[1])
          f.write(text)
        f.close()
      self.control_files += '!INCLUDE, INPUT=include/INIT.msh\n'

    ### EQUATION ###
    if ''.join(self.equation) != '':
      with open('EQUATION.msh','w', encoding='utf-8') as f:
        for text in self.equation:
          f.write(text)
        f.close()
      self.model_files += '!INCLUDE, INPUT=include/EQUATION.msh\n'
      if len(self.boundary) == 0: self.step += ' BOUNDARY, 1\n'

    self.make_template()

    if len(self.cpairs) != 0:
    ### CONTACT ###
      with open('CONTACT.msh','w', encoding='utf-8') as f:
        f.write(self.cparam_format+self.contact_format)
        for i, cpair in enumerate(self.cpairs):
          fric = self.contact_info[cpair[0]]
          f.write(f' CP{i+1}, {fric:5.3f}, 1.0e3\n')
        f.close()

    ### STEP ###
    f = open('STEP.msh','w', encoding='utf-8')
    f.write(self.make_step_form())
    f.close()

    ### OUTPUT ###
    f = open('OUTPUT.msh','w', encoding='utf-8')
    f.write(self.output_format); f.close()

    ### SPRING ###
    f = open('SPRING.msh','w', encoding='utf-8')
    f.write(self.spring_format); f.close()

    os.chdir(self.out_dir)

    ### .msh file ###
    f = open(f'{self.title}.msh','w', encoding='utf-8')
    f.write(self.msh_format); f.close()

    ### .cnt file ###
    f = open(f'{self.title}.cnt','w', encoding='utf-8')
    f.write(self.cnt_format); f.close()

    ### hecmw_ctrl.dat file ###
    f = open(os.path.join('hecmw_ctrl.dat'),'w', encoding='utf-8')
    f.write(self.dat_format); f.close()
