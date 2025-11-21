#!/usr/bin/env python3
"""Generate scheduled medication administrations for today's MAR."""
from datetime import datetime, date, time as dt_time
from app import create_app, db
from app.models.medication import Medication, MedicationAdministration

app = create_app()

def generate_today_schedule():
    """Generate scheduled administrations for all active medications for today."""
    with app.app_context():
        today = date.today()
        
        # Get all active scheduled (non-PRN) medications
        medications = Medication.query.filter_by(status='active').filter(
            Medication.is_prn == False
        ).all()
        
        print(f'Generating MAR schedule for {today}')
        print(f'Found {len(medications)} active scheduled medications\n')
        
        created_count = 0
        
        for med in medications:
            if not med.time_of_day:
                print(f'⚠️  Skipping {med.medication_name} (Patient {med.patient_id}) - no time_of_day')
                continue
            
            # Parse scheduled times
            times = [t.strip() for t in med.time_of_day.split(',')]
            
            for time_str in times:
                try:
                    # Parse time (format: HH:MM)
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_dt = datetime.combine(today, dt_time(hour, minute))
                    
                    # Check if already exists
                    existing = MedicationAdministration.query.filter_by(
                        medication_id=med.id,
                        scheduled_time=scheduled_dt
                    ).first()
                    
                    if existing:
                        print(f'  ✓ Already scheduled: {med.medication_name} at {time_str}')
                        continue
                    
                    # Create new scheduled administration
                    # Note: DB schema requires administration_time to be NOT NULL
                    # For scheduled doses, we set it equal to scheduled_time initially
                    admin = MedicationAdministration(
                        medication_id=med.id,
                        patient_id=med.patient_id,
                        scheduled_time=scheduled_dt,
                        administration_time=scheduled_dt,  # Will be updated when actually given
                        status='scheduled',
                        dose_given=med.dose,
                        route=med.route,
                        administered_by=1  # System/scheduler user
                    )
                    
                    db.session.add(admin)
                    created_count += 1
                    print(f'  ✅ Created: {med.medication_name} at {time_str} (Patient {med.patient_id})')
                    
                except ValueError as e:
                    print(f'  ❌ Error parsing time "{time_str}" for {med.medication_name}: {e}')
        
        if created_count > 0:
            db.session.commit()
            print(f'\n✅ Successfully created {created_count} scheduled administrations')
        else:
            print(f'\n✓ All schedules already exist')

if __name__ == '__main__':
    generate_today_schedule()
