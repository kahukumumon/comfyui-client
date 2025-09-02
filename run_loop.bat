@echo off
setlocal

REM 移動: このバッチがあるフォルダ
cd /d "%~dp0"

REM Python 検出（py ランチャ優先）
where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set PY=python
  ) else (
    echo Python が見つかりません。https://www.python.org/ からインストールしてください。
    pause
    exit /b 1
  )
)

echo 依存関係をインストールしています...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo 依存インストールに失敗しました。
  pause
  exit /b 1
)

echo loop.py を起動します...
%PY% loop.py
set EXITCODE=%errorlevel%

echo 終了コード: %EXITCODE%
pause
exit /b %EXITCODE%


