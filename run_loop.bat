@echo off
setlocal

REM �ړ�: ���̃o�b�`������t�H���_
cd /d "%~dp0"

REM Python ���o�ipy �����`���D��j
where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set PY=python
  ) else (
    echo Python ��������܂���Bhttps://www.python.org/ ����C���X�g�[�����Ă��������B
    pause
    exit /b 1
  )
)

echo �ˑ��֌W���C���X�g�[�����Ă��܂�...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo �ˑ��C���X�g�[���Ɏ��s���܂����B
  pause
  exit /b 1
)

echo loop.py ���N�����܂�...
%PY% loop.py
set EXITCODE=%errorlevel%

echo �I���R�[�h: %EXITCODE%
pause
exit /b %EXITCODE%


