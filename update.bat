@echo off
setlocal

echo ComfyUI Clientの更新を開始します...

REM comfyui-clientフォルダが存在するかチェック
if exist ".git" (
    echo ローカルの変更をリセットします...
    git reset --hard
    if %errorlevel% neq 0 (
        echo git reset --hard に失敗しました。
        pause
        exit /b 1
    )

    echo 最新版をダウンロードします...
    git pull
    if %errorlevel% neq 0 (
        echo git pull に失敗しました。
        pause
        exit /b 1
    )

    echo 更新が完了しました。
) else (
    echo Gitリポジトリが見つかりません。新規インストールする場合は scripts/install.bat を使用してください。
    pause
    exit /b 1
)

echo 更新が完了しました。
pause
endlocal
