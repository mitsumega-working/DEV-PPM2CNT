# -*- coding: utf-8 -*-
from tkinter import StringVar, BooleanVar

class EDITOR_templates():
  def __init__(self, title):
    self.title = title
    self.tnum_var = StringVar(value='4')
    self.pnum_var = StringVar(value='4')

    self.part_select = BooleanVar(value=False)

  def get_exe_command(self):
    self.command = []
    if self.part_select.get(): self.command += ['mpiexec.exe','-np', self.pnum_var.get()]
    self.command += ['fistr1.exe','-t',self.tnum_var.get()]

  def make_ctrl_files(self):
    if self.part_select.get():
      ctrl_head = f'''\
## Converted from inp file by inp2cnt
# for partitioner
#
!MESH, NAME=part_in,TYPE=HECMW-ENTIRE
 {self.title}.msh
!MESH, NAME=part_out,TYPE=HECMW-DIST
 {self.title}_{self.pnum_var.get()}
#
# for solver
#
!MESH, NAME=fstrMSH, TYPE=HECMW-DIST
 {self.title}_{self.pnum_var.get()}'''
      
      self.pdat_format = f'''\
!PARTITION,TYPE=NODE-BASED,METHOD=PMETIS,DOMAIN={self.pnum_var.get()},DEPTH=2
'''
      
    else:
      ctrl_head = f'''\
## Converted from inp file by inp2cnt
# for solver
#
!MESH, NAME=fstrMSH, TYPE=HECMW-ENTIRE
 {self.title}.msh'''

    self.dat_format = f'''\
{ctrl_head}
!CONTROL, NAME=fstrCNT
 {self.title}.cnt
!RESTART, NAME=restart_out, IO=INOUT
 restart.in
!RESULT, NAME=fstrRES, IO=OUT
 {self.title}.res
!RESULT, NAME=vis_out, IO=OUT
 {self.title}_vis
!SUBDIR, ON
'''
