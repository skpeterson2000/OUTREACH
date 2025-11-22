#!/usr/bin/env python3
"""
Reset ADR Alert Acknowledgments - Admin Utility

This script resets all acknowledgments to allow fresh testing of the alert system.
Use this for testing, training, or when starting a new shift.
"""

from app import create_app, db
from app.models import ADRAlertAcknowledgment, ADRAlert

def reset_acknowledgments():
    """Reset all acknowledgments and set alerts back to NEW status."""
    app = create_app()
    with app.app_context():
        # Count before
        count_before = ADRAlertAcknowledgment.query.count()
        alerts = ADRAlert.query.filter(ADRAlert.status != 'RESOLVED').all()
        
        print("=" * 60)
        print("ADR ALERT ACKNOWLEDGMENT RESET")
        print("=" * 60)
        print(f"\n📊 Current State:")
        print(f"   - Acknowledgments in database: {count_before}")
        print(f"   - Active alerts: {len(alerts)}")
        
        # Delete all acknowledgments
        ADRAlertAcknowledgment.query.delete()
        
        # Reset all non-resolved alerts to NEW status
        for alert in alerts:
            alert.status = 'NEW'
            alert.acknowledged_by_user_id = None
            alert.acknowledged_at = None
        
        db.session.commit()
        
        count_after = ADRAlertAcknowledgment.query.count()
        
        print(f"\n✅ Reset Complete:")
        print(f"   - Deleted {count_before} acknowledgments")
        print(f"   - Reset {len(alerts)} alerts to NEW status")
        print(f"   - Current acknowledgments: {count_after}")
        print("\n💡 All staff will need to re-acknowledge alerts on their next shift.")
        print("=" * 60)

if __name__ == '__main__':
    import sys
    
    print("\n⚠️  WARNING: This will delete all acknowledgments!")
    print("All active alerts will return to NEW status.")
    
    if '--force' not in sys.argv:
        confirm = input("\nAre you sure you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Reset cancelled")
            sys.exit(0)
    
    reset_acknowledgments()
