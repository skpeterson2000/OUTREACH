# Home Care EHR System

A comprehensive Electronic Health Record system designed specifically for home healthcare nursing, with specialized assessment modules for various clinical specialties.

## Overview

This EHR supports:
- **Medication Management**: MAR, reconciliation, PRN tracking
- **Wound Care**: Comprehensive wound assessment and tracking
- **Specialty Assessments**:
  - Burn evaluation (Rule of 8s)
  - Respiratory assessments
  - Dietary/nutritional assessments
  - Psychological screening tools
  - Pain management
  - Fall risk assessment
  - And more...

## Architecture

### Backend
- **Framework**: Python Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with role-based access control
- **API**: RESTful design with comprehensive audit logging

### Frontend
- **Framework**: React with TypeScript
- **UI Components**: Material-UI for clinical interfaces
- **State Management**: Redux for complex state handling
- **Routing**: React Router for SPA navigation

## Project Structure

```
/backend
  /app
    /models          # Database models
    /routes          # API endpoints
    /services        # Business logic
    /assessments     # Specialty assessment modules
    /utils           # Helper functions
  /migrations        # Database migrations
  /tests            # Unit and integration tests

/frontend
  /src
    /components      # Reusable UI components
    /pages           # Main application pages
    /services        # API integration
    /modules         # Feature-specific modules
    /utils           # Helper functions

/docs
  /clinical         # Clinical workflow documentation
  /technical        # Technical specifications
```

## Key Features

### Core Clinical Modules
- Patient demographics and medical history
- Visit scheduling and documentation
- Vital signs tracking with trend analysis
- Medication administration records (MAR)
- Care plans and nursing diagnoses
- Progress notes with narrative documentation

### Specialty Assessment Modules
Each specialty has focused assessment tools:
- **Burns**: Rule of 8s calculation, TBSA estimation, depth classification
- **Wounds**: Staging, measurement, drainage documentation, healing progress
- **Respiratory**: Breath sounds, oxygen requirements, breathing patterns
- **Cardiac**: Heart sounds, edema assessment, circulation checks
- **Neurological**: Consciousness level, pupil response, motor/sensory function
- **Nutritional**: Dietary intake, weight trends, swallowing assessment
- **Psychological**: Depression screening, anxiety assessment, cognitive status

### Compliance & Security
- HIPAA-compliant data handling
- Comprehensive audit trails
- Encrypted data at rest and in transit
- Role-based access control
- Automatic session timeout
- Password policies

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- npm or yarn

### Installation

See individual setup instructions in:
- `/backend/README.md`
- `/frontend/README.md`

## Development Roadmap

- [x] Project initialization
- [ ] Core database schema
- [ ] Authentication system
- [ ] Medication management
- [ ] Wound care module
- [ ] Specialty assessments
- [ ] Frontend dashboard
- [ ] Reporting and analytics

## License

Proprietary - All rights reserved
