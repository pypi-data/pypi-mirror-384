# FastAPI React Web CLI

A modern CLI tool to scaffold a full-stack FastAPI + React project in seconds.

## Features at a Glance
- Interactive CLI with prompts
- Project templates:
  - React (Vite)
  - Next.js
  - Eleventy (11ty)
  - Vanilla JavaScript & TypeScript
- Tailwind CSS integration (optional)
- TypeScript support
- Pick your favorite package manager (npm, yarn, pnpm)
- ESLint pre-configured
- Auto installs everything you need

## Features
- Instantly create a FastAPI backend with CORS and a sample API endpoint
- Scaffold a React frontend (with Vite, TypeScript, and Tailwind support)
- Automatic backend/frontend connection (proxy setup)
- Python virtual environment setup with [uv](https://github.com/astral-sh/uv)
- One command to get started: `fastapi-react-cli`

## Installation

```bash
pip install fastapi-react-web
```

## Usage

```bash
fastapi-react-cli
```

Follow the interactive prompts to set up your project. The CLI will:
- Ask for your project name
- Scaffold backend and frontend
- Set up a Python virtual environment and install backend dependencies
- Set up the React frontend with Vite (and optionally Tailwind CSS)

## Running Your App

### Start the backend
```bash
cd <your_project>/backend
source ../venv/bin/activate
uvicorn main:app --reload
```

### Start the frontend
```bash
cd <your_project>/<frontend_dir>
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) to see your app in action!

## Uninstall
```bash
pip uninstall fastapi-react-web
```

## License
MIT

---

Made with ❤️ by Rudraksh121a
