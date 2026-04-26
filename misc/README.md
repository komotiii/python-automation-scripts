# misc

日常の補助作業をまとめた小さな自動化スクリプト群です。

## プロジェクト概要

PC起動時の複数スクリプト起動と、15分おきの定時リマインドという、日常で繰り返し発生する作業を軽量に自動化する。

## ファイル構成

- `Auto_startup.py`: 複数Pythonスクリプトを順番に起動するランチャー
- `Tutturu15m.py`: 15分おきのリマインダー通知
- `.env.example`: `Tutturu15m.py` 用の設定テンプレート

## 使い方

### Auto_startup.py の使い方

```bash
python Auto_startup.py
```

起動対象を変えたい場合は、環境変数 `STARTUP_PROGRAMS` に `;` 区切りでパスを指定します。

### Tutturu15m.py の使い方

```bash
python Tutturu15m.py
```

## 設定項目

### Auto_startup.py の設定

- `STARTUP_PROGRAMS`: 起動するPythonスクリプトのパス一覧（`;` 区切り）

### Tutturu15m.py の設定

- `TUTTURU_SOUND_FILE`: 再生する音声ファイルのパス
- `TUTTURU_CHECK_INTERVAL_SECONDS`: 確認間隔（既定値: `1`）
- `TUTTURU_SNOOZE_SECONDS`: 通知後の待機時間（既定値: `890`）

`TUTTURU_SOUND_FILE` が未設定、またはファイルが見つからない場合は、Windows のシステムビープで通知します。

## 実装上のポイント

- 起動ランチャーはGUIを固めないようバックグラウンドスレッドで動作
- 出力は画面に残し、起動状況と終了状態を色付きで可視化
- リマインダーは重複通知を避けるため、同一時刻キーで再通知を抑制
