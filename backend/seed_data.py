"""
Seed data script for testing clinical workflows.

Creates realistic test data including:
- Organizations and facilities
- Users (RN, LPN, Pharmacist)
- Patients with varying complexity
- Medications (active orders)
- Known ADR patterns
- Sample clinical scenarios

Usage:
    python seed_data.py
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Organization, Facility, Device, User,
    Patient, Visit, Medication, MedicationAdministration,
    VitalSigns, Assessment, PatientObservation,
    ADRAlert, MedicationAdverseReaction, MedicationReconciliation, MedicationDiscrepancy,
    PharmacistCollaboration, PharmacistIntervention
)
import bcrypt


def clear_data():
    """Clear existing data (for clean testing)."""
    print("🗑️  Clearing existing data...")
    
    # Order matters due to foreign key constraints
    PharmacistIntervention.query.delete()
    PharmacistCollaboration.query.delete()
    MedicationDiscrepancy.query.delete()
    MedicationReconciliation.query.delete()
    ADRAlert.query.delete()
    PatientObservation.query.delete()
    MedicationAdministration.query.delete()
    Medication.query.delete()
    Assessment.query.delete()
    VitalSigns.query.delete()
    Visit.query.delete()
    Patient.query.delete()
    User.query.delete()
    Device.query.delete()
    Facility.query.delete()
    Organization.query.delete()
    
    db.session.commit()
    print("✅ Data cleared")


def seed_organizations_and_facilities():
    """Create organizations and facilities."""
    print("\n🏢 Creating organizations and facilities...")
    
    # Organization
    org = Organization(
        name="Harmony Home Health",
        address_line1="123 Healthcare Blvd",
        city="Springfield",
        state="IL",
        zip_code="62701",
        phone="555-0100",
        email="info@harmonyhealth.com",
        license_number="HH-IL-12345",
        is_active=True
    )
    db.session.add(org)
    db.session.flush()
    
    # Facilities
    facility1 = Facility(
        organization_id=org.id,
        name="Harmony Home Health - Central",
        facility_type="HOME_HEALTH",
        facility_code="HHH-CENTRAL",
        address_line1="123 Healthcare Blvd",
        city="Springfield",
        state="IL",
        zip_code="62701",
        phone="555-0101",
        is_active=True,
        licensed_beds=100
    )
    
    facility2 = Facility(
        organization_id=org.id,
        name="Harmony Home Health - North",
        facility_type="HOME_HEALTH",
        facility_code="HHH-NORTH",
        address_line1="456 North St",
        city="Springfield",
        state="IL",
        zip_code="62702",
        phone="555-0102",
        is_active=True,
        licensed_beds=75
    )
    
    db.session.add_all([facility1, facility2])
    db.session.flush()
    
    # Devices
    device1 = Device(
        facility_id=facility1.id,
        device_name="Tablet-001",
        device_type="TABLET",
        device_uuid="device-uuid-tablet-001",
        location="Nurse Station A",
        is_active=True
    )
    
    device2 = Device(
        facility_id=facility1.id,
        device_name="Laptop-001",
        device_type="LAPTOP",
        device_uuid="device-uuid-laptop-001",
        location="Med Room",
        is_active=True
    )
    
    db.session.add_all([device1, device2])
    db.session.commit()
    
    print(f"✅ Created organization: {org.name}")
    print(f"✅ Created facilities: {facility1.name}, {facility2.name}")
    print(f"✅ Created devices: {device1.device_name}, {device2.device_name}")
    
    return org, facility1, facility2


def seed_users(facility):
    """Create test users with different roles."""
    print("\n👥 Creating users...")
    
    users = []
    
    # RN - Full access
    rn = User(
        facility_id=facility.id,
        username="nurse.jane",
        email="jane.smith@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Jane",
        last_name="Smith",
        role="RN",
        license_number="RN-IL-98765",
        phone="555-1001",
        status="active",
        is_active=True
    )
    users.append(rn)
    
    # LPN - Limited access
    lpn = User(
        facility_id=facility.id,
        username="nurse.bob",
        email="bob.johnson@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Bob",
        last_name="Johnson",
        role="LPN",
        license_number="LPN-IL-54321",
        phone="555-1002",
        status="active",
        is_active=True
    )
    users.append(lpn)
    
    # Pharmacist
    pharmacist = User(
        facility_id=facility.id,
        username="pharm.sarah",
        email="sarah.williams@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Sarah",
        last_name="Williams",
        role="Pharmacist",
        license_number="RPH-IL-11111",
        phone="555-1003",
        status="active",
        is_active=True
    )
    users.append(pharmacist)
    
    # Admin
    admin = User(
        facility_id=facility.id,
        username="admin.mike",
        email="mike.davis@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Mike",
        last_name="Davis",
        role="Admin",
        phone="555-1004",
        status="active",
        is_active=True
    )
    users.append(admin)
    
    # CNA - Certified Nursing Assistant
    cna = User(
        facility_id=facility.id,
        username="cna.maria",
        email="maria.garcia@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Maria",
        last_name="Garcia",
        role="CNA",
        license_number="CNA-IL-22222",
        phone="555-1005",
        status="active",
        is_active=True
    )
    users.append(cna)
    
    # HHA - Home Health Aide
    hha = User(
        facility_id=facility.id,
        username="hha.david",
        email="david.martinez@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="David",
        last_name="Martinez",
        role="HHA",
        license_number="HHA-IL-33333",
        phone="555-1006",
        status="active",
        is_active=True
    )
    users.append(hha)
    
    # TMA - Trained Medication Assistant (CNA with delegation)
    tma = User(
        facility_id=facility.id,
        username="tma.lisa",
        email="lisa.chen@harmonyhealth.com",
        password_hash=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        first_name="Lisa",
        last_name="Chen",
        role="TMA",
        license_number="TMA-IL-44444",
        phone="555-1007",
        status="active",
        is_active=True
    )
    users.append(tma)
    
    db.session.add_all(users)
    db.session.commit()
    
    print(f"✅ Created {len(users)} users (ALL USE PASSWORD: password123):")
    for u in users:
        print(f"   - {u.first_name} {u.last_name} ({u.role}) - username: {u.username}")
    
    return users  # Return full list for medication administration history


def seed_patients(facility):
    """Create test patients with varying complexity."""
    print("\n🏥 Creating patients...")
    
    patients = []
    
    # Patient 1: Simple case - stable, routine medications
    p1 = Patient(
        facility_id=facility.id,
        medical_record_number="MRN001",
        first_name="Mary",
        last_name="Anderson",
        date_of_birth=datetime(1942, 5, 15).date(),
        gender="F",
        phone_primary="555-2001",
        address_line1="789 Oak St",
        city="Springfield",
        state="IL",
        zip_code="62701",
        emergency_contact_name="John Anderson",
        emergency_contact_relationship="Son",
        emergency_contact_phone="555-2002",
        primary_diagnosis="Hypertension, Type 2 Diabetes",
        allergies="NKDA",
        code_status="Full Code",
        admission_date=(datetime.utcnow() - timedelta(days=30)).date(),
        status="active",
        fall_risk=False
    )
    patients.append(p1)
    
    # Patient 2: Complex case - multiple conditions, fall risk, hospice
    p2 = Patient(
        facility_id=facility.id,
        medical_record_number="MRN002",
        first_name="Robert",
        last_name="Johnson",
        date_of_birth=datetime(1938, 8, 22).date(),
        gender="M",
        phone_primary="555-2003",
        address_line1="456 Elm Ave",
        city="Springfield",
        state="IL",
        zip_code="62701",
        emergency_contact_name="Linda Johnson",
        emergency_contact_relationship="Daughter",
        emergency_contact_phone="555-2004",
        primary_diagnosis="CHF, COPD, CKD Stage 3",
        secondary_diagnoses="Atrial fibrillation, history of falls",
        allergies="Penicillin (rash), Sulfa drugs (hives)",
        code_status="DNR",
        admission_date=(datetime.utcnow() - timedelta(days=45)).date(),
        status="active",
        fall_risk=True,
        infection_precautions="Contact precautions",
        is_hospice=True,
        hospice_agency="Serenity Hospice Care",
        goals_of_care="Comfort-focused care, symptom management",
        comfort_measures_only=True,
        do_not_hospitalize=True,
        advance_directive_on_file=True,
        polst_on_file=True
    )
    patients.append(p2)
    
    # Patient 3: Moderate complexity - medication reconciliation needed
    p3 = Patient(
        facility_id=facility.id,
        medical_record_number="MRN003",
        first_name="Patricia",
        last_name="Williams",
        date_of_birth=datetime(1955, 3, 10).date(),
        gender="F",
        phone_primary="555-2005",
        address_line1="321 Maple Dr",
        city="Springfield",
        state="IL",
        zip_code="62702",
        emergency_contact_name="David Williams",
        emergency_contact_relationship="Husband",
        emergency_contact_phone="555-2006",
        primary_diagnosis="Post-surgical (hip replacement)",
        secondary_diagnoses="Osteoarthritis, hypothyroidism",
        allergies="Codeine (nausea)",
        code_status="Full Code",
        admission_date=(datetime.utcnow() - timedelta(days=7)).date(),
        status="active",
        fall_risk=True
    )
    patients.append(p3)
    
    # Patient 4: High-risk medications - warfarin, insulin
    p4 = Patient(
        facility_id=facility.id,
        medical_record_number="MRN004",
        first_name="James",
        last_name="Brown",
        date_of_birth=datetime(1945, 11, 30).date(),
        gender="M",
        phone_primary="555-2007",
        address_line1="654 Pine St",
        city="Springfield",
        state="IL",
        zip_code="62701",
        emergency_contact_name="Sarah Brown",
        emergency_contact_relationship="Wife",
        emergency_contact_phone="555-2008",
        primary_diagnosis="Atrial fibrillation, Type 1 Diabetes",
        secondary_diagnoses="History of DVT, neuropathy",
        allergies="NKDA",
        code_status="Full Code",
        admission_date=(datetime.utcnow() - timedelta(days=60)).date(),
        status="active",
        fall_risk=False
    )
    patients.append(p4)
    
    # Patient 5: Recently discharged (for testing discharge workflow)
    p5 = Patient(
        facility_id=facility.id,
        medical_record_number="MRN005",
        first_name="Dorothy",
        last_name="Miller",
        date_of_birth=datetime(1950, 7, 5).date(),
        gender="F",
        phone_primary="555-2009",
        address_line1="987 Cedar Ln",
        city="Springfield",
        state="IL",
        zip_code="62702",
        emergency_contact_name="Michael Miller",
        emergency_contact_relationship="Son",
        emergency_contact_phone="555-2010",
        primary_diagnosis="Pneumonia (resolved)",
        allergies="NKDA",
        code_status="Full Code",
        admission_date=(datetime.utcnow() - timedelta(days=14)).date(),
        discharge_date=(datetime.utcnow() - timedelta(days=2)).date(),
        status="discharged"
    )
    patients.append(p5)
    
    db.session.add_all(patients)
    db.session.commit()
    
    print(f"✅ Created {len(patients)} patients:")
    for p in patients:
        print(f"   - {p.full_name} (MRN: {p.medical_record_number}) - {p.primary_diagnosis}")
    
    return patients


def seed_medications(patients):
    """Create active medications for patients."""
    print("\n💊 Creating medications...")
    
    medications = []
    
    print("   → Patient 1 medications (Mary Anderson)...")
    # Patient 1 (Mary Anderson) - Simple case
    meds_p1 = [
        Medication(
            patient_id=patients[0].id,
            name="Lisinopril",
            medication_name="Lisinopril",
            generic_name="lisinopril",
            dose="10 mg",
            route="PO",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="08:00",
            instructions="Take with food",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=30)).date(),
            indication="Hypertension",
            prescriber="Dr. Smith"
        ),
        Medication(
            patient_id=patients[0].id,
            medication_name="Metformin",
            generic_name="metformin",
            dose="500 mg",
            route="PO",
            frequency="BID",
            frequency_times_per_day=2,
            time_of_day="08:00,18:00",
            instructions="Take with meals",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=30)).date(),
            indication="Type 2 Diabetes",
            prescriber="Dr. Smith"
        )
    ]
    medications.extend(meds_p1)
    
    print("   → Patient 2 medications (Robert Johnson)...")
    # Patient 2 (Robert Johnson) - Complex case with multiple meds
    meds_p2 = [
        Medication(
            patient_id=patients[1].id,
            medication_name="Furosemide",
            generic_name="furosemide",
            dose="40 mg",
            route="PO",
            frequency="BID",
            frequency_times_per_day=2,
            time_of_day="08:00,14:00",
            instructions="Monitor potassium levels",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=45)).date(),
            indication="CHF",
            prescriber="Dr. Jones",
            is_high_risk=True
        ),
        Medication(
            patient_id=patients[1].id,
            medication_name="Albuterol nebulizer",
            generic_name="albuterol",
            dose="2.5 mg",
            route="INH",
            frequency="QID",
            frequency_times_per_day=4,
            time_of_day="08:00,12:00,16:00,20:00",
            instructions="Use with nebulizer",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=45)).date(),
            indication="COPD",
            prescriber="Dr. Jones"
        ),
        Medication(
            patient_id=patients[1].id,
            medication_name="Morphine",
            generic_name="morphine sulfate",
            dose="5 mg",
            route="PO",
            frequency="PRN",
            prn_reason_required=True,
            instructions="For pain or dyspnea. Max 6 doses per 24 hours",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=20)).date(),
            indication="Pain/dyspnea management (hospice)",
            prescriber="Dr. Jones",
            is_controlled_substance=True,
            is_high_risk=True
        ),
        Medication(
            patient_id=patients[1].id,
            medication_name="Digoxin",
            generic_name="digoxin",
            dose="0.125 mg",
            route="PO",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="08:00",
            instructions="Hold if HR < 60. Narrow therapeutic window.",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=45)).date(),
            indication="Atrial fibrillation",
            prescriber="Dr. Jones",
            is_high_risk=True
        )
    ]
    medications.extend(meds_p2)
    
    print("   → Patient 3 medications (Patricia Williams)...")
    # Patient 3 (Patricia Williams) - Post-surgical
    meds_p3 = [
        Medication(
            patient_id=patients[2].id,
            medication_name="Oxycodone",
            generic_name="oxycodone",
            dose="5 mg",
            route="PO",
            frequency="Q4-6H PRN",
            prn_reason_required=True,
            instructions="For moderate to severe pain. Max 6 doses per 24 hours",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=7)).date(),
            indication="Post-surgical pain",
            prescriber="Dr. Wilson",
            is_controlled_substance=True,
            is_high_risk=True
        ),
        Medication(
            patient_id=patients[2].id,
            medication_name="Enoxaparin",
            generic_name="enoxaparin",
            dose="40 mg",
            route="SUBQ",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="20:00",
            instructions="DVT prophylaxis. Rotate injection sites.",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=7)).date(),
            indication="DVT prophylaxis",
            prescriber="Dr. Wilson",
            is_high_risk=True
        ),
        Medication(
            patient_id=patients[2].id,
            medication_name="Levothyroxine",
            generic_name="levothyroxine",
            dose="75 mcg",
            route="PO",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="06:00",
            instructions="Take on empty stomach, 30 min before breakfast",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=365)).date(),
            indication="Hypothyroidism",
            prescriber="Dr. Thompson"
        )
    ]
    medications.extend(meds_p3)
    
    print("   → Patient 4 medications (James Brown)...")
    # Patient 4 (James Brown) - High-risk meds
    meds_p4 = [
        Medication(
            patient_id=patients[3].id,
            medication_name="Warfarin",
            generic_name="warfarin",
            dose="5 mg",
            route="PO",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="18:00",
            instructions="Monitor INR weekly. Target INR 2-3. Avoid foods high in Vitamin K.",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=60)).date(),
            indication="Atrial fibrillation (stroke prevention)",
            prescriber="Dr. Martinez",
            is_high_risk=True,
            requires_monitoring=True
        ),
        Medication(
            patient_id=patients[3].id,
            medication_name="Insulin glargine",
            generic_name="insulin glargine",
            dose="20 units",
            route="SUBQ",
            frequency="Daily",
            frequency_times_per_day=1,
            time_of_day="22:00",
            instructions="Long-acting insulin. Rotate injection sites.",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=60)).date(),
            indication="Type 1 Diabetes",
            prescriber="Dr. Martinez",
            is_high_risk=True,
            requires_monitoring=True
        ),
        Medication(
            patient_id=patients[3].id,
            medication_name="Insulin lispro",
            generic_name="insulin lispro",
            dose="Per sliding scale",
            route="SUBQ",
            frequency="AC + HS",
            frequency_times_per_day=4,
            time_of_day="07:30,12:30,17:30,22:00",
            instructions="Rapid-acting insulin. Check blood glucose before each dose. See sliding scale protocol.",
            status="active",
            start_date=(datetime.utcnow() - timedelta(days=60)).date(),
            indication="Type 1 Diabetes",
            prescriber="Dr. Martinez",
            is_high_risk=True,
            requires_monitoring=True
        )
    ]
    medications.extend(meds_p4)
    
    print(f"   → Adding {len(medications)} medications to database...")
    db.session.add_all(medications)
    print("   → Committing medications...")
    db.session.commit()
    
    print(f"✅ Created {len(medications)} active medications")
    return medications


def seed_visits_and_vitals(patients, nurse):
    """Create recent visits with vital signs."""
    print("\n📋 Creating visits and vital signs...")
    
    visits = []
    vitals = []
    
    # Patient 1 - Routine visit yesterday (completed)
    visit1 = Visit(
        patient_id=patients[0].id,
        nurse_id=nurse.id,
        visit_type="Routine Check",
        scheduled_date=datetime.utcnow() - timedelta(days=1),
        check_in_time=datetime.utcnow() - timedelta(days=1, hours=10),
        check_out_time=datetime.utcnow() - timedelta(days=1, hours=10, minutes=45),
        status="completed",
        chief_complaint="Routine medication administration and vital signs check",
        subjective="Patient reports feeling well. No new complaints. Taking medications as prescribed.",
        objective="Alert and oriented x3. Ambulating independently. No signs of distress.",
        assessment_summary="Stable condition. Hypertension and diabetes well-controlled.",
        plan="Continue current medications. Next visit in 3 days.",
        nurse_signature=f"{nurse.first_name} {nurse.last_name}, RN",
        duration_minutes=45
    )
    visits.append(visit1)
    
    vital1 = VitalSigns(
        patient_id=patients[0].id,
        visit_id=visit1.id,
        recorded_by=nurse.id,
        temperature=Decimal("98.4"),
        pulse=72,
        respiratory_rate=16,
        blood_pressure_systolic=128,
        blood_pressure_diastolic=78,
        oxygen_saturation=98,
        pain_level=0,
        recorded_time=datetime.utcnow() - timedelta(days=1, hours=10, minutes=5)
    )
    vitals.append(vital1)
    
    # Patient 2 - Visit today (in progress) - will document observation for ADR testing
    visit2 = Visit(
        patient_id=patients[1].id,
        nurse_id=nurse.id,
        visit_type="Skilled Nursing Visit",
        scheduled_date=datetime.utcnow(),
        check_in_time=datetime.utcnow() - timedelta(minutes=30),
        status="in_progress",
        chief_complaint="Routine hospice visit - medication administration, symptom assessment"
    )
    visits.append(visit2)
    
    vital2 = VitalSigns(
        patient_id=patients[1].id,
        visit_id=visit2.id,
        recorded_by=nurse.id,
        temperature=Decimal("99.1"),
        pulse=88,
        pulse_rhythm="irregular",
        respiratory_rate=22,
        blood_pressure_systolic=142,
        blood_pressure_diastolic=88,
        oxygen_saturation=92,
        oxygen_delivery="2L nasal cannula",
        pain_level=4,
        recorded_time=datetime.utcnow() - timedelta(minutes=25)
    )
    vitals.append(vital2)
    
    # Patient 3 - Visit scheduled for later today
    visit3 = Visit(
        patient_id=patients[2].id,
        nurse_id=nurse.id,
        visit_type="Post-surgical assessment",
        scheduled_date=datetime.utcnow() + timedelta(hours=2),
        status="scheduled",
        chief_complaint="Post-op hip replacement - wound check, pain management"
    )
    visits.append(visit3)
    
    db.session.add_all(visits + vitals)
    db.session.commit()
    
    print(f"✅ Created {len(visits)} visits and {len(vitals)} vital signs")
    return visits


def seed_medication_administrations(medications, patients, users):
    """Create realistic medication administration history for training scenarios."""
    print("\n💉 Creating medication administration history (past 7 days)...")
    
    administrations = []
    now = datetime.utcnow()
    
    # Get users for varied documentation
    nurse_rn = users[0]  # RN Jane
    nurse_lpn = users[1]  # LPN Bob
    tma = users[4]  # TMA Lisa
    
    # Helper function to create scheduled administrations
    def create_scheduled_admin(med_id, patient_id, nurse, days_back, hour, dose, route, notes=None):
        sched_time = (now - timedelta(days=days_back)).replace(hour=hour, minute=0, second=0, microsecond=0)
        admin_time = sched_time + timedelta(minutes=15)  # Typical 15min after scheduled
        return MedicationAdministration(
            medication_id=med_id,
            patient_id=patient_id,
            administered_by=nurse.id,
            scheduled_time=sched_time,
            administration_time=admin_time,
            status="given",
            route=route,
            dose_given=dose,
            notes=notes
        )
    
    # Patient 1 - Mary Anderson (simple case - HTN + Diabetes)
    # Lisinopril 10mg daily @ 08:00 - consistent adherence, past 7 days
    print("   → Mary Anderson (consistent routine meds)...")
    for day in range(7):
        administrations.append(create_scheduled_admin(
            medications[0].id, patients[0].id, 
            nurse_rn if day % 3 == 0 else nurse_lpn,  # Mix of RN/LPN
            day, 8, "10 mg", "PO",
            "Taken with breakfast" if day == 0 else None
        ))
    
    # Metformin 500mg BID @ 08:00 and 18:00 - past 7 days
    for day in range(7):
        # Morning dose
        administrations.append(create_scheduled_admin(
            medications[1].id, patients[0].id,
            nurse_rn if day % 3 == 0 else tma,  # Mix of RN/TMA
            day, 8, "500 mg", "PO"
        ))
        # Evening dose
        administrations.append(create_scheduled_admin(
            medications[1].id, patients[0].id,
            nurse_lpn if day % 2 == 0 else tma,
            day, 18, "500 mg", "PO"
        ))
    
    # Patient 2 - Robert Johnson (complex hospice - multiple scheduled + PRN)
    print("   → Robert Johnson (complex hospice with PRN use)...")
    
    # Furosemide 40mg BID @ 08:00 and 14:00 - past 7 days
    for day in range(7):
        administrations.append(create_scheduled_admin(
            medications[2].id, patients[1].id,
            nurse_rn if day < 4 else nurse_lpn,
            day, 8, "40 mg", "PO",
            "Weight monitored" if day == 0 else None
        ))
        administrations.append(create_scheduled_admin(
            medications[2].id, patients[1].id,
            nurse_rn if day < 4 else nurse_lpn,
            day, 14, "40 mg", "PO"
        ))
    
    # Albuterol QID @ 08:00, 12:00, 16:00, 20:00 - past 7 days
    for day in range(7):
        for hour in [8, 12, 16, 20]:
            administrations.append(create_scheduled_admin(
                medications[3].id, patients[1].id,
                nurse_rn if hour in [8, 20] else nurse_lpn,
                day, hour, "2.5 mg", "INH",
                "Breath sounds improved" if day == 0 and hour == 8 else None
            ))
    
    # Morphine PRN - variable use for dyspnea/pain (realistic hospice pattern)
    prn_times = [
        (0, 10, "Dyspnea", 8, 5),  # Today morning
        (1, 15, "Dyspnea with exertion", 7, 4),
        (1, 22, "Pain", 6, 4),
        (2, 9, "Dyspnea", 8, 5),
        (3, 14, "Pain in chest", 7, 4),
        (4, 11, "Dyspnea", 9, 5),
        (5, 16, "Pain", 6, 3),
        (6, 21, "Dyspnea at rest", 8, 5)
    ]
    for days_back, hour, reason, before, after in prn_times:
        admin_time = (now - timedelta(days=days_back)).replace(hour=hour, minute=30, second=0, microsecond=0)
        reassess_time = admin_time + timedelta(minutes=30)
        administrations.append(MedicationAdministration(
            medication_id=medications[4].id,
            patient_id=patients[1].id,
            administered_by=nurse_rn.id,
            scheduled_time=None,
            administration_time=admin_time,
            status="given",
            route="PO",
            dose_given="5 mg",
            prn_reason=reason,
            prn_pain_level_before=before,
            prn_pain_level_after=after,
            prn_effectiveness_rating=4 if after < 5 else 3,
            prn_reassessment_time=reassess_time,
            notes=f"{reason}. Symptom level reduced from {before}/10 to {after}/10."
        ))
    
    # Digoxin 0.125mg daily @ 08:00 - past 7 days, one held for low HR
    for day in range(7):
        if day == 3:  # Held one dose
            sched_time = (now - timedelta(days=day)).replace(hour=8, minute=0, second=0, microsecond=0)
            administrations.append(MedicationAdministration(
                medication_id=medications[5].id,
                patient_id=patients[1].id,
                administered_by=nurse_rn.id,
                scheduled_time=sched_time,
                administration_time=sched_time,  # Time of decision to hold
                status="held",
                route="PO",
                dose_given="0.125 mg",
                notes="HELD: HR 54 bpm. MD notified. Will recheck in 4 hours."
            ))
        else:
            administrations.append(create_scheduled_admin(
                medications[5].id, patients[1].id,
                nurse_rn if day % 2 == 0 else nurse_lpn,
                day, 8, "0.125 mg", "PO",
                "HR 68 bpm - within parameters" if day == 0 else None
            ))
    
    # Patient 3 - Patricia Williams (post-surgical)
    print("   → Patricia Williams (post-op pain management)...")
    
    # Oxycodone PRN - decreasing frequency (healing pattern)
    prn_oxy = [
        (0, 14, 6, 2),  # Today - much better
        (1, 9, 7, 3), (1, 21, 6, 2),  # Yesterday - improving
        (2, 6, 8, 4), (2, 14, 7, 3), (2, 22, 7, 3),  # 2 days ago
        (3, 8, 8, 4), (3, 16, 8, 4), (3, 23, 7, 3),  # 3 days ago
        (4, 7, 9, 5), (4, 13, 8, 4), (4, 19, 8, 4),  # 4 days ago - peak pain
        (5, 10, 8, 4), (5, 16, 9, 5), (5, 22, 8, 4),  # 5 days ago
        (6, 12, 9, 5), (6, 18, 9, 5)  # 6 days ago - post-op day 1
    ]
    for days_back, hour, before, after in prn_oxy:
        admin_time = (now - timedelta(days=days_back)).replace(hour=hour, minute=0, second=0, microsecond=0)
        reassess_time = admin_time + timedelta(minutes=30)
        administrations.append(MedicationAdministration(
            medication_id=medications[6].id,
            patient_id=patients[2].id,
            administered_by=nurse_rn.id if days_back > 3 else nurse_lpn.id,
            scheduled_time=None,
            administration_time=admin_time,
            status="given",
            route="PO",
            dose_given="5 mg",
            prn_reason="Post-surgical incision pain",
            prn_pain_level_before=before,
            prn_pain_level_after=after,
            prn_effectiveness_rating=5 if after <= 3 else 4,
            prn_reassessment_time=reassess_time,
            notes=f"Pain reduced {before}/10 → {after}/10. {'Able to ambulate' if after < 4 else 'Resting in bed'}."
        ))
    
    # Enoxaparin 40mg daily @ 20:00 - DVT prophylaxis, past 7 days
    for day in range(7):
        sites = ["Left abdomen", "Right abdomen", "Left thigh", "Right thigh"]
        administrations.append(create_scheduled_admin(
            medications[7].id, patients[2].id,
            nurse_rn if day % 2 == 0 else nurse_lpn,
            day, 20, "40 mg", "SUBQ",
            f"Injection site: {sites[day % 4]}. No bleeding or bruising noted." if day == 0 else f"{sites[day % 4]}"
        ))
    
    # Levothyroxine 75mcg daily @ 06:00 - consistent, past 7 days
    for day in range(7):
        administrations.append(create_scheduled_admin(
            medications[8].id, patients[2].id,
            nurse_rn if day < 3 else nurse_lpn,
            day, 6, "75 mcg", "PO",
            "Taken on empty stomach" if day == 0 else None
        ))
    
    # Patient 4 - James Brown (high-risk anticoagulation)
    print("   → James Brown (warfarin management)...")
    
    # Warfarin 5mg daily @ 18:00 - past 7 days with INR monitoring
    for day in range(7):
        inr_note = None
        if day == 0:
            inr_note = "INR 2.4 (therapeutic). Continue current dose."
        elif day == 3:
            inr_note = "INR checked today: 2.6 (therapeutic range)."
        
        administrations.append(create_scheduled_admin(
            medications[9].id, patients[3].id,
            nurse_rn,  # RN only for warfarin
            day, 18, "5 mg", "PO",
            inr_note
        ))
    
    # Patient 1 - Add sliding scale insulin administrations (realistic BG management)
    print("   → Mary Anderson (sliding scale insulin - added)...")
    insulin_med_id = None
    for med in medications:
        if med.patient_id == patients[0].id and 'Insulin' in (med.medication_name or ''):
            insulin_med_id = med.id
            break
    
    if insulin_med_id:
        # AC (before meals) and HS (bedtime) pattern - 4 times daily
        insulin_schedule = [
            (0, 7, 30, 185, 2),  # Today breakfast - BG 185
            (0, 11, 30, 165, 0),  # Today lunch - BG 165 (no insulin needed)
            (0, 17, 0, 220, 4),  # Today dinner - BG 220
            (1, 7, 30, 195, 2),  # Yesterday breakfast
            (1, 11, 30, 155, 0),  # Yesterday lunch
            (1, 17, 0, 175, 2),  # Yesterday dinner
            (1, 21, 0, 145, 0),  # Yesterday bedtime
            (2, 7, 30, 210, 4),  # 2 days ago breakfast
            (2, 11, 30, 180, 2),  # 2 days ago lunch
        ]
        
        for days_back, hour, minute, bg_reading, units in insulin_schedule:
            admin_time = (now - timedelta(days=days_back)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            dose = f"{units} units" if units > 0 else "0 units"
            status = "given" if units > 0 else "held"
            notes = f"BG {bg_reading} mg/dL. "
            if units == 0:
                notes += "No insulin needed per sliding scale."
            else:
                notes += f"Administered {units} units per sliding scale protocol."
            
            administrations.append(MedicationAdministration(
                medication_id=insulin_med_id,
                patient_id=patients[0].id,
                administered_by=nurse_rn.id if days_back < 2 else tma.id,
                scheduled_time=admin_time,
                administration_time=admin_time + timedelta(minutes=5) if units > 0 else admin_time,  # Decision time if held
                status=status,
                route="SQ",
                dose_given=dose,
                notes=notes
            ))
    
    db.session.add_all(administrations)
    db.session.commit()
    
    print(f"✅ Created {len(administrations)} medication administrations (7-day realistic history)")
    return administrations


def seed_adr_scenario(patients, nurse, medications):
    """Create ADR detection scenario - observation that triggers alert."""
    print("\n⚠️  Creating ADR detection scenario...")
    
    # Patient 2 (Robert Johnson on Digoxin) - will create observation for bradycardia
    # This should trigger ADR alert for digoxin toxicity
    
    observation = PatientObservation(
        patient_id=patients[1].id,
        facility_id=patients[1].facility_id,
        observed_by_user_id=nurse.id,
        observation_type="VITAL_SIGN",
        observation_category="cardiovascular",
        observation_text="Heart rate 48 bpm (irregular). Patient reports mild dizziness when standing. Visual disturbances (yellow-green halos noted).",
        severity_rating=7,
        related_vital_signs={
            "heart_rate": 48,
            "blood_pressure": "142/88",
            "rhythm": "irregular"
        },
        observation_datetime=datetime.utcnow() - timedelta(minutes=15)
    )
    
    db.session.add(observation)
    db.session.flush()
    
    # First create the known adverse reaction for digoxin toxicity
    digoxin_toxicity_adr = MedicationAdverseReaction(
        medication_name="Digoxin",
        generic_name="digoxin",
        drug_class="Cardiac Glycoside",
        reaction_name="Digoxin Toxicity",
        reaction_description="Toxic levels of digoxin causing cardiac and neurological effects",
        severity=MedicationAdverseReaction.SEVERITY_MAJOR,
        likelihood=MedicationAdverseReaction.LIKELIHOOD_COMMON,
        typical_onset_days=3,
        observable_symptoms=["nausea", "vomiting", "dizziness", "visual_disturbances", "confusion"],
        vital_sign_changes={"heart_rate": "decreased", "heart_rhythm": "irregular"},
        lab_abnormalities=["elevated_digoxin_level", "hypokalemia"],
        behavioral_changes=["confusion", "lethargy"],
        monitoring_recommendations="Monitor heart rate, rhythm, digoxin levels, and potassium",
        nursing_interventions=[
            "Hold next dose if signs of toxicity",
            "Monitor vital signs closely", 
            "Assess for visual changes (yellow-green halos)",
            "Document all symptoms",
            "Notify provider"
        ],
        provider_notification_guidance="Report bradycardia, visual changes, GI symptoms. Provider may order digoxin level, potassium, EKG, and may hold or adjust dosing",
        when_to_escalate="STAT notification if heart rate <50, new arrhythmia, severe confusion, or syncope",
        risk_factors=["elderly", "renal_impairment", "hypokalemia", "concurrent_diuretics"]
    )
    db.session.add(digoxin_toxicity_adr)
    db.session.flush()
    
    # Get the digoxin medication
    digoxin_med = next((m for m in medications if m.medication_name == "Digoxin"), None)
    
    # Create corresponding ADR alert (simulating auto-detection)
    adr_alert = ADRAlert(
        patient_id=patients[1].id,
        facility_id=patients[1].facility_id,
        medication_id=digoxin_med.id,
        observation_id=observation.id,
        known_adr_id=digoxin_toxicity_adr.id,
        suspected_reaction="Digoxin Toxicity",
        alert_summary="Potential digoxin toxicity detected: Bradycardia (HR 48 bpm), visual disturbances (yellow-green halos), dizziness. Patient on digoxin 0.125mg daily.",
        confidence_level=ADRAlert.CONFIDENCE_HIGH,
        severity=MedicationAdverseReaction.SEVERITY_MAJOR,
        matching_symptoms=["dizziness", "visual_disturbances"],
        matching_vital_signs=["bradycardia", "irregular_rhythm"],
        correlation_score=0.85,
        medication_start_date=datetime.utcnow().date() - timedelta(days=30),
        days_since_medication_start=30,
        expected_onset_match=True,
        patient_risk_factors=["elderly", "renal_impairment", "concurrent_diuretics"],
        nursing_interventions=[
            "Hold next digoxin dose",
            "Monitor heart rate and rhythm closely",
            "Assess for additional symptoms",
            "Document all findings"
        ],
        provider_notification_needed=True,
        provider_notification_urgency="URGENT",
        provider_notification_guidance="Patient showing signs of digoxin toxicity (bradycardia 48bpm, visual halos, dizziness). Current dose 0.125mg daily. Last dose given this morning.",
        suggested_provider_orders=[
            "Digoxin level (therapeutic range 0.5-2.0 ng/mL)",
            "Potassium level",
            "12-lead EKG",
            "Hold digoxin pending lab results"
        ],
        requires_immediate_action=True,
        escalation_guidance="URGENT notification needed - bradycardia with visual changes suggests toxicity",
        is_hospice_patient=True,
        hospice_comfort_focus="Balance cardiac management with comfort goals; discuss risks/benefits with patient and family",
        status=ADRAlert.STATUS_NEW
    )
    
    db.session.add(adr_alert)
    db.session.commit()
    
    print(f"✅ Created ADR alert scenario: Digoxin toxicity for {patients[1].full_name}")
    return observation, adr_alert


def seed_reconciliation_scenario(patients, nurse):
    """Create medication reconciliation scenario with discrepancies."""
    print("\n🔄 Creating medication reconciliation scenario...")
    
    # Patient 3 (Patricia Williams) - post-surgical, needs reconciliation
    # Home meds different from current orders
    
    home_medications = [
        {
            "medication_name": "Levothyroxine",
            "dose": "75 mcg",
            "frequency": "Daily",
            "route": "PO"
        },
        {
            "medication_name": "Ibuprofen",
            "dose": "400 mg",
            "frequency": "TID PRN",
            "route": "PO",
            "note": "For arthritis pain"
        },
        {
            "medication_name": "Vitamin D",
            "dose": "2000 IU",
            "frequency": "Daily",
            "route": "PO"
        }
    ]
    
    reconciliation = MedicationReconciliation(
        patient_id=patients[2].id,
        facility_id=patients[2].facility_id,
        initiated_by_user_id=nurse.id,
        reconciliation_type=MedicationReconciliation.TYPE_ADMISSION,
        transition_from="Community Hospital (post-surgical)",
        transition_to="Home with Home Health",
        source_document_type="Hospital discharge summary",
        source_document_date=datetime.utcnow().date() - timedelta(days=1),
        source_medications=home_medications,
        current_medications=[],  # Will be populated from active meds
        status=MedicationReconciliation.STATUS_IN_REVIEW,
        requires_pharmacist_review=True,
        clinical_summary="Post-op hip replacement, on anticoagulation therapy (enoxaparin)",
        review_started_at=datetime.utcnow() - timedelta(hours=6)
    )
    
    db.session.add(reconciliation)
    db.session.flush()
    
    # Create discrepancies (auto-detected)
    discrepancies = []
    
    # Discrepancy 1: Ibuprofen not on current med list (intentionally held due to surgery)
    disc1 = MedicationDiscrepancy(
        reconciliation_id=reconciliation.id,
        medication_name="Ibuprofen",
        discrepancy_type=MedicationDiscrepancy.TYPE_DISCONTINUED,
        severity=MedicationDiscrepancy.SEVERITY_HIGH,
        source_details={
            "medication_name": "Ibuprofen",
            "dose": "400 mg",
            "frequency": "TID PRN",
            "route": "PO",
            "indication": "Arthritis pain"
        },
        current_details=None,
        clinical_concern="Home medication Ibuprofen 400mg TID PRN not found in current orders",
        potential_impact="High-risk: NSAIDs contraindicated post-surgery due to bleeding risk and interaction with anticoagulant therapy (enoxaparin)",
        requires_pharmacist_input=True,
        resolution_action=MedicationDiscrepancy.ACTION_PENDING
    )
    discrepancies.append(disc1)
    
    # Discrepancy 2: Oxycodone added (new post-surgical med)
    disc2 = MedicationDiscrepancy(
        reconciliation_id=reconciliation.id,
        medication_name="Oxycodone",
        discrepancy_type=MedicationDiscrepancy.TYPE_NEW_MED,
        severity=MedicationDiscrepancy.SEVERITY_MEDIUM,
        source_details=None,
        current_details={
            "medication_name": "Oxycodone",
            "dose": "5 mg",
            "frequency": "Q4-6H PRN",
            "route": "PO",
            "indication": "Post-surgical pain"
        },
        clinical_concern="New medication Oxycodone 5mg Q4-6H PRN added to regimen",
        potential_impact="New controlled substance for post-operative pain management. Monitor for effectiveness and side effects.",
        requires_pharmacist_input=True,
        resolution_action=MedicationDiscrepancy.ACTION_PENDING
    )
    discrepancies.append(disc2)
    
    # Discrepancy 3: Vitamin D missing (omitted from orders)
    disc3 = MedicationDiscrepancy(
        reconciliation_id=reconciliation.id,
        medication_name="Vitamin D",
        discrepancy_type=MedicationDiscrepancy.TYPE_DISCONTINUED,
        severity=MedicationDiscrepancy.SEVERITY_LOW,
        source_details={
            "medication_name": "Vitamin D",
            "dose": "2000 IU",
            "frequency": "Daily",
            "route": "PO"
        },
        current_details=None,
        clinical_concern="Home medication Vitamin D 2000 IU daily not found in current orders",
        potential_impact="Low-risk: Vitamin D supplementation for bone health. Should be continued.",
        requires_pharmacist_input=False,
        resolution_action=MedicationDiscrepancy.ACTION_PENDING
    )
    discrepancies.append(disc3)
    
    db.session.add_all(discrepancies)
    db.session.commit()
    
    print(f"✅ Created reconciliation with {len(discrepancies)} discrepancies for {patients[2].full_name}")
    return reconciliation, discrepancies


def print_summary(org, facility, users, patients):
    """Print summary of seed data."""
    print("\n" + "="*60)
    print("🎉 SEED DATA CREATION COMPLETE!")
    print("="*60)
    
    print(f"\n📊 Summary:")
    print(f"   Organization: {org.name}")
    print(f"   Facility: {facility.name}")
    print(f"   Users: {len(users)} (RN, LPN, Pharmacist, Admin)")
    print(f"   Patients: {len(patients)} (varying complexity)")
    print(f"   Active Medications: {Medication.query.filter_by(status='active').count()}")
    print(f"   Recent Visits: {Visit.query.count()}")
    print(f"   ADR Alerts: {ADRAlert.query.count()}")
    print(f"   Reconciliations: {MedicationReconciliation.query.count()}")
    
    print(f"\n🔐 Login Credentials (all passwords: 'password123'):")
    for user in users:
        print(f"   - Username: {user.username:15} Role: {user.role:12} Name: {user.first_name} {user.last_name}")
    
    print(f"\n🧪 Test Scenarios Created:")
    print(f"   ✅ Simple case: Mary Anderson (stable, routine meds)")
    print(f"   ✅ Complex hospice: Robert Johnson (multiple conditions, fall risk, PRN morphine)")
    print(f"   ✅ Post-surgical: Patricia Williams (reconciliation needed, pain management)")
    print(f"   ✅ High-risk meds: James Brown (warfarin, insulin)")
    print(f"   ✅ Discharged patient: Dorothy Miller")
    print(f"   ✅ ADR Alert: Digoxin toxicity (bradycardia, visual changes)")
    print(f"   ✅ Medication Reconciliation: 3 discrepancies (omission, addition, supplement)")
    
    print(f"\n🚀 Ready for Testing!")
    print(f"   Use the API endpoints to test full clinical workflows")
    print("="*60 + "\n")


def main():
    """Main seed data creation function."""
    app = create_app()
    
    with app.app_context():
        print("🌱 Starting seed data creation...")
        print("="*60)
        
        # Create tables first
        db.create_all()
        print("\n✅ Database tables ensured")
        
        # Clear existing data
        response = input("\n⚠️  Clear existing data? (y/n): ")
        if response.lower() == 'y':
            clear_data()
        
        # Create data
        org, facility1, facility2 = seed_organizations_and_facilities()
        users = seed_users(facility1)  # Returns list: [rn, lpn, pharmacist, admin, tma, cna, hha]
        rn, lpn, pharmacist, admin = users[0], users[1], users[2], users[3]
        patients = seed_patients(facility1)
        medications = seed_medications(patients)
        visits = seed_visits_and_vitals(patients, rn)
        administrations = seed_medication_administrations(medications, patients, users)
        observation, adr_alert = seed_adr_scenario(patients, rn, medications)
        reconciliation, discrepancies = seed_reconciliation_scenario(patients, rn)
        
        # Print summary
        print_summary(org, facility1, [rn, lpn, pharmacist, admin], patients)


if __name__ == "__main__":
    main()
