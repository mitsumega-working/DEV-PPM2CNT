# -*- coding: utf-8 -*-

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
 NSTRESS, ON
 NSTRAIN, ON
 DISP, ON
 REACTION, ON
 ESTRESS, OFF
 ESTRAIN, OFF
'''
    
    self.dat_format = f'''\
## Converted from inp file by inp2cnt
# for solver
#
!MESH, NAME=fstrMSH, TYPE=HECMW-ENTIRE
 {self.title}.msh
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
    
  def make_step_form(self):
    steps_format = ''
    for step in self.steps:
      steps_format += f'!STEP,INC_TYPE={step['TYPE']},SUBSTEPS={step['SUBSTEPS']},MAXITER=25,CONVERG=1.0e-4,CONVERG_DDISP=1.0e-4,MAXRES=1.0e5'
      if len(self.cpairs) != 0: steps_format += ',MAXCONTITER=10'
      if step['TYPE'] == 'AUTO': steps_format += ',AUTOINCPARAM=AP1'
      steps_format += f'\n {step['increment']}\n'
      if 'BOUNDARY' in step: steps_format += f' BOUNDARY,{step['BOUNDARY']}\n'
      if 'LOAD' in step: steps_format += f' LOAD,{step['LOAD']}\n'
      # if 'CONTACT' in step: steps_format += f' CONTACT,{step['CONTACT']}\n'
      if len(self.cpairs) != 0: steps_format += ' CONTACT, 1\n'
      if len(self.tied) != 0: steps_format += ' CONTACT, 2\n'
      steps_format += f' LOAD,99\n' #spring
    
    steps_format = f'''\
!AUTOINC_PARAM, NAME=AP1
 0.75, 10, 20, 5, 1
 1.25,  5, 15, 3, 1
 0.25,  5
{steps_format}\
### Solver Control
!SOLVER,METHOD=MUMPS
'''
    return steps_format

