#!/usr/bin/env python3
"""
Create ADR Alert Acknowledgments table for multi-user, shift-based acknowledgments.
"""

from app import create_app, db

def upgrade():
    """Create the adr_alert_acknowledgments table."""
    app = create_app()
    with app.app_context():
        # Create all tables (will only create missing ones)
        db.create_all()
        print("✅ Database tables created/updated successfully")
        print("   - adr_alert_acknowledgments table added")

if __name__ == '__main__':
    upgrade()
