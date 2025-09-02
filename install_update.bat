@echo off
setlocal

echo ComfyUI Clientのインストール/更新を開始します...

REM comfyui-clientフォルダが存在するかチェック
if not exist "comfyui-client" (
    echo comfyui-clientフォルダが見つからないため、クローンします...
    git clone https://github.com/kahukumumon/comfyui-client.git
    if %errorlevel% neq 0 (
        echo クローンに失敗しました。
        pause
        exit /b 1
    )
    echo クローンが完了しました。
) else (
    echo comfyui-clientフォルダが見つかったため、更新します...
    cd comfyui-client
    if %errorlevel% neq 0 (
        echo フォルダへの移動に失敗しました。
        pause
        exit /b 1
    )

    echo git reset --hard を実行します...
    git reset --hard
    if %errorlevel% neq 0 (
        echo git reset --hard に失敗しました。
        pause
        exit /b 1
    )

    echo git pull を実行します...
    git pull
    if %errorlevel% neq 0 (
        echo git pull に失敗しました。
        pause
        exit /b 1
    )

    cd ..
    echo 更新が完了しました。
)

echo 処理が完了しました。
pause
endlocal
