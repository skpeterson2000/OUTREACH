# OUTREACH EHR System

A comprehensive Electronic Health Record system designed for multi-level care environments including home healthcare, assisted living facilities (ALF), memory care, skilled nursing facilities (SNF), and acute care settings.

## Overview

This enterprise-grade EHR supports:
- **Medication Management**: MAR with hold/resume capabilities, medication reconciliation, PRN tracking, overdue alerts
- **Adverse Drug Reaction (ADR) Surveillance**: Real-time monitoring and pharmacist collaboration
- **Care Plan Management**: Comprehensive nursing interventions, physician orders, and assistance tasks with role-based workflows
- **Patient Care Documentation**: Visit notes, assessments, care plans with outcome tracking
- **Wound Care**: Comprehensive wound assessment and tracking
- **Skilled Nursing Procedures**: Catheter care, tracheostomy care, ostomy care, G-tube care, IV management
- **Billing & Revenue Cycle**: Medicare/Medicaid billing codes, visit documentation for reimbursement, ICD-10/CPT coding
- **Specialty Assessments**:
  - Fall risk (Morse Scale) and pressure injury risk (Braden Scale)
  - Respiratory assessments (COPD, oxygen therapy)
  - Cardiac assessments (CHF monitoring, edema tracking)
  - Neurological assessments (Glasgow Coma Scale, pain assessment)
  - Nutritional assessments (BMI, malnutrition screening)
  - Functional status (Barthel Index, ADL tracking)
  - And more...

## Care Settings Supported

- **Home Healthcare**: Skilled nursing visits, medication management, chronic disease management
- **Assisted Living Facilities (ALF)**: Daily medication administration, wellness checks, care coordination
- **Memory Care**: Specialized dementia/Alzheimer's documentation, behavioral tracking, safety monitoring
- **Skilled Nursing Facilities (SNF)**: Comprehensive nursing care, rehabilitation tracking, discharge planning
- **Hospice & Palliative Care**: Comfort measures, symptom management, advance directive documentation

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

### Completed ✅

- [x] Project initialization with Flask backend and React frontend
- [x] SQLAlchemy database models and relationships
- [x] JWT authentication with role-based access control (RN, LPN, Pharmacist, Admin, CNA, HHA, TMA)
- [x] Multi-tenant architecture with organization and facility management
- [x] Patient management and demographics
- [x] Medication Administration Record (MAR) with scheduling
- [x] Medication hold/resume functionality
- [x] Overdue medication tracking with configurable grace periods
- [x] Adverse Drug Reaction (ADR) surveillance system
- [x] Pharmacist collaboration workflow
- [x] **Care Plan Management System**:
  - [x] Care plan creation and management (RN/Admin)
  - [x] Nursing interventions with scheduling and assignment
  - [x] Physician orders with verification workflow
  - [x] Assistance tasks for CNAs/HHAs with safety tracking
  - [x] Completion documentation with outcomes and patient response
  - [x] Role-based permissions and workflow enforcement
  - [x] Support for catheter care, tracheostomy care, ostomy care, G-tube care
- [x] Comprehensive audit logging with rotating file handlers
- [x] Auto-lock security system with idle detection
- [x] Database migrations with Alembic

### In Progress 🔨

- [ ] Care plan creation form (UI)
- [ ] Navigation menu integration
- [ ] Visit documentation interface
- [ ] Medication reconciliation workflow

### Planned Features 📋

#### Revenue Cycle Management
- [ ] **Billing Module**
  - Visit-based billing with time tracking
  - ICD-10 diagnosis code integration
  - CPT/HCPCS procedure codes
  - Medicare/Medicaid billing forms (UB-04, CMS-1500)
  - Commercial insurance claim generation
- [ ] **Revenue Cycle Dashboard**
  - Unbilled visits tracking
  - Claims submission status
  - Payment posting and reconciliation
  - Denial management workflow
- [ ] **Compliance Reporting**
  - OASIS documentation for home health (required for Medicare)
  - MDS 3.0 for skilled nursing facilities
  - Regulatory compliance alerts

#### Clinical Features
- [ ] Wound care assessment module
- [ ] Specialty assessments (burns, respiratory, cardiac, neuro)
- [ ] Care plan builder with nursing diagnoses
- [ ] Clinical decision support alerts
- [ ] Lab result integration and trending

#### Administrative Features
- [ ] Schedule management for nursing staff
- [ ] Mileage tracking for home visits
- [ ] Facility census and bed management (ALF/SNF)
- [ ] Quality metrics dashboard (readmission rates, infection rates, falls)
- [ ] Reporting and analytics engine

#### Advanced Features
- [ ] Electronic prescribing (eRx) integration
- [ ] HL7/FHIR interface for hospital EMR connectivity
- [ ] Mobile app for field nurses
- [ ] Family portal for care coordination
- [ ] Telehealth visit documentation

## License

Proprietary - All rights reserved
