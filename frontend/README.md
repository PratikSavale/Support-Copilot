# Support Copilot - Frontend (User View)

This is the frontend implementation for the AI-Powered L2 Support Copilot. It features a premium, real-time chat interface built with React, TypeScript, and Tailwind CSS.

## 🚀 Getting Started

### 1. Prerequisites
- Node.js (v18 or higher)
- npm or yarn

### 2. Installation
Navigate to the frontend directory and install the dependencies:
```bash
cd frontend
npm install
```

### 3. Environment Setup
Create a `.env` file in the `frontend` directory and configure the backend URLs:
```env
# The REST API base URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# The WebSocket URL for real-time streaming
VITE_WS_URL=ws://localhost:8000/api/v1/chat/ws
```

### 4. Running Development Server
Start the Vite development server:
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

## 🛠️ Features for Developers

- **Real-time Streaming:** The app uses WebSockets to stream AI responses chunk-by-chunk. Check `src/hooks/useWebSocket.ts` for logic.
- **State Management:** All chat and session data is managed via Zustand in `src/store/userStore.ts`.
- **Styling:** We use a custom "Deep Space" theme. Brand colors and glassmorphism utilities are defined in `tailwind.config.ts` and `src/index.css`.
- **Path Aliases:** Use `@/` to refer to the `src/` directory (e.g., `@/components/Button`).

## 🏗️ Production Build
To create a production-ready bundle:
```bash
npm run build
```
The output will be in the `dist/` folder.

## 🤝 Integration Notes
- **Session IDs:** The app automatically generates a session ID if none is present in the URL (`/chat/:sessionId`).
- **Actions:** The frontend listens for `action` fields in the WebSocket messages to trigger:
    - `resolve`: Shows a resolution indicator.
    - `clarification`: Shows "Clarification Chips" (suggestions).
    - `escalated`: Shows the "Ticket Notification" component.
