# Sisimpur Frontend (React + Vite)

A React SPA frontend for the Sisimpur AI-Powered Exam Prep platform, built with **Vite**, **React 19**, **TypeScript**, and **Tailwind CSS v4**.

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server (port 3000, proxies /api/* to Django at :8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Tech Stack

- **React 19** with React Router v7 for client-side routing
- **Vite 6** for fast dev server and optimized builds
- **TypeScript 5** for type safety
- **Tailwind CSS v4** via `@tailwindcss/postcss`
- **Axios** for API calls with CSRF cookie support
- **react-dropzone** for file upload
- **react-hook-form** for form handling

## Project Structure

```
src/
├── main.tsx              # Entry point (BrowserRouter, providers)
├── App.tsx               # Route definitions
├── globals.css           # Global styles, design tokens, Tailwind
├── components/
│   ├── layout/           # Background, Navbar, Sidebar
│   └── ui/               # ToastProvider, Toaster
├── layouts/
│   ├── AuthLayout.tsx    # Auth page wrapper
│   ├── DashboardLayout.tsx # Dashboard wrapper (sidebar + nav)
│   └── ProtectedRoute.tsx  # Auth guard (redirects to /signin)
├── lib/
│   ├── api.ts            # Axios API client
│   ├── auth-context.tsx  # Auth context provider
│   ├── types.ts          # TypeScript interfaces
│   └── utils.ts          # Utility functions (cn, formatDate, etc.)
└── pages/                # All page components
```

## API Proxy

In development, Vite proxies `/api/*` requests to `http://localhost:8000` (Django backend). This is configured in `vite.config.ts`.

For production, configure your web server (nginx, etc.) to proxy `/api/*` to the Django backend.
