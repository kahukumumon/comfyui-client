# ComfyUI Client バッチ処理ツール

ComfyUIで画像をバッチ処理するための便利ツールです。指定したフォルダ内の画像を順次ComfyUIに送信し、自動処理を行います。

## 🚀 インストール

1. [install_update.bat](https://raw.githubusercontent.com/kahukumumon/comfyui-client/refs/heads/main/install_update.bat) を右クリックして「名前を付けて保存」を選択
2. 任意の場所（例: C:\comfyui-client）に保存して実行
3. 自動的にGitHubから最新版がダウンロードされます

## 🔄 更新

1. [install_update.bat](https://raw.githubusercontent.com/kahukumumon/comfyui-client/refs/heads/main/install_update.bat) を再度実行するだけ
2. 自動的に最新版に更新されます

## 📋 必要な環境

- **Windows 10以上**
- **Python 3.10以上**（インストールされていない場合は自動で案内されます）
- **ComfyUI** が `http://127.0.0.1:8188` で起動していること

## ⚙️ 初期設定

### 1. ComfyUIの準備
- ComfyUIを起動し、`http://127.0.0.1:8188` でアクセスできる状態にしてください
- ワークフローを作成したら、右上の「Export (API)」からJSONファイルをエクスポートしてください

### 2. 設定ファイルの編集
`config.json` をテキストエディタで開いて以下を設定してください：

```json
{
  "input_dir": "C:\\Path\\To\\Input\\Images",
  "workflow": "base.json"
}
```

- `input_dir`: 処理したい画像（PNG形式）を入れるフォルダ
- `workflow`: ComfyUIからエクスポートしたJSONファイル名

### 3. ワークフローの準備
- ComfyUIで作成したワークフローを `base.json` として保存
- `LoadImagesFromFolderKJ` ノードを使用していることを確認してください

## 🎯 使用方法

### 0. モデルローダーのグループ情報抽出
ワークフローからモデルローダーグループの情報を抽出する場合：
- 最新の`00-I2v_ImageToVideo.json` をrun_extract.batと同じフォルダにコピーする。
- `run_extract.bat` をダブルクリックして実行
- `00-I2v_ImageToVideo.json` からグループ情報を抽出し、`out/model_loader_groups.json` と `trigger_folder_names.txt` を生成します

### 1. 画像の準備
- `input_dir` に処理したいPNG画像を配置

### 1.5. フォルダ名による条件分岐（オプション）
ワークフロー内で特定のモデルグループを有効/無効にしたい場合：

**フォルダ名のルール：**
- フォルダ名やファイルパスにキーワードを含めることで、対応するモデルグループを有効化
- 例: `input/realistic/image001.png` → "realistic"キーワードで対応グループを有効化
- キーワードが含まれない場合、そのグループのノードはワークフローから自動的に除去されます

**使用可能なキーワード：**
- `run_extract.bat`実行後に生成される `trigger_folder_names.txt` に記載
- 各行が使用可能なキーワード（トリガー）に対応

**例:**
```
realistic, photo
anime, illustration
portrait, face
```

上記の場合、`realistic`または`photo`がパスに含まれる画像はリアリスティック系のモデルグループを使用し、それ以外の画像はアニメ系モデルグループを使用します。

### 2. ComfyUIの起動確認
- ComfyUIが `http://127.0.0.1:8188` で起動していることを確認
- ワークフローが正しく読み込まれていることを確認

### 3. 実行
- `run_loop.bat` をダブルクリックして実行
- 自動的に依存関係がインストールされ、処理が開始されます

### 4. 処理の流れ
1. スクリプトが `input_dir` の画像を順次読み込み
2. 10秒ごとにComfyUIのキュー状況を確認
3. キューが空いている場合のみ、次の画像を処理
4. すべての画像が処理されるまで繰り返し

## 🔧 トラブルシューティング

### Pythonが見つからない場合
```
Python が見つかりません。https://www.python.org/ からインストールしてください。
```
- Python 3.10以上の公式版をインストールしてください

### ComfyUIに接続できない場合
- ComfyUIが `127.0.0.1:8188` で起動しているか確認してください
- ポート番号を変更している場合は `loop.py` の `COMFY` 定数を編集してください

### 処理が進まない場合
- ComfyUIのキューに未処理のジョブが溜まっていないか確認してください
- ComfyUIの処理が長時間かかっている可能性があります

## 📁 ファイル構成

```
comfyui-client/
├── install_update.bat      # インストール/更新用スクリプト
├── run_loop.bat           # メイン実行用バッチファイル
├── run_extract.bat        # モデルグループ抽出用バッチファイル
├── loop.py               # メイン処理スクリプト
├── extract_model_loader_groups.py  # モデルグループ抽出スクリプト
├── config.json           # 設定ファイル
├── base.json            # ワークフロー例
├── 00-I2v_ImageToVideo.json  # ワークフロー定義ファイル（オプション）
├── requirements.txt      # Python依存パッケージ
├── out/
│   └── model_loader_groups.json  # 抽出されたモデルグループ情報
├── trigger_folder_names.txt     # 使用可能なフォルダ名キーワード
└── README.md            # このファイル
```

## 💡 ヒント

- 初回実行時は `run_loop.bat` を使用すると便利です（自動で依存関係をインストール）
- 画像の処理順序はファイル名の順番です
- 処理中にスクリプトを強制終了しても、ComfyUIの処理は継続されます

## 📞 サポート

問題が発生した場合は、以下の情報を確認してください：
1. ComfyUIのバージョン
2. Pythonのバージョン
3. エラーメッセージの詳細
4. `config.json` の設定内容

---

**注意**: このツールはComfyUIの公式ツールではありません。ComfyUIのAPI仕様変更により動作しなくなる可能性があります。
