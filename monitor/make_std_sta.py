# -*- coding: utf-8 -*-
import os
from datetime import datetime
import tkinter as tk

######### + num_cutback, now_residual, increment
# ff = open('FSTR.sta', encoding='utf-8')
header  = '╔═════════════════════════════════════════╦════════╦══════════════════════════╗\n'
header += '║             SUMMARY OF STEP             ║ NUM of ║     INFO OF CONTACTS     ║\n'
header += '║ STEP │   TIME   │  dTIME  │CVG│ITER│CONT║  ITER  ║ CONT │ FREE │ MOVE │TOTAL║\n'
header += '║━━━━━━│━━━━━━━━━━│━━━━━━━━━│━━━│━━━━│━━━━║━━━━━━━━║━━━━━━│━━━━━━│━━━━━━│━━━━━║\n'
footer  = '╚══════╧══════════╧═════════╧═══╧════╧════╩════════╩══════╧══════╧══════╧═════╝\n'

texts = [header]
restart = []

data = {'step':0,'iter':0,'piter':0,'ctime':0.0,'btime':0.0,'sum_iter':0,'sum_cont':0 \
        , 'MOVE':0, 'FREE':0, 'CONT':0, 'TOTAL':0, 'cvg_flag':'S', 'cont_cvg': False}
flag = ''

def sta_init(sta_text, test_exe=False):
  global data, f, flag
  flag = ''
  os.makedirs('STA', exist_ok=True)
  now = datetime.now()
  path = 'STA/NEW_FSTR_{0:%m_%d_%H.%M.%S}.sta'.format(now)
  if test_exe: path = 'STA/NEW_FSTR.sta'
  f = open(path, 'w', encoding='utf-8')
  f.write(header); f.flush()
  sta_text.insert(tk.END, header)
  data = {'step':0,'iter':0,'piter':0,'ctime':0.0,'btime':0.0,'sum_iter':0,'sum_cont':0 \
        , 'MOVE':0, 'FREE':0, 'CONT':0, 'TOTAL':0, 'cvg_flag':'S', 'cont_cvg': False}

def control_std_sta(line, sta_text):
  global data, flag
  flag = judge_line(line)
  text = ''

  if flag == 'T': text = get_substep(line); f.write(text); f.flush()
  elif flag == 'R':
    flag = ''
    if data['cont_cvg']: text = proc_cstep(); f.write(text); f.flush()
    else: print_curr_res(sta_text); return
  elif flag == 'END': text = proc_end(); flag = '!END'
  elif flag == '!END': text = line; f.write(text); f.flush()
  else: return
  end_idx = sta_text.index("end-1c linestart")
  sta_text.delete(end_idx,"end-1c"); sta_text.insert(tk.END, text)
  
  # sta_text.see(tk.END)


def judge_line(line):
  global data, flag
  if 'current_time=' in line: flag = 'T'
  elif '- Residual(' in line:
    flag = 'R'
    temp = line.replace(' - Residual(', '').split()
    niter = int(temp[0].rstrip(')'))
    if data['iter'] >= niter:
      data['cont_cvg'] = True
      data['sum_iter'] += data['iter']
      data['sum_cont'] += 1
    else: data['cont_cvg'] = False
    data['piter'] = data['iter']; data['iter'] = niter
    data['res'] = float(temp[-2]); data['reres'] = float(temp[-1])

  elif 'contact' in line: 
    if 'move' in line:   data['MOVE'] += 1
    elif 'free' in line: data['FREE'] += 1
    elif 'total' in line:data['TOTAL'] = int(line.split()[-1])
    else:                data['CONT'] += 1
  elif '='*36 in line and flag != '!END': flag = 'END'
  elif flag == '!END': return flag
  elif 'time increment is increased' in line: data['cvg_flag'] = 'I'
  elif 'time increment is decreased' in line: data['cvg_flag'] = 'D'
  else: flag = ''
  return flag

def get_substep(line):
  global data
  temp = line.split()
  step = int(temp[1].rstrip(','))
  dtime = float(temp[-1])
  ctime = float(temp[-3].rstrip(',')) + dtime

  if data['step'] >= step: data['CVG'] = 'C'
  else: data['CVG'] = data['cvg_flag']

  data['sum_iter'] += data['iter']
  data['sum_cont'] += 1
  data['cvg_flag'] = 'S'
  
  sta_line  = ''
  if step == 1 and data['CVG'] != 'C': pass
  else:
    data['piter'] += 1; sta_line = proc_cstep()
    sta_line += '╟{:^6d}┼{:^10.5f}┼{:^7.3e}┼{:^3s}┼{:^4d}┼{:^4d}'.format( \
      data['step'],data['ctime'],data['dtime'],data['CVG'],data['sum_iter'],data['sum_cont'])
    sta_line += '╫────────╫──────┼──────┼──────┼─────╢\n'

  data['dtime'] = dtime; data['ctime'] = ctime; data['step'] = step
  
  data['iter'] = 0; data['sum_iter'] = 0; data['sum_cont'] = 0
  data['MOVE'] = 0; data['FREE'] = 0; data['CONT'] = 0

  return sta_line

def proc_cstep():
  global data
  sta_line  = '║{:6s}│{:10s}│{:9s}│{:3s}│{:4s}│{:4s}'.format(' ',' ',' ',' ',' ',' ')
  sta_line += '║{:^8d}║{:^6d}│{:^6d}│{:^6d}│{:^5d}║\n'.format( \
    data['piter'], data['CONT'], data['FREE'], data['MOVE'], data['TOTAL'])
  data['MOVE'] = 0; data['FREE'] = 0; data['CONT'] = 0

  return sta_line

def print_curr_res(sta):
  if sta.__class__.__name__ == 'noGUI_dummy': return
  global data
  c = "blue"
  if data['res'] > 1e3: c = "red"
  elif data['res'] < 1e-3: c = "limegreen"
  text = '╟{:^6d}┼{:^10.5f}┼  R: {:^6.3e}   RR: {:^6.3e}  ║                          ║'.format(\
    data['step'],data['ctime'],data['res'], data['reres'])
  
  end_idx = sta.index("end-1c linestart"); sta.delete(end_idx,"end-1c")
  sta.insert(end_idx, text)
  end_idx = float(end_idx)
  sta.tag_add(c, f'{end_idx:^.0f}.21', f'{end_idx:^.0f}.33')

def proc_end():
  data['sum_iter'] += data['iter']
  data['sum_cont'] += 1
  data['cvg_flag'] = 'S'

  sta_line = proc_cstep()
  sta_line += '╟{:^6d}┼{:^10.5f}┼{:^7.3e}┼{:^3s}┼{:^4d}┼{:^4d}'.format( \
  data['step'],data['ctime'],data['dtime'],data['CVG'],data['sum_iter'],data['sum_cont'])
  sta_line += '╫────────╫──────┼──────┼──────┼─────╢\n'
  sta_line += footer
  f.write(sta_line)

  return sta_line