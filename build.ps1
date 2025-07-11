# -*- coding: utf-8 -*-
$libraryPath = python -c "import ttkthemes; print(ttkthemes.__path__[0])"
$cores=3
nuitka `
  ..\PrePoSTR.py `
  --job=$cores `
  --standalone `
  --windows-console-mode=disable `
  --enable-plugin=tk-inter `
  --include-data-dir=$libraryPath=ttkthemes\ `
  --include-data-files=..\icon.ico=icon.ico `
  --include-data-files=..\file.png=file.png `
  --windows-icon-from-ico=..\icon.ico 

if (Test-Path -Path "PrePoSTR\") {
  Write-Host "The destination file already exists. Deleting: PrePoSTR"
  Remove-Item -Path "PrePoSTR\" -Force -Recurse
}

Copy-Item -Recurse PrePoSTR.dist PrePoSTR\
Copy-Item -Recurse ..\FrontISTR-DEV250506 .\PrePoSTR
Copy-Item ..\open_pvtu.py .\PrePoSTR
7z.exe a ..\PrePoSTR_v1.0.zip PrePoSTR\* #7zipが使える場合はこちらの方が圧縮・解凍ともに高速
# Compress-Archive -Path .\PrePoSTR -DestinationPath ..\PrePoSTR_vX.X.zip -Force
Remove-Item -Recurse PrePoSTR
