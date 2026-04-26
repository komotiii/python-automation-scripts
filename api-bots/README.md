# api-bots

Discord、Google Calendar、Webスクレイピングなどの外部APIを使った個人用自動化ボット集です。

## ディレクトリ構成

```text
api-bots/
  .env.example
  .gitignore
  PlayingBOT.py
  Tukunavi.py
  requirements.txt
  data/
    .gitkeep
```

## クイックスタート

1. 依存パッケージをインストールします。

```bash
pip install -r api-bots/requirements.txt
```

2. ローカル用の環境変数ファイルを作成します。

```bash
copy api-bots\.env.example api-bots\.env
```

3. `api-bots/.env` に必要な値を設定します。

4. ボットを実行します。

```bash
python api-bots/PlayingBOT.py
# または
python api-bots/Tukunavi.py
```

## PlayingBOT.py

Discord上の対象ユーザーのアクティビティ変化を監視し、開始・終了タイミングをGoogle Calendarに記録します。

### PlayingBOT 必須環境変数

- `DISCORD_BOT_TOKEN`
- `DISCORD_TARGET_USER_ID`
- `DISCORD_TARGET_GUILD_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_CALENDAR_ID`

### PlayingBOT 任意環境変数

- `PLAYING_BOT_LOG_FILE`（既定値: `logs/activity_log.txt`）
- `PLAYING_BOT_CHECK_INTERVAL_SECONDS`（既定値: `60`）
- `PLAYING_BOT_TIMEZONE`（既定値: `Asia/Tokyo`）

### PlayingBOT 事前設定

- Discord Developer Portalで `SERVER MEMBERS INTENT` と `PRESENCE INTENT` を有効化してください。
- 監視対象を記録するGoogle Calendarを、サービスアカウントのメールアドレスに共有してください。

## Tukunavi.py

Tsukunaviフォーラムの更新を監視し、Discordに通知します。

### Tukunavi 必須環境変数

- `DISCORD_BOT_TOKEN`
- `TSUKUNAVI_DISCORD_CHANNEL_ID`

### Tukunavi 任意環境変数

- `TSUKUNAVI_URL`
- `TSUKUNAVI_SAVE_FILE`（既定値: `data/posts.json`）
- `TSUKUNAVI_CHECK_INTERVAL_SECONDS`（既定値: `300`）
- `TSUKUNAVI_RETRY_SECONDS`（既定値: `30`）
- `TSUKUNAVI_REQUEST_TIMEOUT_SECONDS`（既定値: `20`）
- `TSUKUNAVI_SKIP_INITIAL_NOTIFY`（既定値: `true`）
- `TSUKUNAVI_NOTIFY_ON_START`（既定値: `true`）

`TSUKUNAVI_NOTIFY_ON_START=true` の場合、起動時に「監視開始」をDiscordへ通知します。

## Public公開前チェック

- `.env` がGit管理対象に入っていないことを確認する
- APIトークンやWebhook URLをソースコードへ直書きしない
- サービスアカウント鍵JSONをリポジトリ外または `.gitignore` 対象にする
- 過去に秘密情報を漏えいした可能性がある場合は、公開前に必ずローテーションする
