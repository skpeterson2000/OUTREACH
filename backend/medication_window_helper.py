#!/usr/bin/env python3
"""
Medication Administration Time Window Helper

Standard Practice:
- Medications should be administered within 1 hour before or after the scheduled time
- This is the standard "administration window" or "grace period"
- Some facilities may adjust this (30min, 2hr) based on policy

Example:
- Medication scheduled for 08:00
- Can be given between 07:00 and 09:00
- If given at 07:30 or 08:45, it's "on time"
- If given at 06:45 or 09:15, it's "late" or "early"

For time-critical medications (insulin, antibiotics, cardiac meds):
- Window may be narrower (30 minutes)
- Should be documented in special_instructions
"""

from datetime import datetime, timedelta

def calculate_administration_window(scheduled_time, grace_minutes=60):
    """
    Calculate the acceptable administration window for a medication.
    
    Args:
        scheduled_time (datetime): The scheduled administration time
        grace_minutes (int): Minutes before/after scheduled time (default: 60)
        
    Returns:
        tuple: (window_start, window_end, is_overdue, is_upcoming)
    """
    window_start = scheduled_time - timedelta(minutes=grace_minutes)
    window_end = scheduled_time + timedelta(minutes=grace_minutes)
    now = datetime.utcnow()
    
    is_within_window = window_start <= now <= window_end
    is_overdue = now > window_end
    is_upcoming = now < window_start
    
    return {
        'window_start': window_start,
        'window_end': window_end,
        'is_within_window': is_within_window,
        'is_overdue': is_overdue,
        'is_upcoming': is_upcoming,
        'minutes_until_window_opens': max(0, int((window_start - now).total_seconds() / 60)),
        'minutes_overdue': max(0, int((now - window_end).total_seconds() / 60))
    }

def is_administration_on_time(scheduled_time, actual_time, grace_minutes=60):
    """
    Determine if a medication was administered within the acceptable window.
    
    Args:
        scheduled_time (datetime): When it was scheduled
        actual_time (datetime): When it was actually given
        grace_minutes (int): Acceptable variance in minutes
        
    Returns:
        bool: True if within window, False if late/early
    """
    window_start = scheduled_time - timedelta(minutes=grace_minutes)
    window_end = scheduled_time + timedelta(minutes=grace_minutes)
    
    return window_start <= actual_time <= window_end

def get_time_status_color(scheduled_time, actual_time=None, grace_minutes=60):
    """
    Get color code for medication timing status.
    
    Returns:
        str: 'green' (on time), 'yellow' (upcoming/within window), 
             'orange' (slightly late), 'red' (overdue)
    """
    now = datetime.utcnow()
    window_start = scheduled_time - timedelta(minutes=grace_minutes)
    window_end = scheduled_time + timedelta(minutes=grace_minutes)
    
    if actual_time:
        # Already administered - check if it was on time
        if window_start <= actual_time <= window_end:
            return 'green'  # On time
        else:
            return 'orange'  # Late or early
    else:
        # Not yet administered - check current time
        if now < window_start:
            return 'gray'  # Upcoming, not yet in window
        elif window_start <= now <= window_end:
            return 'yellow'  # Within window, should give now
        elif now > window_end:
            minutes_late = int((now - window_end).total_seconds() / 60)
            if minutes_late < 120:  # Less than 2 hours late
                return 'orange'
            else:
                return 'red'  # Seriously overdue
    
    return 'gray'


# Example usage
if __name__ == '__main__':
    # Example: Medication scheduled for 08:00 today
    scheduled = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    print("Medication Administration Window Calculator")
    print("=" * 50)
    print(f"Scheduled time: {scheduled.strftime('%H:%M')}")
    print()
    
    window = calculate_administration_window(scheduled, grace_minutes=60)
    print(f"Administration window: {window['window_start'].strftime('%H:%M')} - {window['window_end'].strftime('%H:%M')}")
    print(f"Within window: {window['is_within_window']}")
    print(f"Overdue: {window['is_overdue']}")
    print(f"Upcoming: {window['is_upcoming']}")
    
    if window['is_overdue']:
        print(f"⚠️  OVERDUE by {window['minutes_overdue']} minutes")
    elif window['is_within_window']:
        print("✅ Within administration window - can give now")
    else:
        print(f"⏰ Opens in {window['minutes_until_window_opens']} minutes")
