def show_guest_list(bot, message, events_data):
    """Shows the list of guests who responded 'yes'."""
    chat_id = message.chat.id
    event_id = message.text
    if event_id in events_data['events']:
        event = events_data['events'][event_id]
        yes_rsvps = event.get('yes_rsvps', [])
        if yes_rsvps:
            guest_list = "\n".join(yes_rsvps)
            bot.send_message(chat_id, f"Guests who responded 'yes' for event '{event['name']}':\n{guest_list}")
        else:
            bot.send_message(chat_id, "No guests have responded 'yes' yet.")
    else:
        bot.send_message(chat_id, "❌ Invalid event ID.")