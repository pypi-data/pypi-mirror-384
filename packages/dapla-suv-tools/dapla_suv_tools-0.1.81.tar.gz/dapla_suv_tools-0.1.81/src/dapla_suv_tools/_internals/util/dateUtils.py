import pytz
from dateutil import parser
from datetime import datetime

def find_and_convert_datetime_fields(content):
    """
    Recursively scans the content for fields that look like datetime strings
    and converts them to local time if found.

    Parameters
    ----------
    content : dict or list
        The JSON content to scan, either a dictionary or a list of dictionaries.

    Returns
    -------
    dict or list
        A dictionary or list with datetime values converted to local time.
    """
    datetime_fields = {}
    local_tz = pytz.timezone("Europe/Oslo")  
    
    if isinstance(content, list):  # Check if content is a list
        for item in content:
            find_and_convert_datetime_fields(item)  # Process each dictionary in the list

    elif isinstance(content, dict):  # Process dictionary as usual
        for key, value in content.items():
            if isinstance(value, str):
                try:
                    # Check if the value has a pattern resembling a datetime (rough check for "T" in ISO strings)
                    if 'T' in value or '-' in value or ':' in value:
                        # Parse the datetime string with format detection
                        parsed_date = parser.parse(value)
                        
                        # Skip if date-only
                        if parsed_date.hour == 0 and parsed_date.minute == 0 and parsed_date.second == 0:
                            continue
                    
                        # timezone information
                        if parsed_date.tzinfo is None:
                            parsed_date = parsed_date.replace(tzinfo=pytz.utc)
                        
                        # Convert UTC to local time
                        local_datetime = parsed_date.astimezone(local_tz)
                        formatted_datetime = local_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                        
                        # Store and update with local time version
                        datetime_fields[key] = formatted_datetime
                        content[key] = formatted_datetime
                except (ValueError, TypeError):
                    continue

    return datetime_fields






def convert_to_utc(dt: datetime | None) -> datetime | None:
    """
    Converts a datetime to UTC. Assumes the datetime is in the local timezone if naive.

    Parameters
    ----------
    dt : datetime or None
        The datetime to convert to UTC.

    Returns
    -------
    datetime or None
        The datetime in UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:  # If naive, assume it's in local timezone and convert
        local_tz = pytz.timezone("Europe/Oslo")
        dt = local_tz.localize(dt)
    return dt.astimezone(pytz.utc)  # Convert to UTC
