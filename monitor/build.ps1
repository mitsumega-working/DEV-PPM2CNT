# -*- coding: utf-8 -*-
mkdir BUILD -Force; cd BUILD

$libraryPath = python -c "import ttkthemes; print(ttkthemes.__path__[0])"
$cores=8
nuitka `
  ..\..\monitor.py `
  --job=$cores `
  --onefile `
  --enable-plugin=tk-inter `
  --include-data-dir=$libraryPath=ttkthemes\ `
  --include-data-files=..\icon.ico=icon.ico `
  --windows-icon-from-ico=..\icon.ico `
  --windows-product-version="1.1" `
  --windows-company-name="Structia"

Copy-Item -Recurse monitor.exe ..\..\tools

cd ..