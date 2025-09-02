# -*- coding: utf-8 -*-

class ExpectedError(Exception):
  pass # base class


class KeyWordError(ExpectedError):
  pass # keyword error class

def etype_error(log):
  return f'要素タイプエラー\n行{log[0]}:{log[1]}'

def mesh_error(keyword):
  if keyword == '*MATERIAL':
    return f'{keyword}が見つかりません.\n材料特性が設定されたか確認してください.'
  else:
    return f'{keyword}が見つかりません.\nメッシュが作成されたか確認してください.'


class ConvertError(ExpectedError):
  pass # convert error class

def trans_error(tf_type):
  return f'局所座標系の変換エラー\n対応していない座標系タイプです:"{tf_type}"'

def write_err_damp(dirpath,now,log,clog):
  path = dirpath+'/error.log'
  f = open(path, 'w', encoding='utf-8')
  f.write(f'### ERROR OCCURRED {now} ###')
  f.write('\n---- ERROR LOG ----\n')
  f.write(f'{log}')
  f.write('\n---- ERROR LOG END ----\n')
  if not '*END' in clog[1].upper():
    f.write('\n*** LAST CONVERTED LINE ***\n')
    f.write(f'l.{clog[0]}: {clog[1]}')
    f.write('\n*** END ***\n')
  f.close()