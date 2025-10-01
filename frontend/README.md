# Mira Frontend

React + TypeScript + Vite frontend for the Mira smart mirror application.

## Features

- **Morning Mode**: Dashboard view with calendar, weather, news, and todos
- **Ambient Mode**: Clock display with minimal information
- **Real-time Vision**: WebSocket-based gesture detection and camera preview
- **Dark Theme**: Beautiful gradient-based dark theme
- **Responsive**: Adapts to different screen sizes
- **Optimistic Updates**: Instant UI feedback for todo operations

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS v4** for styling
- **Framer Motion** for animations
- **Axios** for API communication

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment (Optional)

Create a `.env.local` file if you need to customize the API URL:

```env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_VERSION=1.0.0
```

Default API URL is `http://localhost:8080` if not specified.

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or the next available port).

Make sure the backend server is running at the configured API URL.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── Card.tsx
│   ├── ModeSwitcher.tsx
│   ├── Quadrant.tsx
│   └── Toast.tsx
├── features/         # Feature-specific components
│   ├── calendar/
│   ├── news/
│   ├── todos/
│   ├── vision/
│   └── weather/
├── lib/              # Utilities and API client
│   ├── api.ts        # Backend API wrapper
│   └── types.ts      # TypeScript type definitions
├── App.tsx           # Main application component
├── App.css           # Application styles
├── index.css         # Global styles with Tailwind
└── main.tsx          # Application entry point
```

## API Integration

The frontend communicates with the backend through the following endpoints:

- `GET /health` - Health check
- `GET /api/v1/morning-report` - Fetch all dashboard data
- `GET /api/v1/todos` - Get todos
- `POST /api/v1/todos` - Create todo
- `PUT /api/v1/todos/:id` - Update todo
- `DELETE /api/v1/todos/:id` - Delete todo
- `POST /api/v1/voice/interpret` - Interpret voice command
- `GET /api/v1/settings` - Get settings
- `PUT /api/v1/settings` - Update settings
- `GET /vision/snapshot.jpg` - Get camera snapshot
- `WS /ws/vision` - WebSocket for real-time vision intents

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready to be served by nginx or another static file server.

## Deployment

See the main project README and `phase_1_detailed.md` Guide 3 for Docker and deployment instructions.
