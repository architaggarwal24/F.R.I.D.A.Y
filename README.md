# F.R.I.D.A.Y

AI-powered personal desktop assistant inspired by JARVIS, built with React, Express, Python voice services, and modern LLM integrations.

## Overview

F.R.I.D.A.Y is a voice-enabled AI assistant that combines a modern conversational interface with speech capabilities to create a natural desktop assistant experience.

The project includes:

* Real-time AI chat interface
* Voice input and speech output
* Activity monitoring
* Assistant settings management
* Modern animated UI
* Support for external AI models through APIs

## Features

### Voice Assistant

* Voice-to-text interaction
* Text-to-speech responses
* Hands-free conversations
* Microphone integration

### AI Chat

* Natural language conversations
* Context-aware responses
* Persistent conversation flow
* Fast response handling

### Modern Interface

* Interactive assistant orb
* Activity feed
* Chat panel
* Settings drawer
* Responsive design

### Local Bridge Server

* Express backend
* API communication layer
* Environment-based configuration
* Secure key management

## Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS
* JavaScript

### Backend

* Node.js
* Express

### Voice Engine

* Python
* Speech processing libraries

## Project Structure

```text
FRIDAY/
├── src/
│   ├── components/
│   ├── App.jsx
│   ├── api.js
│   ├── useConversation.js
│   └── useVoice.js
│
├── voice/
│   ├── friday_voice.py
│   ├── requirements.txt
│   └── mictest.py
│
├── server.js
├── package.json
└── .env.example
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/architaggarwal24/F.R.I.D.A.Y.git
cd F.R.I.D.A.Y
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env` file using:

```bash
cp .env.example .env
```

Add your API keys and configuration values.

### 4. Setup Voice Service

```bash
cd voice
pip install -r requirements.txt
```

Create:

```bash
voice/.env
```

using the provided example.

## Running the Application

### Start Frontend + Backend

```bash
npm run dev
```

### Start Voice Engine

```bash
cd voice
python friday_voice.py
```

## Available Scripts

```bash
npm run dev
npm run build
npm run preview
npm run lint
```

## Use Cases

* Personal AI assistant
* Productivity companion
* Voice-controlled interactions
* AI experimentation platform
* Desktop assistant prototype

## Future Improvements

* Wake-word detection
* Calendar integrations
* Email management
* Smart home controls
* Local LLM support
* Multi-agent workflows

## Author

Archit Aggarwal

## License

MIT License
