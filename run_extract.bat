@echo off
setlocal

REM 現在のスクリプトのあるディレクトリに移動
cd /d "%~dp0"

REM Python の環境チェック
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

echo 依存関係のインストールを開始します...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo 依存関係のインストールに失敗しました。
  pause
  exit /b 1
)

echo extract_model_loader_groups.py を実行します...
%PY% extract_model_loader_groups.py
set EXITCODE=%errorlevel%

echo 終了コード: %EXITCODE%
pause
exit /b %EXITCODE%
