# Blueprint BI

Blueprint BI is an **AI-powered conversational business intelligence platform** designed to help small and independent businesses turn their customer conversations into useful business insights.

## The Problem

Many small businesses manage customer interactions through WhatsApp, where important information is scattered across:
- Text messages
- Voice notes
- Images
- Order discussions

Manually reviewing large volumes of conversations to extract business insights is time-consuming and inefficient.

## The Solution

Blueprint BI automatically:
- **Extracts and structures** information from customer conversations
- **Maintains useful context** about customers, orders, and inquiries
- **Allows natural-language exploration** of business data through an AI assistant
- **Provides actionable insights** about customers, products, services, and business patterns

## Key Features

- **🌍 Multilingual Conversation Understanding** — Processes conversations in English, Sinhala, Singlish (Romanized Sinhala), and mixed-language messages

- **📱 Multimodal Data Processing** — Works with text, voice notes, images, and structured order information

- **🤖 AI-Powered Information Extraction** — Automatically extracts customers, inquiries, products/services, requirements, orders, dates, prices, and conversation outcomes

- **📊 Customer & Order Intelligence** — Organizes extracted information into structured records while maintaining interaction history

- **💡 Business Insights & Analytics** — Provides insights into customer inquiries, frequently requested products/services, new vs. returning customers, inquiry-to-order patterns, and more

- **🗣️ Natural-Language Business Assistant** — Ask questions about your business data and receive context-aware answers

- **🔍 AI-Assisted Conversation Analysis** — Identifies patterns, common questions, unconverted inquiries, and other valuable information

- **✅ Human-in-the-Loop Validation** — Review and correct AI-extracted information before updating business records

- **🎤 Post-Call Voice Summaries** — Incorporate important information from verbal conversations into customer and order records

## Project Structure

```
Blueprint BI/
├── backend/              # Python backend (LangGraph agent, API)
│   ├── app/
│   │   ├── agent.py     # AI agent implementation
│   │   └── __init__.py
│   ├── requirements.txt   # Python dependencies
│   └── langgraph.json    # LangGraph configuration
│
├── frontend/            # Next.js frontend
│   └── agent-chat-ui/   # Chat UI application
│       ├── src/
│       ├── package.json
│       └── README.md     # Frontend-specific setup
│
└── README.md            # This file
```

## Quick Start

### Prerequisites
- **Python 3.10+** (for backend)
- **Node.js 18+** & **pnpm** (for frontend)
- **Git**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python -m app.agent
```

### Frontend Setup

```bash
cd frontend/agent-chat-ui

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
# Add your configuration here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

### Backend Development
- Agent logic: [backend/app/agent.py](backend/app/agent.py)
- Configuration: [backend/langgraph.json](backend/langgraph.json)
- Dependencies: [backend/requirements.txt](backend/requirements.txt)

See [frontend/agent-chat-ui/README.md](frontend/agent-chat-ui/README.md) for frontend-specific development guides.

## Project Features & Architecture

- **Agent-based Architecture** — Uses LangGraph for multi-step AI reasoning and tool calling
- **Multi-modal Input** — Processes text, images, and voice
- **Streaming UI** — Real-time conversation updates with artifact support
- **Context Management** — Maintains conversation state and user context
- **Tool Integration** — Integrates with various tools for data processing and retrieval

## Directory Structure

### Frontend (`frontend/agent-chat-ui/src/`)
- **`app/`** — Next.js app router (pages, layouts, API routes)
- **`components/`** — React components (thread UI, messages, agent inbox)
- **`hooks/`** — Custom React hooks
- **`lib/`** — Utility functions and helpers
- **`providers/`** — Context providers (API client, thread state)

### Backend (`backend/`)
- **`app/agent.py`** — Main agent implementation
- **`requirements.txt`** — Python dependencies (LangGraph, FastAPI, etc.)
- **`langgraph.json`** — LangGraph workflow configuration

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit your changes: `git commit -m 'Add your feature'`
3. Push to the branch: `git push origin feature/your-feature`
4. Open a Pull Request

## Deployment

- **Backend**: Deploy using Docker or cloud platforms (AWS, GCP, Azure)
- **Frontend**: Deploy using Vercel, Netlify, or traditional hosting

## Troubleshooting

**Backend won't start?**
- Ensure Python 3.10+ is installed
- Verify virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`

**Frontend issues?**
- Clear node modules: `rm -rf node_modules` and reinstall with `pnpm install`
- See [frontend/agent-chat-ui/README.md](frontend/agent-chat-ui/README.md) for frontend-specific issues

## License

See [frontend/agent-chat-ui/LICENSE](frontend/agent-chat-ui/LICENSE)

## Contact & Support

For issues, feature requests, or questions, please open an issue on GitHub.

---

**Last Updated:** 2026-08-09
