# weather-tools

OpenWeather の予報データを Google Calendar に同期する Python スクリプトです。

## プロジェクト概要

このツールは、天気予報を3時間単位のカレンダーイベントとして登録し、
日々の予定確認をカレンダー中心に統合するために作成しました。

## ファイル構成

- `Openweather.py`: メイン実装
- `.env.example`: 環境変数テンプレート
- `requirements.txt`: 依存ライブラリ

## セットアップ

1. 依存パッケージをインストールします。

```bash
pip install -r requirements.txt
```

2. 環境変数ファイルを作成します。

```bash
copy .env.example .env
```

3. `.env` に APIキーと認証ファイルパスを設定します。

## 必須環境変数

- `OPENWEATHER_API_KEY`
- `OPENWEATHER_LAT`
- `OPENWEATHER_LON`
- `GOOGLE_CALENDAR_OAUTH_CREDENTIALS`
- `GOOGLE_CALENDAR_TOKEN_FILE`
- `GOOGLE_CALENDAR_ID`

## 任意環境変数

- `WEATHER_TIMEZONE`（既定値: `Asia/Tokyo`）
- `WEATHER_FORECAST_HOURS`（既定値: `24`）
- `WEATHER_SLOT_HOURS`（既定値: `3`）
- `WEATHER_REPLACE_AFTER_HOURS`（既定値: `3`）
- `WEATHER_EVENT_PREFIX`（既定値: `[Weather]`）
- `OPENWEATHER_LANG`（既定値: `en`）

## 実行

```bash
python Openweather.py
```

予報時間を一時的に変えて実行する場合:

```bash
python Openweather.py --hours 12
```


## 実装上のポイント

- OpenWeather の3時間予報を取得し、イベント化
- 既存イベントは `WEATHER_EVENT_PREFIX` で識別し、他予定を誤削除しない
- OAuthトークンは初回認証後に自動保存し、再実行時は再利用

## セキュリティ注意

- `.env`、`token.json`、`credentials.json` は Git に含めない
- APIキーやトークンを公開してしまった場合は必ず再発行する
