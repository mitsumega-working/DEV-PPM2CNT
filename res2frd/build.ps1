# -*- coding: utf-8 -*-
mkdir BUILD -Force; cd BUILD

$cores=6
nuitka `
  ..\res2frd.py `
  --job=$cores `
  --onefile `
  --windows-console-mode=disable `
  --windows-product-version="1.1" `
  --windows-company-name="Structia"

Copy-Item -Recurse res2frd.exe ..\..\tools

cd ..