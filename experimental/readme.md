# experimental

API連携、音声、可視化などの試作コードを置く実験フォルダです。

## プロジェクト概要

- 音声アナウンス（VOICEVOX + 天気 + カレンダー）
- Flask API での予定配信
- Google Timeline JSON の可視化
- 音声入力 / 文章生成の試行

## ファイル構成

- `Morning_Voice.py`: 朝の音声アナウンス（天気・予定・ニュース）
- `Openweather.py`: OpenWeather 予報の簡易テキスト化
- `CalendarFlask.py`: Google Calendar の予定を返す Flask API
- `timeline_viewer.py`: Google Timeline JSON からテキスト/HTMLレポート生成
- `Audio_txt.py`: 音声入力 + 会話モデル応答の試作

## セットアップ

1. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

1. 環境変数ファイルを作成

```bash
copy .env.example .env
```

## 主要スクリプト

### Morning_Voice.py

- VOICEVOX へテキストを渡して音声合成
- OpenWeather 予報を取得して読み上げ文を生成
- Flask 経由で当日予定を取得して読み上げ

実行:

```bash
python Morning_Voice.py
```

### CalendarFlask.py

Google Calendar の予定を JSON で返すローカルAPIです。

実行:

```bash
python CalendarFlask.py
```

エンドポイント:

- `/events`: すべての対象カレンダーの予定
- `/events/<calendar_name>`: 指定カレンダーの予定

### Openweather.py

OpenWeather API の予報から、当日用の要約文を生成します。

実行:

```bash
python Openweather.py
```

### timeline_viewer.py

Google Timeline Edits JSON を解析して、テキストとHTMLレポートを出力します。

実行:

```bash
python timeline_viewer.py --input-json "Timeline Edits.json" --output-dir "timeline_output"
```

## 今後の拡張候補

- 天気・温湿度・デバイス状態を統合した音声レポート
- 定時ルーチンとの連携アナウンス
- 複数データソースの非同期取得
