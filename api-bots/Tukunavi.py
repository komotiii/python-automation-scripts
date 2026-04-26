import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pyshorteners
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    url: str
    save_file: Path
    discord_bot_token: str
    discord_channel_id: str
    check_interval_seconds: int
    retry_interval_seconds: int
    request_timeout_seconds: int
    skip_initial_notify: bool
    notify_on_start: bool


def _get_int_env(name: str, default_value: int) -> int:
    raw = os.getenv(name, str(default_value)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer: {raw}") from exc

    if value <= 0:
        raise ValueError(f"Environment variable {name} must be greater than 0: {value}")
    return value


def _get_bool_env(name: str, default_value: bool) -> bool:
    raw = os.getenv(name, str(default_value).lower()).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    raw_save_file = os.getenv("TSUKUNAVI_SAVE_FILE", "data/posts.json").strip()
    if raw_save_file.replace("\\", "/").startswith("api-bots/"):
        raw_save_file = raw_save_file.split("/", 1)[1] if "/" in raw_save_file else "data/posts.json"

    return Settings(
        url=os.getenv(
            "TSUKUNAVI_URL",
            "https://tsukunavi.com/forums/forum/%E3%82%A2%E3%83%AB%E3%83%90%E3%82%A4%E3%83%88/",
        ).strip(),
        save_file=Path(raw_save_file),
        discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", "").strip(),
        discord_channel_id=os.getenv("TSUKUNAVI_DISCORD_CHANNEL_ID", "").strip(),
        check_interval_seconds=_get_int_env("TSUKUNAVI_CHECK_INTERVAL_SECONDS", 300),
        retry_interval_seconds=_get_int_env("TSUKUNAVI_RETRY_SECONDS", 30),
        request_timeout_seconds=_get_int_env("TSUKUNAVI_REQUEST_TIMEOUT_SECONDS", 20),
        skip_initial_notify=_get_bool_env("TSUKUNAVI_SKIP_INITIAL_NOTIFY", True),
        notify_on_start=_get_bool_env("TSUKUNAVI_NOTIFY_ON_START", True),
    )

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

shortener = pyshorteners.Shortener()


def ensure_save_file_exists(save_file: Path) -> None:
    save_file.parent.mkdir(parents=True, exist_ok=True)
    if not save_file.exists():
        save_file.write_text("[]", encoding="utf-8")


def fetch_posts(url: str, timeout_seconds: int) -> List[Dict[str, str]]:
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        topics = soup.select(".bbp-topic-title")
        reply_counts = soup.select(".bbp-topic-reply-count")

        posts: List[Dict[str, str]] = []
        for title, reply in zip(topics, reply_counts):
            title_element = title.select_one("a")
            if title_element:
                posts.append({
                    "title": title_element.text.strip(),
                    "url": title_element["href"],
                    "replies": reply.text.strip(),
                })
        return posts
    except requests.exceptions.RequestException as exc:
        logging.error("Error fetching posts: %s", exc)
        return []


def save_posts_to_json(save_file: Path, posts: List[Dict[str, str]]) -> None:
    with save_file.open("w", encoding="utf-8") as file:
        json.dump(posts, file, ensure_ascii=False, indent=4)


def load_previous_posts(save_file: Path) -> List[Dict[str, str]]:
    try:
        with save_file.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
            return loaded if isinstance(loaded, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def check_new_or_changed_posts(
    posts: List[Dict[str, str]],
    previous_posts: List[Dict[str, str]],
) -> List[Tuple[str, Dict[str, str]]]:
    titles_previous = {post["title"]: post for post in previous_posts}
    titles_current = {post["title"]: post for post in posts}
    new_or_changed_posts: List[Tuple[str, Dict[str, str]]] = []
    for title, post in titles_current.items():
        prev_post = titles_previous.get(title)
        if prev_post is None and post["replies"] == "1":
            new_or_changed_posts.append(("新規", post))
        elif prev_post is not None and post["replies"] != prev_post["replies"]:
            new_or_changed_posts.append(("既存", post))
    return new_or_changed_posts


def _send_via_bot_channel(bot_token: str, channel_id: str, message: str, timeout_seconds: int) -> bool:
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }
    payload = {"content": message[:1900]}
    response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    return True


def send_discord_notify(settings: Settings, message: str) -> None:
    try:
        if settings.discord_bot_token and settings.discord_channel_id:
            _send_via_bot_channel(
                settings.discord_bot_token,
                settings.discord_channel_id,
                message,
                settings.request_timeout_seconds,
            )
            return

        logging.error(
            "Discord通知設定が不足しています。"
            "DISCORD_BOT_TOKEN と TSUKUNAVI_DISCORD_CHANNEL_ID を設定してください。"
        )
    except requests.exceptions.RequestException as exc:
        logging.error("Error sending Discord notification: %s", exc)


def fetch_latest_post_from_url(url: str, timeout_seconds: int) -> str:
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        loop_items = soup.select("[class^='loop-item-']")
        if not loop_items:
            return ""
        latest_post = loop_items[-1]
        content_element = latest_post.select_one(".bbp-reply-content")
        if content_element is None:
            return ""
        content = content_element.text.strip()
        return content
    except requests.exceptions.RequestException as exc:
        logging.error("Error fetching latest post from %s: %s", url, exc)
        return ""


def shorten_url(url: str) -> str:
    try:
        return shortener.tinyurl.short(url)
    except Exception as exc:
        logging.warning("Failed to shorten URL. Using original URL: %s", exc)
        return url


def main() -> None:
    settings = load_settings()
    save_file = settings.save_file if settings.save_file.is_absolute() else BASE_DIR / settings.save_file

    ensure_save_file_exists(save_file)
    bot_ready = bool(settings.discord_bot_token and settings.discord_channel_id)
    if not bot_ready:
        logging.warning(
            "Discord通知先が未設定です。"
            "DISCORD_BOT_TOKEN と TSUKUNAVI_DISCORD_CHANNEL_ID を設定してください。"
        )
    elif settings.notify_on_start:
        send_discord_notify(
            settings,
            "Tukunavi監視を開始しました。\n"
            f"URL: {settings.url}\n"
            f"監視間隔: {settings.check_interval_seconds}秒",
        )

    while True:
        try:
            posts = fetch_posts(settings.url, settings.request_timeout_seconds)
            if not posts:
                logging.info("No posts to process. Retrying...")
                time.sleep(settings.retry_interval_seconds)
                continue

            previous_posts = load_previous_posts(save_file)
            if settings.skip_initial_notify and not previous_posts:
                save_posts_to_json(save_file, posts)
                logging.info("Initialized post cache without notifications.")
                time.sleep(settings.check_interval_seconds)
                continue

            new_or_changed_posts = check_new_or_changed_posts(posts, previous_posts)
            for status, post in new_or_changed_posts:
                logging.info("%s post detected: %s", status, post["title"])
                content = fetch_latest_post_from_url(post["url"], settings.request_timeout_seconds)
                short_url = shorten_url(post["url"])
                message = f"Tsukunavi: {status} {post['title']} \n{short_url} \n{content}"
                send_discord_notify(settings, message)

            save_posts_to_json(save_file, posts)
            logging.info("Done")
            time.sleep(settings.check_interval_seconds)
        except KeyboardInterrupt:
            logging.info("Stopped by user.")
            break
        except Exception as exc:
            logging.exception("Unexpected error in main loop: %s", exc)
            time.sleep(settings.retry_interval_seconds)

if __name__ == "__main__":
    main()
