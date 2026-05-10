# 🗂️ My Organizer

> AI-powered personal organizer for email and files. Runs locally. Gets smarter over time.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)

---

## What it does

- **Watches** your inbox and Downloads folder
- **Classifies** every email and file into categories (Finances, Work, Receipts, etc.)
- **Executes** actions automatically — move, archive, rename
- **Learns** from your corrections and gets smarter over time
- **Runs locally** after Phase 1 — no internet required for 95% of tasks

---

## Architecture

```
Phase 1 (Days 1-3)   →  Gemini API classifies everything (free tier)
Phase 2 (Week 2-4)   →  Baby AI + Gemini (your corrections fine-tune a local model)
Phase 3 (After 500)  →  Baby AI handles 95%+ locally, Gemini only for unknowns
```

```
┌──────────────────────────────────────────────────┐
│              Desktop Widget (Electron)            │
│   Email List │ File Tree │ Action Log             │
│              ↓                                    │
│        FastAPI backend (localhost:5000)           │
│              ↓                                    │
│   Orchestrator → Baby AI or Gemini               │
│              ↓                                    │
│         SQLite (actions + corrections)            │
└──────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- A [Gemini API key](https://aistudio.google.com) (free)
- Gmail App Password or IMAP credentials

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/my-organizer.git
cd my-organizer

# Node deps
npm install

# Python deps
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.json config.json
# Edit config.json — add your Gemini API key and IMAP credentials
```

```json
{
  "gemini_api_key": "AIza...",
  "imap": {
    "host": "imap.gmail.com",
    "user": "you@gmail.com",
    "password": "your_app_password"
  },
  "folders": {
    "watch": ["~/Downloads", "~/Desktop"],
    "organize_root": "~/Organized"
  }
}
```

### 3. Run

```bash
# Desktop widget (Electron)
npm start

# Or run API only (for mobile app dev)
cd api && uvicorn server:app --reload --port 5000
```

---

## Project Structure

```
my-organizer/
├── electron/           # Desktop widget
│   ├── main.js        # Electron main process
│   ├── preload.js     # Secure IPC bridge
│   ├── index.html     # Widget UI
│   └── renderer.js    # UI logic
├── api/
│   └── server.py      # FastAPI backend (REST API)
├── ai/
│   ├── orchestrator.py  # Decides Baby AI vs Free API
│   ├── free_api.py      # Gemini wrapper
│   └── baby_ai/
│       ├── inference.py  # Local model (pattern-based → transformer)
│       └── train.py      # LoRA fine-tuning script
├── helpers/
│   ├── email_utils.py   # IMAP operations
│   └── file_utils.py    # File move/rename
├── storage/
│   ├── database.py      # SQLite layer
│   ├── actions.db       # (gitignored) your decision log
│   └── training_data.jsonl  # Baby AI training examples
├── config.example.json  # Template — copy to config.json
└── requirements.txt
```

---

## Phases

### Phase 1 — Free API Only (Days 1–3)
Everything goes through Gemini. Nothing is trained yet. Just collect corrections.

### Phase 2 — Train Baby AI (Week 2–4)
Once you have 200+ corrections, run:

```bash
python ai/baby_ai/train.py
```

Then set `"baby_ai_enabled": true` in `config.json` and restart. Baby AI will handle confident predictions; Gemini handles the rest.

### Phase 3 — Mostly Local (Month 2+)
Baby AI handles 95%+ of tasks locally. No internet needed for routine organization. Re-train every weekend for best accuracy.

---

## API Endpoints

The FastAPI backend is shared between the desktop widget and the mobile app.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Status + model info |
| `/actions` | GET | Recent actions |
| `/actions/{id}/undo` | POST | Undo an action |
| `/actions/{id}/why` | POST | Explain a decision |
| `/corrections` | POST | Submit a correction |
| `/emails/organize-all` | POST | Organize all emails |
| `/files/organize-all` | POST | Organize all files |
| `/stats` | GET | Usage stats |

Full docs at `http://localhost:5000/docs` (Swagger UI auto-generated).

---

## Mobile App

The FastAPI backend is designed to be shared with a React Native or Capacitor app. To build the mobile version:

1. The `/api/server.py` is the backend for both desktop and mobile
2. Host the backend locally or on a small VPS
3. Point the mobile app to `http://YOUR_IP:5000`

See `docs/mobile.md` for mobile setup guide (coming soon).

---

## Gmail Setup

1. Enable IMAP in Gmail Settings → Forwarding and POP/IMAP
2. Go to Google Account → Security → 2-Step Verification → App passwords
3. Create an app password for "Mail" on "Mac" (or your device)
4. Use that 16-character password in `config.json`

---

## Cost

| Item | Cost |
|---|---|
| Gemini API (500 req/day free) | $0 |
| Hosting (all local) | $0 |
| Training compute (Google Colab T4) | $0 |
| Baby AI inference (CPU only) | $0 |

**Total: $0**

---

## Building Installers

```bash
npm run build:mac    # .dmg
npm run build:win    # .exe
npm run build:linux  # .AppImage
```

---

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Capacitor web/mobile bridge
- [ ] Calendar integration
- [ ] Slack/Teams notification sorting
- [ ] Export to Notion / Obsidian
- [ ] Multi-account email support

---

## License

MIT — do whatever you want.
