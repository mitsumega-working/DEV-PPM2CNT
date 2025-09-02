# -*- coding: utf-8 -*-
mkdir BUILD -Force ; cd BUILD

$cores=4
nuitka `
  ..\PrePoSTR.py `
  --job=$cores `
  --standalone `
  --nofollow-import-to=tkinter `
  --nofollow-import-to=inp_converter `
  --nofollow-import-to=editor `
  --nofollow-import-to=monitor `
  --windows-product-version="1.1" `
  --windows-company-name="Structia" `
  --windows-icon-from-ico=..\icon.ico 

if (Test-Path -Path "PrePoSTR\") {
  Write-Host "The destination file already exists. Deleting: PrePoSTR"
  Remove-Item -Path "PrePoSTR\" -Force -Recurse
}
else{
  mkdir PrePoSTR
}

Copy-Item -Recurse PrePoSTR.dist PrePoSTR\
Copy-Item -Recurse ..\FrontISTR-DEV250506 .\PrePoSTR
Copy-Item -Recurse ..\open_pvtu.py .\PrePoSTR
Copy-Item -Recurse ..\tools .\PrePoSTR
7z.exe a ..\PrePoSTR_v1.1.zip PrePoSTR\* #7zipが使える場合はこちらの方が圧縮・解凍ともに高速
# # Compress-Archive -Path .\PrePoSTR -DestinationPath ..\PrePoSTR_vX.X.zip -Force
# Remove-Item -Recurse PrePoSTR

cd ..
