# calendar-tools

Google Calendar を使った日常タスクを自動化する Python スクリプト集です。

## プロジェクト概要

このフォルダは、以下の3つの業務を分離して実装しています。

- `Add_event_cmd.py`: カレンダーに予定を追加
- `Clear_event.py`: 指定期間の未来予定を一括削除
- `Sum_calendar.py`: カレンダーごとの利用時間を集計・可視化

## 技術スタック

- Python
- Google Calendar API
- google-api-python-client / google-auth-oauthlib
- matplotlib

## セットアップ

1. 依存パッケージをインストールします。

```bash
pip install -r requirements.txt
```

2. 環境変数ファイルを作成します。

```bash
copy .env.example .env
```

3. 必要な認証ファイルを用意します。

## 必要ファイル

### OAuthモード（予定追加 / 予定削除）

- `credentials.json`: Google Cloud で作成した OAuth クライアント情報
- `token.json`: 初回認証時に自動生成されるトークン

### Service Accountモード（利用時間集計）

- `service_account.json`: サービスアカウント鍵
- `calendar_list.txt`: `表示名,calendar_id` 形式の一覧ファイル

`calendar_list.example.txt` をテンプレートとして使えます。

## 使い方

### 1. 予定を追加

```bash
python Add_event_cmd.py --summary "Gym" --start "2026-04-27 19:00" --minutes 60
```

### 2. 未来予定を一括削除（例: 今から5日分）

```bash
python Clear_event.py --days 5 --calendar-id primary
```

### 3. 利用時間を日次集計

```bash
python Sum_calendar.py --date 2026-04-25
```

## 設計上のポイント

- 追加・削除は OAuth を利用し、ユーザー権限で安全に操作
- 集計は read-only スコープの Service Account を利用
- 引数未指定時は `.env` の値を既定として利用可能

## セキュリティ注意

- `credentials.json`、`token.json`、`service_account.json` はGitに含めない
- 本番運用では最小権限スコープを使用する
