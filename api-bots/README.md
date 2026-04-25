# api-bots

This folder contains automation bots used in my personal workflow.

## PlayingBOT.py

`PlayingBOT.py` tracks a target Discord member's current activity and creates a Google Calendar event when the activity changes or ends.

### Why this version is safe to publish

- No secrets are hardcoded in source code.
- Discord and Google settings are loaded from environment variables.
- Local service account key files are referenced by path and kept out of git.

### Setup

1. Install dependencies.

```bash
pip install -r api-bots/requirements.txt
```

2. Copy the environment template and set your values.

```bash
copy api-bots\.env.example api-bots\.env
```

`PlayingBOT.py` loads `api-bots/.env` automatically.

3. Configure Discord bot intents.

- Enable `SERVER MEMBERS INTENT` and `PRESENCE INTENT` in the Discord Developer Portal.

4. Share your target Google Calendar with the service account email.

5. Run the bot.

```bash
python api-bots/PlayingBOT.py
```

### Required environment variables

- `DISCORD_BOT_TOKEN`
- `DISCORD_TARGET_USER_ID`
- `DISCORD_TARGET_GUILD_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_CALENDAR_ID`

### Optional environment variables

- `PLAYING_BOT_LOG_FILE` (default: `logs/activity_log.txt`)
- `PLAYING_BOT_CHECK_INTERVAL_SECONDS` (default: `60`)
- `PLAYING_BOT_TIMEZONE` (default: `Asia/Tokyo`)

### Security note

If a token has ever been committed or shared, revoke and reissue it before making the repository public.

## Tukunavi.py

Tukunavi monitor checks forum post updates and sends notifications to Discord.

### Setup

1. Install dependencies.

```bash
pip install -r api-bots/requirements.txt
```

2. Set environment values in api-bots/.env.

Required:

- DISCORD_WEBHOOK_URL

Optional:

- TSUKUNAVI_URL
- TSUKUNAVI_SAVE_FILE (default: api-bots/data/posts.json)
- TSUKUNAVI_CHECK_INTERVAL_SECONDS (default: 300)
- TSUKUNAVI_RETRY_SECONDS (default: 30)
- TSUKUNAVI_REQUEST_TIMEOUT_SECONDS (default: 20)

3. Run.

```bash
python api-bots/Tukunavi.py
```
