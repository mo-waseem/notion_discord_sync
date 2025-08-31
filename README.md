# 🚀 Notion → Discord Issues Bridge

This project listens to **Notion issue updates** via webhook and posts them into a **Discord channel** using a webhook.  
Built with **FastAPI** + **Discord.py (webhooks)**.

---

## 📦 Requirements

- Python 3.11+ (recommended)  
- [uv](https://github.com/astral-sh/uv) (for package management)  
- Redis (for deduplication, if enabled)

---

## ⚙️ Environment Variables

Create a `.env` file in the project root with:

```env
# Notion API webhook secret
NOTION_WEBHOOK_SECRET=""

# Database ID of your Issues database in Notion
NOTION_ISSUES_DATABASE_ID=""

# Discord webhook for needed(live issues)channel
DISCORD_LIVE_ISSUES_WEBHOOK_URL=""
```

---

## 📚 Installation

Install dependencies using **uv**:

```bash
uv pip install -r requirements.txt
```

---

## ▶️ Running the App

Run locally with **uvicorn**:

```bash
uv run uvicorn app:app --reload --port 5000
```

Now your FastAPI server is running at:  
👉 http://localhost:5000

---

## 🔗 Webhook Setup

1. In Notion, set up a webhook that points to:

```
https://<your-domain>/webhook/notion
```

2. Use the `NOTION_WEBHOOK_SECRET` to validate incoming requests.  

3. Issues created or updated in your **Notion Issues Database** will be sent to your configured **Discord channel**.

---

## 🛠️ Development Notes

- Messages posted to Discord are built dynamically from your `config.yaml`.  
- You can configure **required** and **optional** properties, and customize leading tokens/emojis.  

Example `config.yaml`:

```yaml
required_properties:
  - name: "Issue"
    type: "title"

  - name: "Assignee"
    type: "people"

optional_properties:
  - name: "Priority"
    type: "select"

  - name: "extra"
    type: "rich_text"


```

---

## 📦 requirements.txt

```txt
fastapi
uvicorn
pyyaml
discord.py
python-dotenv
redis
requests
# Optional:
# psycopg2-binary  # if you connect to Postgres
# gunicorn         # if deploying with Gunicorn
```

---

## 🚀 Deployment

- **Production**: run with Gunicorn + Uvicorn workers:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:5000
```

- **Docker**: add a simple `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:5000"]
```

---

## 📝 Example Discord Message

```
🆕 Issue Created
📝 Task: Fix API rate limiting
🙋 Owner: Waleed Al-Tarazi
⚡ Priority: High
📌 Notes: Retry logic needed
⏰ Created: 2025-08-31T13:04:00.000Z
🔗 Open in Notion
```

---

## 📝 License

MIT

---

## 🤝 Contributing

Contributions are welcome!  

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/my-feature`)  
3. Commit your changes (`git commit -am 'Add new feature'`)  
4. Push to the branch (`git push origin feature/my-feature`)  
5. Open a Pull Request  

---

## 💡 Notes

- Make sure your `config.yaml` matches the **property names** in your Notion database.  
- The service will **deduplicate messages** using Redis keys.  
- You can customize message formatting by changing the `lead` tokens in `config.yaml`.

