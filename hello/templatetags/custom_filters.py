from django import template
import hashlib

register = template.Library()

@register.filter
def ordinal(value):
    """Convert integer to ordinal string (1 -> 1st, 2 -> 2nd, etc.)"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    
    return f"{value}{suffix}"


@register.filter
def schedule_height(duration_minutes):
    """
    Calculate height in pixels for a schedule block.
    60px = 30 minutes, so 2px per minute.
    Exact duration - no padding.
    """
    try:
        duration_minutes = int(duration_minutes)
    except (ValueError, TypeError):
        duration_minutes = 0

    # 2 pixels per minute (60px per 30 min slot)
    total_height = duration_minutes * 2
    return int(total_height)


@register.filter
def schedule_top(start_time):
    """
    Calculate the exact top position in pixels from 7:00 AM baseline.
    Each minute = 2px (30 minutes = 60px)
    
    Grid lines are at:
    - 7:00 -> 0px
    - 7:30 -> 60px
    - 8:00 -> 120px
    - 8:30 -> 180px
    etc.
    
    Examples:
    - 7:00 -> 0px (on the 7:00 line)
    - 7:30 -> 60px (on the 7:30 line)
    - 7:35 -> 70px (5 min = 10px below 7:30 line)
    - 10:00 -> 360px (on the 10:00 line)
    """
    try:
        hours, minutes = map(int, str(start_time).split(':'))
        total_minutes = (hours * 60) + minutes
        base_minutes = 7 * 60  # 7:00 AM baseline
        minutes_from_start = total_minutes - base_minutes
        
        # 2 pixels per minute
        return int(minutes_from_start * 2)
    except Exception:
        return 0


@register.filter
def time_12hr(value):
    """Format 24-hour time strings into 12-hour labels."""
    try:
        hours, minutes = map(int, str(value).split(':'))
        suffix = 'AM' if hours < 12 else 'PM'
        hour_12 = hours % 12 or 12
        return f"{hour_12}:{minutes:02d} {suffix}"
    except Exception:
        return value


@register.filter
def auto_color(value):
    """
    Generate a distinct color for a course based on its code.
    Returns a hex color code.
    """
    color_palette = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Blue
        '#FFA07A',  # Light Salmon
        '#98D8C8',  # Mint
        '#F7DC6F',  # Yellow
        '#BB8FCE',  # Purple
        '#85C1E2',  # Sky Blue
        '#F8B88B',  # Peach
        '#52B788',  # Green
        '#FF8FAB',  # Pink
        '#FFB84D',  # Orange
        '#A8DADC',  # Light Blue
        '#E76F51',  # Coral
        '#2A9D8F',  # Dark Teal
        '#E9C46A',  # Gold
        '#F4A261',  # Sandy Brown
        '#8E7CC3',  # Lavender
        '#6A4C93',  # Deep Purple
        '#00B4D8',  # Bright Blue
    ]
    
    if value:
        hash_object = hashlib.md5(str(value).encode())
        hash_int = int(hash_object.hexdigest(), 16)
        return color_palette[hash_int % len(color_palette)]
    
    return '#FFA726'


@register.filter
def rgba_25(hex_color):
    """
    Convert a hex color (#RRGGBB or RRGGBB) into an rgba string with 0.25 alpha.
    If input is invalid, return a sensible fallback rgba(255,167,38,0.25).
    """
    if not hex_color:
        return 'rgba(255,167,38,0.25)'

    c = str(hex_color).strip()
    if c.startswith('#'):
        c = c[1:]

    if len(c) == 3:
        try:
            r = int(c[0]*2, 16)
            g = int(c[1]*2, 16)
            b = int(c[2]*2, 16)
            return f'rgba({r},{g},{b},0.25)'
        except Exception:
            return 'rgba(255,167,38,0.25)'

    if len(c) != 6:
        return 'rgba(255,167,38,0.25)'

    try:
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        return f'rgba({r},{g},{b},0.25)'
    except Exception:
        return 'rgba(255,167,38,0.25)'