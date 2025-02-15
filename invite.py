import uuid
from datetime import timedelta

def generate_event_link(event_name, event_start_time):
    """Generates a Google Calendar event creation link."""
    event_end_time = event_start_time + timedelta(hours=1)
    start_time_str = event_start_time.strftime('%Y%m%dT%H%M%SZ')
    end_time_str = event_end_time.strftime('%Y%m%dT%H%M%SZ')
    event_link = (
        f"https://calendar.google.com/calendar/r/eventedit?"
        f"text={event_name}&"
        f"dates={start_time_str}/{end_time_str}"
    )
    return event_link

def generate_event_id_and_store(chat_id, events_data):
    """Generates a unique event ID and stores it in event data."""
    event_id = str(uuid.uuid4())
    if 'events' not in events_data:
        events_data['events'] = {}
    events_data['events'][event_id] = {
        'id': event_id,
        'chat_id': chat_id,
        'name': events_data[chat_id]['name'],
        'date': events_data[chat_id]['date'],
        'time': events_data[chat_id]['time']
    }
    return event_id #return