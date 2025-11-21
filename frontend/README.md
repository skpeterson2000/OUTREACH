# Frontend Setup

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/      # Reusable UI components
├── pages/          # Page components
├── services/       # API integration
├── store/          # State management (Zustand)
├── utils/          # Helper functions
└── types/          # TypeScript type definitions
```

## Features

- Material-UI for consistent medical interface design
- React Router for navigation
- Zustand for state management
- Axios for API requests
- TypeScript for type safety
- Vite for fast development

## Current Pages

- `/login` - Authentication
- `/dashboard` - Main dashboard

## Upcoming Pages

- `/patients` - Patient management
- `/visits` - Visit scheduling and documentation
- `/medications` - MAR (Medication Administration Record)
- `/assessments` - Clinical assessments
- `/wounds` - Wound care documentation
- `/specialty` - Specialty assessments (burns, respiratory, etc.)
