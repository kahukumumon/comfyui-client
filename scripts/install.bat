@echo off
setlocal

echo ComfyUI Clientの新規インストールを開始します...

REM comfyui-clientフォルダが存在するかチェック
if not exist ".git" (
    echo comfyui-clientフォルダが見つからないため、初期化します...
    git init
    git remote add origin https://github.com/kahukumumon/comfyui-client
    git fetch
    git checkout -t origin/main
    if %errorlevel% neq 0 (
        echo インストールに失敗しました。
        pause
        exit /b 1
    )
    echo インストールが完了しました。
) else (
    echo 既にGitリポジトリが存在します。更新する場合は update.bat を使用してください。
    pause
    exit /b 1
)

echo インストールが完了しました。
pause
endlocal
