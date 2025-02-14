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
    return event_id

def invite_participants(bot, message, events_data):
    """Sends invitations to event participants."""
    chat_id = message.chat.id
    if chat_id not in events_data or 'name' not in events_data[chat_id]:
        bot.send_message(chat_id, "❌ You need to create an event first to invite participants.")
        return
    event_name = events_data[chat_id]['name']
    event_date = events_data[chat_id]['date']
    event_time = events_data[chat_id]['time']
    bot.send_message(chat_id, "📩 Enter the names of participants separated by commas:")
    bot.register_next_step_handler(message, process_invitees, bot, event_name, event_date, event_time)

def process_invitees(message, bot, event_name, event_date, event_time):
    chat_id = message.chat.id
    try:
        invitees = [name.strip() for name in message.text.split(",")]
        for invitee_name in invitees:
            try:
                bot.send_message(chat_id, f"📩 You have invited {invitee_name} to the event \"{event_name}\"!\n"
                                          f"📅 Date: {event_date}\n"
                                          f"⏰ Time: {event_time}")
                events_data[chat_id].setdefault('guests', []).append(invitee_name)
            except Exception as e:
                print(f"Failed to process invitation for {invitee_name}: {e}")
        bot.send_message(chat_id, "✅ Invitations sent successfully.")
    except ValueError:
        bot.send_message(chat_id, "❌ Error: Make sure you entered valid names separated by commas.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ An error occurred: {e}")