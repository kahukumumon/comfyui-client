@echo off
setlocal

REM ���݂̃X�N���v�g�̂���f�B���N�g���Ɉړ�
cd /d "%~dp0"

REM Python �̊��`�F�b�N
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

echo �ˑ��֌W�̃C���X�g�[�����J�n���܂�...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo �ˑ��֌W�̃C���X�g�[���Ɏ��s���܂����B
  pause
  exit /b 1
)

echo extract_model_loader_groups.py �����s���܂�...
%PY% extract_model_loader_groups.py
set EXITCODE=%errorlevel%

echo �I���R�[�h: %EXITCODE%
pause
exit /b %EXITCODE%
