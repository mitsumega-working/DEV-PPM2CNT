# -*- coding: utf-8 -*-
import numpy as np
import re
from math import sqrt
from functions.errors import *
from functions.res2frd import res2frd

def get_param(pattern, header, name_only=True):
  param = ''
  match = re.search(pattern, header)
  if match == None: return param
  
  if name_only: param = match.group(1)
  else:         param = match.group()
  return param

def write_error(text,log_file):
  print(text)
  log_file.write(text+'\n')

def normalize(v):
  if (v == np.zeros(3)).all(): return v
  n_v = v / sqrt(v@v)
  return n_v

etype_dic = {'C3D4':'341','C3D10':'342','C3D8':'361','C3D6':'351'}

class fistr_model:
  def __init__(self):
    self.inp_error_log = [0,'']
    self.heading = ''
    #
    self.elems = []; self.elem_id = []
    self.node_key = [];   self.elem_key = []
    self.nodes_coord = []; self.node_id = []
    self.etypes = []
    #
    self.ngrp = []
    self.ngrp_dict = {}
    #
    self.egrp = []
    self.egrp_header = []
    self.egrp_dict = {}
    #
    self.sgrp = [];    self.sgrp_dict = {}
    self.cpairs = [];   self.contact_info = {}
    self.tied = []
    #
    self.sections = []
    self.materials = [];  self.mat_dict = {}
    #
    self.boundary = []; self.temperature = []
    self.amp = []; self.amp_dict = {}; self.timepoints = [0,1]
    self.cload = [];    self.dload = []
    #
    self.cnt_temp = ''
    self.msh_temp = ''
    self.ctrl_temp = ''
    #
    self.surfaces = []
    #
    self.transform = []; self.equation = []; self.eq2bc = [] 
    #
    self.steps = []
    #
    self.initial_conditions = []
    #
    self.log_file = None

class CONVERTER(fistr_model, res2frd):
  def __init__(self):
    super().__init__()
    res2frd.__init__(self)
  
  ########################################
  ###### Function for Each Keywords ######
  ########################################
  def input_heading(self,text):
    self.heading = text.replace('UNIT SYSTEM','Unit system'); self.flag = ''

  def input_include_file(self,texts):
    with open(self.include_path, encoding='utf-8') as f:
      texts += f.readlines()
      f.close()

  def input_node(self, text):
    self.node_id[-1].append(int(text.split(',')[0]))
    x,y,z = map(float, text.split(',')[1:])
    self.nodes_coord.append(np.array([x,y,z]))
    if self.nset_flag: self.ngrp[-1].append(int(text.split(',')[0]))

  def input_elem(self, text):
    temp = list(map(str, text.split(',')))
    if len(temp) == 11: temp=[temp[i] for i in [0,1,2,3,4,6,7,5,8,9,10]]
    self.elems[-1].append(','.join(temp))
    self.elem_id[-1].append(int(temp[0]))
    if self.elset_flag: self.egrp[-1].append(int(temp[0]))

  def input_nset(self, text):
    try:
      for n in list(map(int, text.split(','))): self.ngrp[-1].append(n)
    except: self.ngrp[-1].append(text)

  def input_elset(self, text):
    try:
      for n in list(map(int, text.split(','))): self.egrp[-1].append(n)
    except: self.egrp[-1].append(text)

  def input_surface(self, text):
    self.surfaces[-1].append(text)

  def input_contact(self, text):
    self.cpairs[-1].append(text)

  def input_material(self, text):
    temp = text.split(',')
    self.materials[-1][self.mmode].append(temp)

  def input_amp(self, text):
    temp = list(map(float, text.split(',')))
    self.amp[-1] += temp

  def input_temprature(self, text):
    temp = text.replace(' ', '').split(',')
    self.temperature[-1][-1].append(temp)

  def input_boundary(self, text):
    temp = text.replace(' ', '').split(',')
    start = int(temp[1]); end = int(temp[2])
    if (start > 3) or (end > 3):
      write_error('NOT SUPPORTED DOF:'+text, self.log_file); return
    if len(temp) == 3: temp.append('0.0')
    self.boundary[-1][-1].append(temp)

  def input_cload(self, text):
    temp = text.replace(' ', '').split(',')
    self.cload[-1][-1].append(temp)
  
  def input_dload(self, text):
    temp = text.replace(' ', '').split(',')
    if temp[1] == 'CENTRIF': temp[2] = f'{np.sqrt(float(temp[2])):g}'
    self.dload[-1].append(temp)
  
  def input_friction(self, text):
    self.contact_info[self.temp_] = float(text)

  def input_tied(self, text):
    self.tied.append(text)

  def input_transform(self, text):
    x1, y1, z1, x2, y2, z2 = map(float, text.split(','))
    a = np.array([x1, y1, z1]); b = np.array([x2, y2, z2])
    self.transform[-1].append(a)
    self.transform[-1].append(b)

  def input_step(self, text):
    self.steps[-1]['increment'] = text

  def input_icond(self, text):
    self.initial_conditions[-1][1].append(text)

  #######################################################
  ###### Convert Keyword to Header and Manage Flag ######
  #######################################################
  def keyword2header(self, text):
    header = text.replace('*','!').replace(' ','')
    header = header.replace('AMPLITUDE=','AMP=')
    if '!HEADING' in header: self.flag = 'H'
    elif '!INCLUDE' in header:
      path = get_param(r'INPUT=([^,]*)', header+',')
      self.flag = 'I'; self.include_path = path
    elif '!NODE' in header:
      if 'NODEFILE' in header: self.flag = ''; return
      self.flag = 'N'; self.nset_flag = False
      name = get_param(r'NSET=([^,]*)', header+',')
      if name != '': 
        self.ngrp_dict[name] = [len(self.ngrp), '']
        self.nset_flag = True; self.ngrp.append([])
      self.node_key.append(header.replace('NSET','NGRP',1))
      self.node_id.append([])
    elif '!ELEMENT' in header:
      self.flag = 'E'
      name = get_param(r'ELSET=([^,]*)', header+','); self.elset_flag = False
      header = header.replace('ELSET','EGRP',1)
      etype = get_param(r'TYPE=(C3D\d+)', header)
      header = re.sub(r'(TYPE=C3D\d+)[A-Z]',r'\1',header)
      try: header = header.replace(etype,etype_dic[etype],1)
      except Exception: raise KeyWordError(etype_error(self.inp_error_log))
      self.elem_key.append(header)
      if name != '':
        self.egrp_header.append('');self.elset_flag=True
        self.egrp_dict[name]=len(self.egrp);self.egrp.append([])
      self.elems.append([]); self.elem_id.append([])
    elif '!NSET' in header:
      self.flag = 'NS'
      header = re.sub(r'(,INSTANCE=[^,]*)','',header)
      name = get_param(r'NSET=([^,]*)', header+',')
      header = header.replace('NSET=','NGRP=').replace('!NSET','!NGROUP')
      self.ngrp_dict[name] = [len(self.ngrp), header]
      self.ngrp.append([])
    elif '!ELSET' in header:
      self.flag = 'ES'
      name = get_param(r'ELSET=([^,]*)', header+',')
      self.egrp_dict[name] = len(self.egrp)
      header = re.sub(r'(,INSTANCE=[^,]*)','',header)
      header = header.replace('ELSET=','EGRP=').replace('!ELSET','!EGROUP')
      self.egrp_header.append(header)
      self.egrp.append([])
    elif '!SURFACE,' in header:
      self.flag = 'S'
      name = get_param(r'NAME=([^,]*)', header+',')
      self.sgrp_dict[name] = len(self.sgrp)
      self.surfaces.append([]); self.sgrp.append([])
    elif '!CONTACTPAIR' in header:
      self.flag = 'CP'
      name = get_param(r'INTERACTION=([^,]*)', header+',')
      self.cpairs.append([name])
    elif '!MATERIAL' in header:
      self.flag = 'M'
      name = get_param(r'NAME=([^,]*)', header+',')
      self.mat_dict[name] = len(self.materials)
      self.materials.append({})
    elif '!ELASTIC' in header:
      self.flag = 'M'
      self.materials[-1]['!ELASTIC']=[]; self.mmode='!ELASTIC'
    elif '!PLASTIC' in header:
      self.flag = 'M'
      self.materials[-1]['!PLASTIC']=[]; self.mmode='!PLASTIC'
    elif '!DENSITY' in header:
      self.flag = 'M'
      self.materials[-1]['!DENSITY']=[]; self.mmode='!DENSITY'
    elif '!EXPANSION' in header:
      self.flag = 'M'
      self.materials[-1]['!EXPANSION']=[]; self.mmode='!EXPANSION'
    elif '!SOLIDSECTION' in header:
      egrp = get_param(r'ELSET=([^,]*)', header+',')
      mat = get_param(r'MATERIAL=[^,]*', header+',', name_only=False)
      self.sections.append('!SECTION,TYPE=SOLID,EGRP='+egrp+','+mat)
      self.flag = 'SC'
    elif '!AMPLITUDE' in header:
      self.flag = 'A'
      self.amp_dict[header] = len(self.amp)
      self.amp.append([])
    elif '!BOUNDARY' in header:
      if 'OP=NEW' in header: self.flag = ''; return
      self.flag = 'B'
      header += f',GRPID={len(self.steps)}'
      self.boundary.append([header,[]])
      self.steps[-1]['BOUNDARY'] = len(self.steps)
    elif '!TEMPERATURE' in header:
      if 'OP=NEW' in header: self.flag = ''; return
      self.flag = 'T'
      header += f',GRPID={len(self.steps)}'
      self.temperature.append([header,[]])
      self.steps[-1]['LOAD'] = len(self.steps)
    elif '!CLOAD' in header:
      if 'OP=NEW' in header: self.flag = ''; return
      self.flag = 'CL'
      header += f',GRPID={len(self.steps)}'
      self.cload.append([header,[]])
      self.steps[-1]['LOAD'] = len(self.steps)
    elif ('!DLOAD' in header) or ('!DSLOAD' in header):
      if 'OP=NEW' in header: self.flag = ''; return
      self.flag = 'DL'
      header += f',GRPID={len(self.steps)}'
      self.dload.append([header])
      self.steps[-1]['LOAD'] = len(self.steps)
    elif '!TIE' in header:
      self.flag = 'TI'
    elif '!SURFACEINTERACTION' in header:
      self.flag = ''
      self.temp_ = get_param(r'NAME=([^,]*)', header+',')
      self.contact_info[self.temp_] = 0.0
    elif '!FRICTION' in header:
      self.flag = 'FR'
    elif '!TRANSFORM' in header:
      self.flag = 'TF'
      ttype = get_param(r'TYPE=([^,]*)', header+',')
      if ttype == '': ttype = 'R'
      nset = get_param(r'NSET=([^,]*)', header+',')
      self.transform.append([ttype,nset])
    elif '!STEP' in header:
      self.flag = 'ST'
      self.steps.append({})
      maxinc = get_param(r'INC=([^,]*)', header+',')
      if maxinc != '': self.steps[-1]['SUBSTEPS'] = int(maxinc)
      else: self.steps[-1]['SUBSTEPS'] = 100
    elif '!STATIC' in header:
      self.flag = 'ST'
      if 'DIRECT' in header: self.steps[-1]['TYPE'] = 'FIXED'
      else: self.steps[-1]['TYPE'] = 'AUTO'
      self.steps[-1]['increment'] = '1, 1.0, 1.0e-5, 1'
    elif '!INITIALCONDITIONS' in header:
      self.flag = 'IC'
      header = header.replace('INITIALCONDITIONS','INITIAL_CONDITION')
      self.initial_conditions.append([header,[]])
    else:
      self.log_file.write('NOT SUPPORTED KEYWORDS:'+text+'\n')
      # print('NOT SUPPORTED KEYWORDS:',text)
      self.flag = ''
    
  ##########################
  ###### Main Process ######
  ##########################
  def main_process(self,texts):
    for text in texts:
      self.inp_error_log[0] += 1; self.inp_error_log[1] = text
      text = text.rstrip(' ,\n').upper()
      text = text.replace('INTERNAL','I')
      # self.log_file.write(text+'\n') ###
      if text == '':continue
      if text[0:2] == '**':continue
      elif text[0] == '*':
        self.counter = 0
        self.keyword2header(text)
      else:
        if self.flag == 'H':
          self.input_heading(text)
        elif self.flag == 'I':
          self.input_include_file(texts)
        elif self.flag == 'N':
          self.input_node(text)
        elif self.flag == 'E':
          self.input_elem(text)
        elif self.flag == 'NS':
          self.input_nset(text)
        elif self.flag == 'ES':
          self.input_elset(text)
        elif self.flag == 'S':
          self.input_surface(text)
        elif self.flag == 'CP':
          self.input_contact(text)
        elif self.flag == 'T':
          self.input_temprature(text)        
        elif self.flag == 'B':
          self.input_boundary(text)
        elif self.flag == 'M':
          self.input_material(text)
        elif self.flag == 'A':
          self.input_amp(text)
        elif self.flag == 'CL':
          self.input_cload(text)
        elif self.flag == 'DL':
          self.input_dload(text)
        elif self.flag == 'FR':
          self.input_friction(text)
        elif self.flag == 'TI':
          self.input_tied(text)
        elif self.flag == 'TF':
          self.input_transform(text)
        elif self.flag == 'ST':
          self.input_step(text)
        elif self.flag == 'IC':
          self.input_icond(text)
        else:
          self.log_file.write('input is skipped:'+text+'\n')
          # print('input is skipped:',text)

  #########################################
  ###### Convert *Surface to !SGROUP ######
  #########################################
  def get_SGROUP(self):
    for i, surface in enumerate(self.surfaces):
      for temp in surface:
        elset_name, s_id = temp.split(',')
        elset_id = self.egrp_dict[elset_name]
        elset = self.egrp[elset_id]
        surf_id = int(re.search(r'S([1-6])', s_id).group(1))
        if 'GENERATE' in self.egrp_header[elset_id]: elset = list(range(elset[0],elset[1]+1,elset[2]))
        for elem in elset:
          self.sgrp[i].append([elem, surf_id])

  #####################################
  ###### Get node and elem ORDER ######
  #####################################
  def get_order(self):
    max_num = max(max(n) for n in self.node_id)+1
    self.node_order = np.full(max_num,-1); temp = []
    for nodes in self.node_id: temp += nodes
    for i, node in enumerate(temp): self.node_order[node] = i
    self.gl_node_id = temp
    self.nnode = len(temp)

    max_num = max(max(e) for e in self.elem_id)+1
    self.elem_order = np.full(max_num,-1); temp = []
    for elems in self.elem_id: temp += elems
    for i, elem in enumerate(temp): self.elem_order[elem] = i
    self.gl_elem_id = temp
    self.nelem = len(temp)

  ####################################
  ###### Redirect Node/Elem Set ######
  ####################################
  def redirect_set(self):
    for order, header in self.ngrp_dict.values():
      if type(self.ngrp[order][0]) == str:
        ngrp = []
        for name in self.ngrp[order]:
          gid = self.ngrp_dict[name][0]
          ngrp += self.ngrp[gid]
        self.ngrp[order] = ngrp

    for order in self.egrp_dict.values():
      if type(self.egrp[order][0]) == str:
        egrp = []
        for name in self.egrp[order]:
          gid = self.egrp_dict[name]
          egrp += self.egrp[gid]
        self.egrp[order] = egrp

  ##################################
  ###### Apply C-SYS to Nodes ######
  ##################################
  def calc_t(self):
    max_num = len(self.node_order)
    self.node_csys = np.full((max_num,3),-1,dtype=int)
    
    for csys_id, tf in enumerate(self.transform):
      ctype = tf[0]; name_ngrp = tf[1]; e1 = tf[2]; e2 = tf[3]
      if   ctype == 'R': e3 = np.cross(e1,e2)
      elif ctype == 'C': e3 = e2 - e1
      elif ctype == 'S': e3 = e2 - e1
      else:
        write_error('NOT SUPPORTED COORDINATE SYSTEM:'+ctype,self.log_file)
        raise ConvertError(trans_error(ctype))
      self.transform[csys_id].append(normalize(e3))

      for n_id in self.ngrp[self.ngrp_dict[name_ngrp][0]]:
        pos = np.where(self.node_csys[n_id] == -1)[0]
        if pos.size > 0: self.node_csys[n_id,pos[0]] = csys_id

  #################################
  ###### Rotation Conditions ######
  #################################
  def rot_condition(self):
    ## proc BC
    for i, bc in enumerate(self.boundary):
      del_list = list(range(len(bc[1])))
      header = bc[0]
      for j, data in enumerate(bc[1]):
        sample_id = self.ngrp[self.ngrp_dict[data[0]][0]][0]
        if sum(self.node_csys[sample_id]) == -3:continue
        del_list.remove(j)

        csys_id = self.node_csys[sample_id][0]
        text = self.get_equ_text(data, csys_id)
        self.equation.append(text)
      if len(del_list) == 0: self.boundary[i] = [header, []]
      else: self.boundary[i][1] = [self.boundary[i][1][n] for n in del_list]
      
      for new_bc in self.eq2bc: self.boundary[i][1].append(new_bc)
      self.eq2bc = []
      if self.boundary[i][1] == []: self.boundary[i] = []
    self.boundary = [val for val in self.boundary if val != []]
    
    ## proc CLOAD
    cload_new = []
    for i, cload in enumerate(self.cload):
      cload_new.append([cload[0],[]])
      for load in cload[1:]:
        for data in load:
          sample_id = self.ngrp[self.ngrp_dict[data[0]][0]][0]
          if sum(self.node_csys[sample_id]) == -3:
            cload_new[-1][-1].append(data);continue
          
          csys_id = self.node_csys[sample_id][0]
          cload_new[-1][-1] += self.get_rot_cload(data,csys_id)
    self.cload = cload_new

  ################################
  ###### Get !EQUATION Text ######
  ################################
  def get_equ_text(self, data, csys_id):
    ngrp_name = data[0]
    dof = int(data[1])+1
    val = float(data[3])

    sys_type = self.transform[csys_id][0]

    text = ''
    text += f'# {ngrp_name}, {dof-1}, {val}\n'
    if sys_type == 'R':
      vec = self.transform[csys_id][dof]
      text = self.make_eq(vec,val,ngrp_name)

    elif sys_type == 'C':
      X0 = self.transform[csys_id][2] 
      Z = self.transform[csys_id][4]
      if dof == 4: text = self.make_eq(Z,val,ngrp_name)
      else:
        nset = self.ngrp[self.ngrp_dict[ngrp_name][0]]
        if 'GENERATE' in self.ngrp_dict[ngrp_name][1]:
          s, e, i = nset[0], nset[1], nset[2]
          nset = list(range(s, e+1, i))
        for n_id in nset:
          node = self.nodes_coord[self.node_order[n_id]]
          t = (node - X0)@Z
          R = node - (X0+t*Z); R = normalize(R)
          if (R == np.zeros(3)).all(): continue
          if dof == 2: text += self.make_eq(R,val,n_id)
          elif dof == 3:
            th = np.cross(Z,R); text += self.make_eq(th,val,n_id)
    
    elif sys_type == 'S':
      O = self.transform[csys_id][2]
      Z0 = self.transform[csys_id][4]
      nset = self.ngrp[self.ngrp_dict[ngrp_name][0]]
      if 'GENERATE' in self.ngrp_dict[ngrp_name][1]:
        s, e, i = nset[0], nset[1], nset[2]
        nset = list(range(s, e+1, i))
      for n_id in nset:
        node = self.nodes_coord[self.node_order[n_id]]
        R = node - O; R = normalize(R)
        if (R == np.zeros(3)).all(): continue
        
        z = Z0 - R@Z0 * R; z = normalize(z)
        if (z == np.zeros(3)).all(): continue
        
        if dof == 2: text += self.make_eq(R,val,n_id)
        elif dof == 3:
          th = np.cross(z,R); text += self.make_eq(th,val,n_id)
        elif dof == 4:
          text += self.make_eq(z,val,n_id)

    return text

  ################################
  ###### Get Rotated !CLOAD ######
  ################################
  def get_rot_cload(self, data, csys_id):
    ngrp_name = data[0]
    dof = int(data[1])+1
    val = float(data[2])

    def calc_cload(vec, name):
      temp = []; f = val * vec
      for out_dof, v in enumerate(f):
        if np.abs(v) < 1e-8: continue
        temp.append([name,f'{out_dof+1}',f'{v}'])
      return temp

    csys = self.transform[csys_id]
    cload = []
    if csys[0] == 'R': vec = csys[dof]; cload += calc_cload(vec, ngrp_name)

    elif csys[0] == 'C':
      X0 = csys[2]; Z = csys[4]
      if dof == 4: vec = csys[dof]; cload += calc_cload(vec, ngrp_name)
      else:
        nset = self.ngrp[self.ngrp_dict[ngrp_name][0]]
        if 'GENERATE' in self.ngrp_dict[ngrp_name][1]:
          s, e, i = nset[0], nset[1], nset[2]
          nset = list(range(s, e+1, i))
        for n_id in nset:
          node = self.nodes_coord[self.node_order[n_id]]
          t = (node - X0)@Z
          R = node - (X0+t*Z); R = normalize(R)
          if (R == np.zeros(3)).all(): continue
          if   dof == 2: vec = R
          elif dof == 3: vec = np.cross(Z,R)
          cload += calc_cload(vec, str(n_id))
    
    elif csys[0] == 'S':
      O = csys[2]; Z0 = csys[4]
      nset = self.ngrp[self.ngrp_dict[ngrp_name][0]]
      if 'GENERATE' in self.ngrp_dict[ngrp_name][1]:
        s, e, i = nset[0], nset[1], nset[2]
        nset = list(range(s, e+1, i))
      for n_id in nset:
        node = self.nodes_coord[self.node_order[n_id]]
        R = node - O; R = normalize(R)
        if (R == np.zeros(3)).all(): continue
        
        z = Z0 - R@Z0 * R; z = normalize(z)
        if (z == np.zeros(3)).all(): continue
        
        if dof == 2: vec = R
        elif dof == 3: vec = np.cross(z,R)
        elif dof == 4: vec = z
        cload += calc_cload(vec, str(n_id))


    return cload

  def make_eq(self,vec,val,ngrp):
    n_cf = np.where(abs(vec)>1e-8)[0]
    if len(n_cf) == 1:
      if val != 0.0: val *= vec[n_cf[0]]
      self.eq2bc.append([f'{ngrp}',f'{n_cf[0]+1}',f'{n_cf[0]+1}',f'{val}'])
      return ''

    if abs(vec[0]) > 1e-8: val = val/vec[n_cf][0]
    text  = '!EQUATION\n'
    text += f'{len(n_cf)},{val}\n'
    for dof_id in n_cf: text += f'{ngrp},{dof_id+1},{vec[dof_id]},'
    text.rstrip(','); text += '\n'
    return text
  
  def del_empty_cond(self):
    del_obj = [self.boundary, self.cload, self.dload]
    for obj in del_obj:
      del_list = []
      for i, cond in enumerate(obj):
        if len(cond) < 2: del_list.insert(0,i); continue
        if len(cond[1]) < 1: del_list.insert(0,i)
      for del_index in del_list:
        del obj[del_index]

  ############################
  ##### Result Converter #####
  ############################
  def model_write(self):
    text = ''
    ## nodes
    node_ids = []
    for ids in self.node_id: node_ids += ids

    text += f'    2C{len(node_ids):>30}                                     1\n'
    for i, coord in enumerate(self.nodes_coord):
      nid = node_ids[i]
      text += f' -1{nid:>10}'+''.join(f'{c:12.5E}' for c in coord)+'\n'
    text += ' -3\n'

    ## elems
    elem_dict = {'8':1, '6':2, '4':3, '10':6}

    elems = []
    for elem in self.elems: elems += [list(map(int,text.split(','))) for text in elem]
    
    text += f'    3C{len(elems):>30}                                     1\n'
    for elem in elems:
      etype = elem_dict[str(len(elem)-1)]
      text += f' -1{elem[0]:>10}{etype:>5}    0    1\n'
      text += ' -2'+''.join(f'{e:>10}' for e in elem[1:])+'\n'
    text += ' -3\n'

    return text

  def read_resfile(self, texts):
    self.nflags = []; self.eflags = []
    # get time
    flag = False
    for dline, text in enumerate(texts):
      if '*data' in text: break
      if 'TOTALTIME' in text: flag = True; continue
      if flag: self.ttime = float(text); continue
    
    # data lines
    texts = texts[dline+1:]

    nn, ne = map(int, texts.pop(0).split())
    nres, eres = map(int, texts.pop(0).split())
    
    # node result
    nums = []
    for i in range(int(nres//10+1)): nums += list(map(int, texts.pop(0).split()))
    names = []
    for i in range(nres): names.append(texts.pop(0))

    self.get_result_dict(nums,names,0)
    self.extract_result(0)
    self.allocate_resarray(self.nnode,0)

    for i in range(nn):
      nid = int(texts.pop(0))
      idx = self.node_order[nid]
      data = []
      for j in range(sum(nums)//5+1):
        data += list(map(float, texts.pop(0).split()))
      self.get_data(data,0,idx)

    # elem result
    nums = []
    for i in range(int(eres//10+1)): nums += list(map(int, texts.pop(0).split()))
    names = []
    for i in range(eres): names.append(texts.pop(0))

    self.get_result_dict(nums,names,1)
    self.extract_result(1)
    self.allocate_resarray(self.nelem,1)
    
    for i in range(ne):
      eid = int(texts.pop(0))
      idx = self.elem_order[eid]
      data = []
      for j in range(sum(nums)//5+1):
        data += list(map(float, texts.pop(0).split()))
      self.get_data(data,1,idx)

  def write_frd(self,path,step):
    f = open(path, 'a', encoding='utf-8')
    f.write(self.frd_head(step,self.nnode))
    for j, name in enumerate(self.nflags):
      res_name = self.res_dict[name]
      f.write(' -4  ')
      f.write(f'{res_name:<8}    4    1\n')
      h = res_name[0]
      for i in range(3): f.write(f' -5  {h}{i+1}          1    2{i+1:>5}    0\n')
      f.write(' -5  ALL         1    2    0    0    1ALL\n')

      for i, data in enumerate(self.node_res):
        nid = self.gl_node_id[i]
        f.write(f' -1  {nid:>8}')
        f.write(''.join(f'{d:12.5E}' for d in data[3*j:3*(j+1)])+'\n')
      f.write(' -3\n')

    f.write(self.frd_head(step,self.nnode))
    for j, name in enumerate(self.eflags):
      res_name = self.res_dict[name]
      f.write(' -4  ')
      f.write(f'{res_name:<8}    6    1\n')
      h = res_name[0]
      if h == 'T': h = 'E'
      temp1 = ['XX','YY','ZZ','XY','YZ','ZX']
      temp2 = [[1,1],[2,2],[3,3],[1,2],[2,3],[3,1]]
      for i in range(6):
        f.write(f' -5  {h}{temp1[i]}         1    4{temp2[i][0]:>5}{temp2[i][1]:>5}\n')

      for i, data in enumerate(self.elem_res):
        eid = self.gl_elem_id[i]
        f.write(f' -1  {eid:>8}')
        f.write(''.join(f'{d:12.5E}' for d in data[6*j:6*(j+1)])+'\n')
      f.write(' -3\n')
    
    f.close()

