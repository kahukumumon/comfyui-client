@echo off
setlocal

echo ComfyUI Client�̐V�K�C���X�g�[�����J�n���܂�...

REM comfyui-client�t�H���_�����݂��邩�`�F�b�N
if not exist ".git" (
    echo comfyui-client�t�H���_��������Ȃ����߁A���������܂�...
    git init
    git remote add origin https://github.com/kahukumumon/comfyui-client
    git fetch
    git checkout -t origin/main
    if %errorlevel% neq 0 (
        echo �C���X�g�[���Ɏ��s���܂����B
        pause
        exit /b 1
    )
    echo �C���X�g�[�����������܂����B
) else (
    echo ����Git���|�W�g�������݂��܂��B�X�V����ꍇ�� update.bat ���g�p���Ă��������B
    pause
    exit /b 1
)

echo �C���X�g�[�����������܂����B
pause
endlocal
