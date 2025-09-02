# -*- coding: utf-8 -*-
mkdir BUILD -Force; cd BUILD

$cores=6
nuitka `
  ..\..\inp_converter.py `
  --job=$cores `
  --onefile `
  --windows-product-version="1.1" `
  --windows-company-name="Structia"

Copy-Item -Recurse inp_converter.exe ..\..\tools

cd ..