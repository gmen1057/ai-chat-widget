# AI Chat Widget

Drop-in AI chat widget for any website. Works with OpenAI, Claude, Gemini, GigaChat, YandexGPT, Ollama, and any OpenAI-compatible API.

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **Universal AI Support** - OpenAI, Claude, Gemini, GigaChat, YandexGPT, DeepSeek, Qwen, Ollama, OpenRouter
- **One-line Integration** - Just add a `<script>` tag
- **Self-hosted** - Full control over your data
- **Knowledge Base** - Load custom knowledge from markdown files
- **Chat History** - Persists across page reloads (localStorage)
- **Telegram Alerts** - Get notified about escalations and feedback
- **Security** - Rate limiting, attack detection, IP blocking
- **Privacy Settings** - Exclude sensitive pages from context collection
- **Markdown Support** - Rich text formatting in responses
- **Mobile Responsive** - Works on all devices

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/gmen1057/ai-chat-widget.git
cd ai-chat-widget
cp backend/.env.example backend/.env
# Edit backend/.env with your AI API key
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up -d
```

### 3. Or Run Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. Add to Your Website

```html
<script
  src="https://your-server.com/widget/widget.js"
  data-server="https://your-server.com"
  data-title="Support"
  data-welcome="Hi! How can I help you?"
  data-placeholder="Type your message..."
  data-position="bottom-right"
></script>
```

That's it! The widget will appear on your website.

## Configuration

### AI Providers

Edit `backend/.env` to configure your AI provider:

**OpenAI** (default):
```env
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-xxx
AI_MODEL=gpt-4o-mini
```

**Claude (Anthropic)**:
```env
AI_BASE_URL=https://api.anthropic.com/v1
AI_API_KEY=sk-ant-xxx
AI_MODEL=claude-sonnet-4-20250514
```

**Google Gemini** (native API):
```env
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
AI_API_KEY=AIza...
AI_MODEL=gemini-2.0-flash-exp
```

**GigaChat** (Sber, Russia):
```env
AI_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
AI_MODEL=GigaChat
GIGACHAT_CREDENTIALS=base64_encoded_credentials
```

**Ollama** (local, free):
```env
AI_BASE_URL=http://localhost:11434/v1
AI_API_KEY=ollama
AI_MODEL=llama3.2
```

See `backend/.env.example` for all providers.

### Widget Options

| Attribute | Default | Description |
|-----------|---------|-------------|
| `data-server` | Required | Your backend URL |
| `data-title` | "Chat" | Widget header title |
| `data-welcome` | "Hello!" | Initial greeting message |
| `data-placeholder` | "Type a message..." | Input placeholder |
| `data-position` | "bottom-right" | Position: `bottom-right`, `bottom-left` |
| `data-primary-color` | "#2563eb" | Primary color (hex) |
| `data-include` | "" | Show only on these pages (comma-separated paths) |
| `data-exclude` | "" | Hide on these pages |
| `data-private` | "" | Don't collect page content on these pages |
| `data-no-content` | "" | Collect URL/title only, not content |

### Privacy Settings

Control what page context is sent to AI:

```html
<!-- Don't show widget on login page -->
<script src="..." data-exclude="/login,/signup"></script>

<!-- Show only on docs pages -->
<script src="..." data-include="/docs/*,/help/*"></script>

<!-- Don't send page content on account pages -->
<script src="..." data-private="/account/*,/settings/*"></script>

<!-- Send only URL/title, not full content -->
<script src="..." data-no-content="/dashboard/*"></script>
```

### Knowledge Base

Add markdown files to `knowledge/` folder to customize bot's knowledge:

```
knowledge/
  about.md      # Company info
  faq.md        # Frequently asked questions
  pricing.md    # Pricing information
```

The bot will use this content to answer questions.

### Telegram Alerts

Get notified when users:
- Ask for human help ("I want to talk to a human")
- Report problems ("this doesn't work")
- Leave positive feedback ("thank you, great help!")
- Leave negative feedback ("this is useless")

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=your_chat_id
```

To get your chat ID:
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your chat ID

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/message` | POST | Send message, get AI response |
| `/api/chat/history/{session_id}` | GET | Get chat history |
| `/api/chat/session/{session_id}` | DELETE | Clear session |
| `/api/chat/telegram/test` | GET | Test Telegram connection |
| `/widget/widget.js` | GET | Widget JavaScript |
| `/widget/widget.css` | GET | Widget styles |

## Architecture

```
ai-chat-widget/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   │   ├── ai_service.py      # AI provider integration
│   │   │   ├── telegram.py        # Telegram notifications
│   │   │   ├── security.py        # Rate limiting, attack detection
│   │   │   └── storage/           # Chat history storage
│   │   ├── config.py     # Configuration
│   │   └── main.py       # FastAPI app
│   ├── data/             # Chat history (json/sqlite)
│   └── .env              # Configuration
├── widget/
│   ├── widget.js         # Self-contained widget
│   └── widget.css        # Standalone CSS (optional)
├── knowledge/            # Knowledge base markdown files
├── docker-compose.yml
└── Dockerfile
```

## Security Features

- **Rate Limiting**: Configurable requests per minute/hour
- **Attack Detection**: SQL injection, XSS, prompt injection detection
- **IP Blocking**: Automatic temporary bans for attackers
- **Strike System**: Progressive penalties for violations
- **Message Validation**: Length limits, content sanitization

## Storage Options

**JSON** (default, development):
```env
STORAGE_TYPE=json
```

**SQLite** (single server):
```env
STORAGE_TYPE=sqlite
```

**PostgreSQL** (production):
```env
STORAGE_TYPE=postgres
DATABASE_URL=postgresql://user:pass@localhost/chatbot
```

## Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run with hot reload
uvicorn app.main:app --reload --port 8080

# Test widget
open demo.html
```

## Production Deployment

### With Docker Compose

```bash
# Configure
cp backend/.env.example backend/.env
# Edit backend/.env

# Deploy
docker-compose up -d

# View logs
docker-compose logs -f
```

### With systemd

```bash
# Create service file
sudo nano /etc/systemd/system/ai-chat-widget.service
```

```ini
[Unit]
Description=AI Chat Widget
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-chat-widget/backend
ExecStart=/opt/ai-chat-widget/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-chat-widget
sudo systemctl start ai-chat-widget
```

### Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl;
    server_name chat.example.com;

    ssl_certificate /etc/letsencrypt/live/chat.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Pull requests welcome! Please ensure tests pass and code is formatted.

## Support

- Issues: [GitHub Issues](https://github.com/gmen1057/ai-chat-widget/issues)
- Telegram: [@gmen1057](https://t.me/gmen1057)
