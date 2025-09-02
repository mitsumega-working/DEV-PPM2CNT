# -*- coding: utf-8 -*-
import numpy as np
import re
from glob import glob
from os.path import join

class res2frd:
  def __init__(self, inp_path, header):
    self.inp_path = inp_path
    self.header = header
    self.ttime = 0
    self.totalstep = 1
    self.res_dict =  {'DISPLACEMENT':'DISP','REACTION_FORCE':'FORC',
                      'NodalSTRAIN':'TOSTRAIN','NodalSTRESS':'STRESS'}

  def get_mesh(self):
    f = open(join(self.inp_path.rstrip('.inp'),'include/node.msh'))
    ntexts = f.readlines(); f.close()
    f = open(join(self.inp_path.rstrip('.inp'),'include/elem.msh'))
    etexts = f.readlines(); f.close()
    
    self.nodes_coord = []; self.node_id = []
    self.elems = [];      self.elem_id = []
    self.etypes = []

    for text in ntexts:
      if '!' in text: continue
      self.node_id.append(int(text.split(',')[0]))
      x,y,z = map(float, text.split(',')[1:])
      self.nodes_coord.append(np.array([x,y,z]))

    for text in etexts:
      if '!' in text: continue
      temp = list(map(int, text.split(',')))
      self.elem_id.append(temp[0])
      self.elems.append(temp[1:])

    max_num = max(self.node_id)+1
    self.node_order = np.full(max_num,-1)
    for i, node in enumerate(self.node_id): self.node_order[node] = i
    self.nnode = len(self.node_id)

    max_num = max(self.elem_id)+1
    self.elem_order = np.full(max_num,-1)
    for i, elem in enumerate(self.elem_id): self.elem_order[elem] = i
    self.nelem = len(self.elem_id)

  def make_frd(self):
    with open(self.inp_path.replace('.inp','.frd'), 'w') as f:
      f.write(self.frd_header())
      f.write(self.model_write())
      f.close()

    resdir_list = glob(join(self.inp_path.rstrip('.inp'), "fstrRES/STEP*"))
    resdir_list = sorted(resdir_list, key=lambda x: int(re.search(r"STEP(\d+)", x).group(1)))

    for resdir in resdir_list:
      nstep = int(re.search(r"STEP(\d+)", resdir).group(1))
      if nstep == 0: continue
      resfile_list = glob(join(resdir, "job.res.*"))
      n_res, e_res = self.read_resfiles(resfile_list)
      self.write_frd(self.inp_path.replace('.inp','.frd'),n_res,e_res,nstep)

  def model_write(self):
    text = ''
    ## nodes
    text += f'    2C{self.nnode:>30}                                     1\n'
    for i, coord in enumerate(self.nodes_coord):
      nid = self.node_id[i]
      text += f' -1{nid:>10}'+''.join(f'{c:12.5E}' for c in coord)+'\n'
    text += ' -3\n'

    ## elems
    elem_dict = {'8':1, '6':2, '4':3, '10':6}

    text += f'    3C{self.nelem:>30}                                     1\n'
    for i, elem in enumerate(self.elems):
      etype = elem_dict[str(len(elem))]
      text += f' -1{self.elem_id[i]:>10}{etype:>5}    0    1\n'
      if etype == 6:
        elem = [elem[i] for i in [0,1,2,3,6,4,5,7,8,9]]
      text += ' -2'+''.join(f'{e:>10}' for e in elem)+'\n'
    text += ' -3\n'

    return text

  def frd_header(self):
    import time
    header = f'''\
    1C
    1U{self.header}
    1UDATE              {time.strftime('%m.%d.%Y',time.localtime())}
    1UTIME              {time.strftime('%H:%M:%S',time.localtime())}\n'''
    return header

  def read_resfiles(self, resfile_list):
    init_flag = True
    n_results = np.zeros(0); e_results = np.zeros(0)
    self.nres_nums = []; self.nres_names = []
    self.eres_nums = []; self.eres_names = []
    for file in resfile_list:
      f = open(file); texts = f.readlines(); f.close()
      if init_flag: self.ttime = float(texts[texts.index('TOTALTIME\n')+1])
      for i, text in enumerate(texts):
        if '*data' in text: break
      texts = texts[i+1:]
      nn, ne = map(int, texts.pop(0).split())

      nres, eres = map(int, texts.pop(0).split())
      nres_flag = (nres == 0); eres_flag = (eres == 0)
      if not nres_flag:
        if init_flag:
          for i in range(int(nres//10+1)): self.nres_nums += list(map(int, texts.pop(0).split()))
          for i in range(nres): self.nres_names.append(texts.pop(0).rstrip('\n'))
          n_results = np.full([self.nnode,sum(self.nres_nums)+1],np.nan)
        else:
          for i in range(int(nres//10+1)): texts.pop(0)
          for i in range(nres): texts.pop(0)
        data_lines = texts[:((sum(self.nres_nums)-1)//5+2)*nn]; del texts[:((sum(self.nres_nums)-1)//5+2)*nn]
        n_all_data = list(map(float, re.findall(r'-?\d+\.\d+(?:[Ee][+-]?\d+)?|\d+', ''.join(data_lines))))
        n_all_data = np.array(n_all_data).reshape((nn, -1))
      
      ##### !!! frd can not read elemental results !!!
      # if not eres_flag:
      #   if init_flag:
      #     for i in range(int(eres//10+1)): self.eres_nums += list(map(int, texts.pop(0).split()))
      #     for i in range(eres): self.eres_names.append(texts.pop(0).rstrip('\n'))
      #     e_results = np.full([self.nelem,sum(self.eres_nums)+1],np.nan)
      #   else:
      #     for i in range(int(eres//10+1)): texts.pop(0)
      #     for i in range(eres): texts.pop(0)
      #   data_lines = texts
      #   e_all_data = list(map(float, re.findall(r'-?\d+\.\d+(?:[Ee][+-]?\d+)?|\d+', ''.join(data_lines))))
      #   e_all_data = np.array(e_all_data).reshape((ne, -1))

      init_flag = False

      for i in range(nn):
        nid = int(n_all_data[i,0])
        idx = self.node_order[nid]
        n_results[idx,:] = n_all_data[i,:]

      # for i in range(ne):
      #   eid = int(e_all_data[i,0])
      #   idx = self.elem_order[eid]
      #   e_results[idx,:] = e_all_data[i,:]
    
    return n_results, e_results

  def write_frd(self,path,n_res,e_res,nstep):
    f = open(path, 'a', encoding='utf-8')
    for j, name in enumerate(self.nres_names):
      if not name in self.res_dict: continue
      f.write(self.step_head(self.nnode,nstep))
      res_name = self.res_dict[name]
      
      if self.nres_nums[j] == 3:
        f.write(' -4  ')
        f.write(f'{res_name:<8}    4    1\n')
        h = res_name[0]
        for i in range(3): f.write(f' -5  {h}{i+1}          1    2{i+1:>5}    0\n')
        f.write(' -5  ALL         1    2    0    0    1ALL\n')

        end = sum(self.nres_nums[:j+1]); start = end - self.nres_nums[j]
        datas = n_res[:,np.r_[0,start+1:end+1]]
        datas = np.hstack([ -1 * np.ones((datas.shape[0], 1)), datas ])

        np.savetxt(f, datas, fmt="%3d%10d%12.5E%12.5E%12.5E")
        f.write(' -3\n')
      
      elif self.nres_nums[j] == 6:
        f.write(' -4  ')
        f.write(f'{res_name:<8}    6    1\n')
        h = res_name[0]
        if h == 'T': h = 'E'
        temp1 = ['XX','YY','ZZ','XY','YZ','ZX']
        temp2 = [[1,1],[2,2],[3,3],[1,2],[2,3],[3,1]]
        for i in range(6):
          f.write(f' -5  {h}{temp1[i]}         1    4{temp2[i][0]:>5}{temp2[i][1]:>5}\n')


        end = sum(self.nres_nums[:j+1]); start = end - self.nres_nums[j]
        datas = n_res[:,np.r_[0,start+1:end+1]]
        datas = np.hstack([ -1 * np.ones((datas.shape[0], 1)), datas ])

        np.savetxt(f, datas, fmt="%3d%10d%12.5E%12.5E%12.5E%12.5E%12.5E%12.5E")
        f.write(' -3\n')

    ##### !!! frd can not read elemental results !!!
    # for j, name in enumerate(self.eres_names):

    f.close()

  def step_head(self,nnode,step):
    text = f'''\
    1PSTEP              {self.totalstep:>12}{step:>12}           1          
  100CL  {100+step}{self.ttime:12.9f}{nnode:>12}                     0{step:>5}           1\n'''
    self.totalstep += 1
    return text

# def read_resfile(self, texts):
#   self.nflags = []; self.eflags = []
#   # get time
#   flag = False
#   for dline, text in enumerate(texts):
#     if '*data' in text: break
#     if 'TOTALTIME' in text: flag = True; continue
#     if flag: self.ttime = float(text); continue
  
#   # data lines
#   texts = texts[dline+1:]

#   nn, ne = map(int, texts.pop(0).split())
#   nres, eres = map(int, texts.pop(0).split())
  
#   # node result
#   nums = []
#   for i in range(int(nres//10+1)): nums += list(map(int, texts.pop(0).split()))
#   names = []
#   for i in range(nres): names.append(texts.pop(0))

#   self.get_result_dict(nums,names,0)
#   self.extract_result(0)
#   self.allocate_resarray(self.nnode,0)

#   for i in range(nn):
#     nid = int(texts.pop(0))
#     idx = self.node_order[nid]
#     data = []
#     for j in range(sum(nums-1)//5+1):
#       data += list(map(float, texts.pop(0).split()))
#     self.get_data(data,0,idx)

#   # elem result
#   nums = []
#   for i in range(int(eres//10+1)): nums += list(map(int, texts.pop(0).split()))
#   names = []
#   for i in range(eres): names.append(texts.pop(0))

#   self.get_result_dict(nums,names,1)
#   self.extract_result(1)
#   self.allocate_resarray(self.nelem,1)
  
#   for i in range(ne):
#     eid = int(texts.pop(0))
#     idx = self.elem_order[eid]
#     data = []
#     for j in range(sum(nums)//5+1):
#       data += list(map(float, texts.pop(0).split()))
#     self.get_data(data,1,idx)




  



  # def convert_result(self):
  #   self.status.insert(tk.END,'結果を変換します...\n'); self.status.see(tk.END)
  #   if self.nogui: print('結果を変換します...')
  #   try: self.make_frd(); out_text = '変換が完了しました'
  #   except Exception as e:
  #     out_path = os.path.join(self.dir_path,splitext(basename(self.inp_path))[0])
  #     write_err_damp(out_path,self.dt_now,traceback.format_exc(limit=None),self.inp_error_log)        
  #     out_text = f'結果変換でエラーが発生しました.\nerror.logを確認してください.'
  #   if not self.nogui: self.status.insert(tk.END,out_text+'\n'); self.status.see(tk.END)
  #   else: print(out_text)



  # def allocate_resarray(self,num,mode):#,cres):
  #   if not self.newstep: return
  #   tgt_flag = [self.nflags,self.eflags][mode]
  #   dnum = [3,6][mode]
  #   nres = len(tgt_flag)*dnum

  #   if mode == 0: #node
  #     self.node_res = np.full([num,nres],0.0)
  #   elif mode == 1: #elem
  #     self.elem_res = np.full([num,nres],0.0)
  #   # self.cont_res = np.full([nnode,cres],0.0)

  # def get_result_dict(self,nums,results,mode):
  #   target = [self.nres_dict, self.eres_dict][mode]

  #   count = 0
  #   for i, result in enumerate(results):
  #     target[result] = count
  #     count += nums[i]
  
  # def extract_result(self, mode):
  #   n_names = ['DISPLACEMENT','REACTION_FORCE']
  #   e_names = ['ElementalSTRAIN','ElementalSTRESS']
  #   names = [n_names,e_names][mode]
  #   tgt_flag = [self.nflags,self.eflags][mode]
  #   tgt_dict = [self.nres_dict, self.eres_dict][mode]

  #   for name in names:
  #     if name in tgt_dict: tgt_flag.append(name)

  # def get_data(self,data,mode,idx):
  #   tgt_flag = [self.nflags,self.eflags][mode]
  #   tgt_dict = [self.nres_dict, self.eres_dict][mode]
  #   tgt_res = [self.node_res, self.elem_res][mode]
  #   num = [3,6][mode]
    
  #   for i, name in enumerate(tgt_flag):
  #     start = tgt_dict[name]
  #     tgt_res[idx,num*i:num*(i+1)] = np.array(data[start:start+num])
