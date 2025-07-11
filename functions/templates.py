# -*- coding: utf-8 -*-
from tkinter import StringVar, IntVar, BooleanVar
import os

class templates():
  def __init__(self, title):
    self.title = title
    self.model_files = ''; self.control_files = ''; self.step = ''
    self.tied_cparam = f'''\
!CONTACT_PARAM, NAME=CPARAM_TIED
 1.0e-4, 5.0e-3, 1.0e-2, 1.0e-4
 1.0e0, -1.0e-6, 1.0,   -1.0e-8, 1.5
!CONTACT_ALGO,TYPE=SLAGRANGE
'''
    self.tpoint_format = '!TIME_POINTS, NAME=TP1\n '

  def make_template(self):
    #msh_file
    self.msh_format = f'''\
!INCLUDE, INPUT=include/node.msh
!INCLUDE, INPUT=include/elem.msh
!INCLUDE, INPUT=include/MATSEC.msh
{self.model_files}'''

    #cnt_file
    self.cnt_format = f'''\
## Converted from inp file by inp2cnt
!VERSION
 5
!SOLUTION, TYPE=STATIC, NONLINEAR
#### Include Files
!INCLUDE, INPUT=include/OUTPUT.msh
!INCLUDE, INPUT=include/SPRING.msh
{self.control_files}\
##### STEP
!INCLUDE, INPUT=include/STEP.msh
### Post Control
!VISUAL, method=PSR
!surface_num=1
!surface 1
!output_type=BIN_VTK
!END
'''

    #contact
    self.cparam_format = f'''\
!CONTACT_PARAM, NAME=CPARAM1
 1.0e-4,  5.0e-3,  1.0e-2,  1.0e-4
 1.0e-6, -1.0e-6,  1.0,    -1.0e-8,  1.05
'''

    self.contact_format = f'''\
!CONTACT_ALGO,TYPE=SLAGRANGE
!CONTACT, GRPID=1,INTERACTION=FSLID, CONTACTPARAM=CPARAM1
'''
    
    #spring
    self.spring_format = f'''\
!SPRING, follow=YES, GRPID=99
 ALL, 1, -1.0e-3
 ALL, 2, -1.0e-3
 ALL, 3, -1.0e-3
'''

    #output
    self.output_text = f'''\
 DISP,ON
 TEMP,ON
 NSTRESS,ON
 ESTRESS,ON
 NSTRAIN,ON
 ESTRAIN,ON
 EMISES,ON
 NMISES,ON
 PRINC_NSTRESS,ON
 PRINC_ESTRESS,ON
 CONTACT_STATE,ON
 CONTACT_NTRACTION,ON
 CONTACT_FTRACTION,ON
 CONTACT_NFORCE,ON
 CONTACT_FRICTION,ON
 MATERIAL_ID,ON
 SECTION_ID,ON
 REACTION,ON
 TEMP,OFF
 NODE_ID,OFF
 ELEM_ID,OFF
 PL_ESTRAIN,OFF'''

    self.output_format = f'''\
!WRITE,VISUAL
!OUTPUT_VIS
{self.output_text}
!WRITE,RESULT
!OUTPUT_RES
 NMISES, OFF
 NSTRESS, OFF
 DISP, ON
 REACTION, ON
 ESTRESS, ON
 ESTRAIN, ON
'''

  def frd_header(self, date_now):
    header = f'''\
    1C
    1U{self.heading}
    1UDATE              {date_now:%m.%d.%Y}
    1UTIME              {date_now:%H:%M:%S}
'''
    return header

class EDITOR_templates():
  def __init__(self, exepath):
    self.tnum_var = StringVar(value='4')
    self.pnum_var = StringVar(value='4')

    self.part_select = BooleanVar(value=False)
    self.exepath = os.path.realpath(exepath)

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

  ### hecmw_part_ctrl.dat file ###
  def write_part_dat(self):
    self.make_ctrl_files()
    ### .dat file ###
    f = open('hecmw_ctrl.dat','w', encoding='utf-8')
    f.write(self.dat_format); f.close()

    if self.part_select.get():
      f = open('hecmw_part_ctrl.dat','w', encoding='utf-8')
      f.write(self.pdat_format); f.close()
