# desktop-monitoring

Windows の画面・ウィンドウ・クリップボード・ネットワークを軽量に監視する Python スクリプト集です。

## プロジェクト概要

このフォルダでは、日常のデスクトップ作業で繰り返し発生する確認作業を自動化しています。
単発のスクリーンショット取得から、クリップボード保存、アクティブウィンドウ記録、ネットワーク可視化までを小さく分けて実装しています。

ポートフォリオとしては次の点を示せます。

- デスクトップ自動化: 画面・クリップボード・入力行動の監視
- 実運用を意識した保存設計: 日付別保存、ウィンドウ名付き保存、CSV出力
- 常駐処理の扱い: ループ処理、重複検知、ログ保存

## ファイル構成

- `active_window.py`: アクティブウィンドウの変化をログ化
- `CamScreen.py`: Webカメラと画面全体を定期保存
- `CtrlV_img.py`: クリップボード画像を保存
- `CtrlV_txt.py`: クリップボード文字列を Excel に保存
- `Networkspeed.py`: ネットワーク速度をグラフ化しCSV保存
- `screenshot.py`: 単発のスクリーンショット取得
- `Typing_monitor.py`: タイピング結果をクリップボードから集計
- `.env.example`: 設定テンプレート

## セットアップ

1. 依存ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

1. 環境変数ファイルを作成します。

```bash
copy .env.example .env
```

## 主な設定項目

### active_window.py

- `ACTIVE_WINDOW_LOG_FILE`: アクティブウィンドウのログ保存先
- `ACTIVE_WINDOW_POLL_INTERVAL_SECONDS`: 監視間隔

### CamScreen.py

- `CAMSCREEN_CAMERA_DIR`: Webカメラ画像の保存先
- `CAMSCREEN_SCREEN_DIR`: スクリーンショットの保存先
- `CAMSCREEN_INTERVAL_SECONDS`: 取得間隔

### CtrlV_img.py

- `CLIPBOARD_IMAGE_DIR`: 画像保存先
- `CLIPBOARD_IMAGE_POLL_INTERVAL_SECONDS`: 監視間隔

### CtrlV_txt.py

- `CLIPBOARD_TEXT_DIR`: 文字列を保存するExcelの出力先
- `CLIPBOARD_TEXT_POLL_INTERVAL_SECONDS`: 監視間隔

### Networkspeed.py

- `NETWORK_SPEED_CSV`: 速度ログCSVの保存先
- `NETWORK_SPEED_INTERVAL_MS`: サンプリング間隔

### Typing_monitor.py

- `TYPING_MONITOR_CSV_PATH`: タイピング結果CSVの保存先
- `TYPING_MONITOR_SESSION_SECONDS`: 集計するセッション時間
- `TYPING_MONITOR_POLL_INTERVAL_SECONDS`: 監視間隔

## 使い方

```bash
python target.py
```
