@echo off
setlocal

echo ComfyUI Client�̍X�V���J�n���܂�...

REM comfyui-client�t�H���_�����݂��邩�`�F�b�N
if exist ".git" (
    echo ���[�J���̕ύX�����Z�b�g���܂�...
    git reset --hard
    if %errorlevel% neq 0 (
        echo git reset --hard �Ɏ��s���܂����B
        pause
        exit /b 1
    )

    echo �ŐV�ł��_�E�����[�h���܂�...
    git pull
    if %errorlevel% neq 0 (
        echo git pull �Ɏ��s���܂����B
        pause
        exit /b 1
    )

    echo �X�V���������܂����B
) else (
    echo Git���|�W�g����������܂���B�V�K�C���X�g�[������ꍇ�� scripts/install.bat ���g�p���Ă��������B
    pause
    exit /b 1
)

echo �X�V���������܂����B
pause
endlocal
