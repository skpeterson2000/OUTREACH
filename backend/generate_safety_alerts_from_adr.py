"""Auto-create safety alerts for unlicensed staff based on active ADR alerts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    ADRAlert, PatientSafetyAlert, create_safety_alert_from_adr, User
)

app = create_app()

with app.app_context():
    print("🚨 Auto-generating patient safety alerts from ADR alerts...")
    print()
    
    # Find a licensed nurse to attribute creation to
    creator = User.query.filter_by(role='RN').first()
    if not creator:
        print("❌ No RN found in database - cannot create safety alerts")
        print("   Safety alerts must be created by licensed staff")
        exit(1)
    
    # Get all active ADR alerts
    active_adr_alerts = ADRAlert.query.filter(
        ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
    ).all()
    
    if not active_adr_alerts:
        print("ℹ️  No active ADR alerts found")
        exit(0)
    
    print(f"📋 Found {len(active_adr_alerts)} active ADR alerts")
    print()
    
    created_count = 0
    skipped_count = 0
    
    for adr_alert in active_adr_alerts:
        # Check if safety alert already exists for this ADR
        existing = PatientSafetyAlert.query.filter_by(
            source_type='ADR_ALERT',
            source_id=adr_alert.id,
            active=True
        ).first()
        
        if existing:
            print(f"   ⏭️  ADR Alert #{adr_alert.id} already has safety alert #{existing.id}")
            skipped_count += 1
            continue
        
        # Create safety alert
        safety_alert = create_safety_alert_from_adr(adr_alert, creator.id)
        db.session.add(safety_alert)
        db.session.flush()  # Get the ID
        
        print(f"   ✅ Created Safety Alert #{safety_alert.id}: {safety_alert.alert_title}")
        print(f"      Patient ID: {safety_alert.patient_id}")
        print(f"      Alert Type: {safety_alert.alert_type}")
        print(f"      Severity: {safety_alert.severity}")
        if safety_alert.requires_orthostatic_vitals:
            print(f"      ⚠️  Requires orthostatic vital signs assessment")
        if safety_alert.trigger_on_low_hr:
            print(f"      💓 Triggers on HR < {safety_alert.hr_threshold} bpm")
        if safety_alert.trigger_on_low_bp:
            print(f"      🩸 Triggers on BP systolic < {safety_alert.bp_systolic_threshold}")
        print()
        
        created_count += 1
    
    # Commit all changes
    db.session.commit()
    
    print()
    print("=" * 70)
    print(f"✅ Safety alert generation complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped (already exists): {skipped_count}")
    print(f"   Total: {len(active_adr_alerts)}")
    print()
    print("🔔 These alerts are now visible to ALL staff (including CNAs, HHAs)")
    print("   during vital signs collection and patient care activities.")
