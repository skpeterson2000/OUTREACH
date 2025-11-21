# Backend Setup

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and secrets
```

4. Set up PostgreSQL database:
```bash
# Create database
createdb homecare_ehr

# Or using psql:
psql -U postgres
CREATE DATABASE homecare_ehr;
\q
```

5. Initialize database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Running the Application

Development server:
```bash
python run.py
```

Or using Flask CLI:
```bash
export FLASK_APP=app
export FLASK_ENV=development
flask run
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Users
- `GET /api/users` - List all users (admin only)
- `GET /api/users/<id>` - Get user details
- `POST /api/users` - Create new user (admin only)
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Deactivate user (admin only)

### Patients
- Coming soon

### Medications
- Coming soon

### Assessments
- Coming soon

### Visits
- Coming soon

## Database Models

- **User** - Healthcare staff with role-based permissions
- **Patient** - Patient demographics and medical information
- **Visit** - Patient visit records
- **Medication** - Medication prescriptions
- **MedicationAdministration** - MAR (Medication Administration Record)
- **Assessment** - General clinical assessments
- **VitalSigns** - Vital signs recordings
- **WoundAssessment** - Comprehensive wound documentation
- **SpecialtyAssessment** - Specialty-specific assessments (burns, respiratory, etc.)
- **AuditLog** - Comprehensive audit trail for HIPAA compliance

## Specialty Assessments

The system supports various specialty assessments:

### Burn Assessment
- TBSA calculation using Rule of Nines
- Burn depth classification
- Rule of 8s implementation
- Severity classification

### Respiratory Assessment
- Respiratory distress scoring
- Breath sound documentation
- Oxygen requirements

### Nutritional Assessment
- BMI calculation
- Dietary intake tracking
- Swallowing assessment

### Fall Risk Assessment
- Morse Fall Scale
- Risk stratification
- Intervention recommendations

## Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Account lockout after failed attempts
- Session timeout
- Comprehensive audit logging
- HIPAA compliance features

## Testing

Run tests:
```bash
pytest
pytest --cov=app tests/
```

## Database Migrations

Create migration:
```bash
flask db migrate -m "Description of changes"
```

Apply migration:
```bash
flask db upgrade
```

Rollback:
```bash
flask db downgrade
```
