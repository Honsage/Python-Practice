# Primarius Bot

Primarius is a simple Telegram bot created for practice bots writing.

## Telegram Link
Link to Primarius: https://t.me/primarius_bot

## Build & Run
If you want to launch your version of this bot, follow these steps:

1. Download the codebase. E.g. clone this repository:
```shell
git clone https://github.com/Honsage/Primarius-Bot
```

2. Register new bot in Telegram. Obtain Telegram Bot API token and save it to `.env` file in the root of repository as follows:
```text
API_TOKEN=<your_token_there>
```

3. Create and activate Python Virtual Environment.

 * Windows:
```shell
python -m venv venv
source venv\Scripts\activate
```

 * Unix:
```shell
python3 -m venv venv
./venv/bin/activate
```

4. Install dependencies.

```shell
pip install -r requirements.txt
```

5. Now your environment is ready and you can launch the bot.

 * Windows
```shell
python primarius.py
```

 * Unix
```shell
python3 primarius.py
```
