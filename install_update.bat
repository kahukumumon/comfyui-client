@echo off
setlocal

echo ComfyUI Client�̃C���X�g�[��/�X�V���J�n���܂�...

REM comfyui-client�t�H���_�����݂��邩�`�F�b�N
if not exist ".git" (
    echo comfyui-client�t�H���_��������Ȃ����߁A�N���[�����܂�...
    git init
    git remote add origin https://github.com/kahukumumon/comfyui-client
    git fetch
    git checkout -t origin/main
    if %errorlevel% neq 0 (
        echo �N���[���Ɏ��s���܂����B
        pause
        exit /b 1
    )
    echo �N���[�����������܂����B
) else (
    echo comfyui-client�t�H���_�������������߁A�X�V���܂�...
    cd comfyui-client
    if %errorlevel% neq 0 (
        echo �t�H���_�ւ̈ړ��Ɏ��s���܂����B
        pause
        exit /b 1
    )

    echo git reset --hard �����s���܂�...
    git reset --hard
    if %errorlevel% neq 0 (
        echo git reset --hard �Ɏ��s���܂����B
        pause
        exit /b 1
    )

    echo git pull �����s���܂�...
    git pull
    if %errorlevel% neq 0 (
        echo git pull �Ɏ��s���܂����B
        pause
        exit /b 1
    )

    cd ..
    echo �X�V���������܂����B
)

echo �������������܂����B
pause
endlocal
