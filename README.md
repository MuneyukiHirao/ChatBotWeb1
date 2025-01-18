# ChatBotWeb1 - README

## Overview

This repository contains a web-based chatbot application that leverages a **Flask** backend and a **React** (Vite) frontend. Its primary purpose is to demonstrate how to integrate a Large Language Model (LLM) through OpenAI’s API with a multi-step, function-calling architecture (e.g., `getMachineInfo`, `searchManual`, `notifyStaff`). The chatbot can:

- Retrieve and confirm machine details (model & serial number).
- Search manuals (either operation manual or shop manual) using an external API.
- Notify staff (service, parts, etc.) via function calls.
- Manage chat sessions and user selections in a simple multi-page web UI.

## Features

- **User login**: A simple demonstration login (`userId = "test"`, `password = "test"`).
- **User selection**: A list of users (loaded from `users.json`), each associated with a company and machine count.
- **Chat**: WhatsApp-like chat interface where the user interacts with the LLM-based bot.
- **Azure OpenAI/Function Calling**: The backend uses `openai.chat.completions.create(...)` to handle function calls (`getMachineInfo`, `searchManual`, `notifyStaff`).
- **In-memory session**: Stores conversation data in Python memory (demo usage).
- **Deployable to Azure Web App** with minimal configuration.

## Project Structure

```plaintext
.
├── frontend/
│    ├── package.json
│    ├── src/
│    │    ├── App.tsx
│    │    ├── pages/
│    │    │    ├── LoginPage.tsx
│    │    │    ├── SelectUserPage.tsx
│    │    │    └── ChatPage.tsx
│    │    └── api/ApiClient.ts
│    └── ...
├── backend/
│    ├── run.py            # Flask entry point
│    ├── chat_bot.py       # Chat logic with OpenAI function calling
│    ├── api_functions.py  # Implementation of getMachineInfo, searchManual, notifyStaff
│    ├── requirements.txt  # Python dependencies
│    ├── users.json        # Sample user data
│    └── customer_machine_list.json (optional) # Sample machine data
├── system_prompt.txt      # System prompt rules for the bot
├── Procfile               # Start commands for Azure deployment
└── ...
```

### Key Components

- **`backend/run.py`**: Flask server, sets up the REST endpoints (`/api/login`, `/api/users`, `/api/select-user`, `/api/chat`, etc.).  
- **`backend/chat_bot.py`**: Implements the LLM function-calling logic (OpenAI chat completions).  
- **`backend/api_functions.py`**: Houses Python helper functions (`getMachineInfo`, `searchManual`, `notifyStaff`).  
- **`frontend/`**: React + TypeScript + Vite application.  
- **`system_prompt.txt`**: Contains the system instructions for the LLM (categories, usage rules).

## Tech Stack

- **Frontend**:
  - **Vite** + **React** + **TypeScript**
  - React Router (for `/login`, `/select-user`, `/chat` pages)
  - Axios or fetch for REST calls to the backend
- **Backend**:
  - **Flask** (Python 3.x)
  - **OpenAI** Python library
  - **Flask-CORS** (for development cross-origin usage)
- **OpenAI**:
  - Uses `openai.chat.completions.create` (model="gpt-4" or similar)
  - Leverages function_call="auto" to handle typed function arguments
- **Azure Web App**:
  - Build & deployment via Deployment Center
  - `OPENAI_API_KEY` stored in Application Settings

## Installation and Usage

Below is a minimal sequence to install dependencies and run locally (assuming Python 3.9+ and Node 16+):

```bash
# 1) Frontend setup
cd frontend
npm install
npm run build  # to build for production
# Alternatively: npm run dev # for local dev on port 5173

# 2) Backend setup
cd ../backend
pip install -r requirements.txt

# 3) Run Flask
python run.py
# or gunicorn --chdir backend run:app --bind=0.0.0.0:$PORT

# The Flask app will serve:
#  /api/... for backend endpoints
#  / for the built frontend (if static_folder is set to ../frontend/dist)
```

Open your browser at http://localhost:5000 (or the Azure-assigned domain when deployed).

Environment Variables
OPENAI_API_KEY: Must be set to your actual OpenAI secret key. In Azure, store it in Application Settings.
If local: Create a .env file in backend/ with OPENAI_API_KEY=sk-xxxx (then add .env to .gitignore).
Deploy to Azure Web App
Typical steps:

Create an Azure Web App (Python) from the Portal.

In Deployment Center, link your GitHub repo & branch.

```bash
Add a build command, e.g.:
cd frontend
npm install
npm run build
cd ../backend
pip install -r requirements.txt
```

Startup command:

```bash
python backend/run.py
```

In Configuration > Application Settings, add OPENAI_API_KEY.

Save & wait for deployment.

Access the Web App URL (e.g. https://your-webapp.azurewebsites.net).

FAQ
Why "Network Error" on login?

Possibly CORS, or the server isn’t running on the correct port. Make sure CORS(app, origins="*") for dev, and double-check the BASE_URL in ApiClient.ts.
Why [Error] Final message is None?

Sometimes the LLM might produce an empty content. See the code in chat_bot.py to handle function calls or implement a retry if final_msg is None.
Where to store the machine info or user data?

For demo, in JSON files (customer_machine_list.json, users.json). In real production, store them in a database.
