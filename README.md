# BriefForge Bot

Bilingual (UK/EN) interactive Telegram bot built with **Python 3.15** and **Aiogram 3.x** that gathers project requirements, calculates a complexity index, estimates timelines, and generates a structured technical brief.

## Features
- Auto-detection of user language (`UK` / `EN`) with instant toggle button
- Interactive step-by-step brief builder with inline keyboards
- Multi-select modules with toggle states
- Complexity scoring and timeline estimation
- Instant brief generation and restart flow

## Screenshots
![BriefForge Bot screenshot 1](bot%201%20img.png)
![BriefForge Bot screenshot 2](bot%202%20img.png)
![BriefForge Bot screenshot 3](Bot%203%20img.png)

## Setup
1. Install dependencies:
```bash
pip install aiogram python-dotenv
```

2. Create a `.env` file in the project root with your bot token:
```env
BOT_TOKEN=your_bot_token_here
```

3. Run the bot:
```bash
python bot.py
```
