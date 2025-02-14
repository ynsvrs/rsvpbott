import telebot
from datetime import datetime
from reminder import schedule_reminder  # Import reminders
from config import BOT_TOKEN  # Bot token
from rsvp import handle_rsvp  # RSVP handler
from invite import generate_event_link, generate_event_id_and_store, invite_participants  # Invitation functions
from events import list_events, cancel_event, edit_event  # Event listing, cancellation, and editing
from guests import show_guest_list  # Guest list function

class RSVPBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.events_data = {'events': {}}  # Initialize with 'events' key
        self.setup_handlers()

    def setup_handlers(self):
        self.bot.message_handler(commands=['start'])(self.welcome)
        self.bot.message_handler(commands=['createevent'])(self.create_event)
        self.bot.message_handler(commands=['myevents'])(self.my_events_command)
        self.bot.message_handler(commands=['cancel'])(self.cancel_event_command)
        self.bot.message_handler(commands=['edit'])(self.edit_event_command)
        self.bot.message_handler(commands=['invite'])(self.invite_command)
        self.bot.message_handler(commands=['rsvp'])(self.rsvp_command)
        self.bot.message_handler(commands=['guestlist'])(self.guest_list_command)

    def welcome(self, message):
        self.bot.send_message(
            message.chat.id,
            f"👋 Hello, {message.from_user.first_name}! I am the <b>RSVP</b> bot to help you manage events.\n\n"
            "📅 <b>Features:</b> \n"
            "✔️ Create an event (/createevent)\n"
            "✔️ View my events (/myevents)\n"
            "✔️ Confirm attendance (/rsvp ID yes/no/maybe)\n"
            "✔️ Cancel an event (/cancel ID)\n"
            "✔️ Edit an event's date and time (/edit ID)\n"
            "✔️ View guest list (/guestlist ID)\n"
            "🚀 <em>Start with /createevent!</em>",
            parse_mode='html'
        )

    def create_event(self, message):
        """Starts the event creation process."""
        chat_id = message.chat.id
        self.events_data[chat_id] = {}  # Initialize data
        self.bot.send_message(chat_id, "📋 What is the name of the event?")
        self.bot.register_next_step_handler(message, self.set_event_name)

    def set_event_name(self, message):
        """Saves the event name."""
        chat_id = message.chat.id
        self.events_data[chat_id]['name'] = message.text
        self.bot.send_message(chat_id, "📅 Enter the date of the event (format: YYYY-MM-DD):")
        self.bot.register_next_step_handler(message, self.set_event_date)

    def set_event_date(self, message):
        """Saves the event date."""
        chat_id = message.chat.id
        try:
            date = datetime.strptime(message.text, "%Y-%m-%d").date()
            self.events_data[chat_id]['date'] = date
            self.bot.send_message(chat_id, "⏰ Enter the time of the event (format: HH:MM):")
            self.bot.register_next_step_handler(message, self.set_event_time)
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid date format. Use YYYY-MM-DD.")
            self.bot.register_next_step_handler(message, self.set_event_date)

    def set_event_time(self, message):
        """Saves the event time and creates a link to Google Calendar."""
        chat_id = message.chat.id
        try:
            time = datetime.strptime(message.text, "%H:%M").time()
            self.events_data[chat_id]['time'] = time

            event_name = self.events_data[chat_id]['name']
            event_date = self.events_data[chat_id]['date']
            event_time = self.events_data[chat_id]['time']
            event_start_time = datetime.combine(event_date, event_time)

            # Generate event ID
            event_id = generate_event_id_and_store(chat_id, self.events_data)

            # Schedule reminder
            schedule_reminder(chat_id, event_name, event_start_time, self.bot)

            # Generate event link
            event_link = generate_event_link(event_name, event_start_time)

            # Send information to the user
            self.bot.send_message(chat_id, f"✅ Event \"{event_name}\" created!\n"
                                           f"📆 {event_date} at {event_time}\n"
                                           f"🔔 Reminder set!\n"
                                           f"📋 Event ID: {event_id}\n"
                                           f"🌍 <a href='{event_link}'>View in Google Calendar</a>",
                                  parse_mode="HTML")
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid time format. Use HH:MM.")
            self.bot.register_next_step_handler(message, self.set_event_time)

    def my_events_command(self, message):
        """Handles the myevents command."""
        chat_id = message.chat.id
        events = list_events(chat_id, self.events_data)
        if not events:
            self.bot.send_message(chat_id, "❌ No upcoming events found.")
        else:
            message_text = "📅 Your upcoming events:\n"
            for event in events:
                message_text += f"ID: {event['id']}\n"
                message_text += f"Name: {event['name']}\n"
                message_text += f"Date: {event['date']}\n"
                message_text += f"Time: {event['time']}\n"
                message_text += "----------------------\n"
            self.bot.send_message(chat_id, message_text)

    def cancel_event_command(self, message):
        """Handles the cancel command."""
        chat_id = message.chat.id
        try:
            _, event_id = message.text.split()
            result = cancel_event(chat_id, event_id, self.events_data)
            if result:
                self.bot.send_message(chat_id, f"✅ Event {event_id} has been canceled.")
            else:
                self.bot.send_message(chat_id, "❌ Invalid event ID or you don't have permission to cancel this event.")
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid format. Use /cancel <event_id>.")

    def edit_event_command(self, message):
        """Handles the edit command."""
        chat_id = message.chat.id
        try:
            _, event_id = message.text.split()
            if event_id in self.events_data['events'] and self.events_data['events'][event_id]['chat_id'] == chat_id:
                self.bot.send_message(chat_id, "📅 Enter the new date of the event (format: YYYY-MM-DD):")
                self.bot.register_next_step_handler(message, self.set_new_event_date, event_id)
            else:
                self.bot.send_message(chat_id, "❌ Invalid event ID or you don't have permission to edit this event.")
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid format. Use /edit <event_id>.")

    def set_new_event_date(self, message, event_id):
        """Saves the new event date."""
        chat_id = message.chat.id
        try:
            date = datetime.strptime(message.text, "%Y-%m-%d").date()
            self.events_data['events'][event_id]['date'] = date
            self.bot.send_message(chat_id, "⏰ Enter the new time of the event (format: HH:MM):")
            self.bot.register_next_step_handler(message, self.set_new_event_time, event_id)
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid date format. Use YYYY-MM-DD.")
            self.bot.register_next_step_handler(message, self.set_new_event_date, event_id)

    def set_new_event_time(self, message, event_id):
        """Saves the new event time and updates the event."""
        chat_id = message.chat.id
        try:
            time = datetime.strptime(message.text, "%H:%M").time()
            self.events_data['events'][event_id]['time'] = time

            event = self.events_data['events'][event_id]
            event_name = event['name']
            event_date = event['date']
            event_time = event['time']
            event_start_time = datetime.combine(event_date, event_time)

            # Generate new event link
            event_link = generate_event_link(event_name, event_start_time)

            # Update reminder
            schedule_reminder(chat_id, event_name, event_start_time, self.bot)

            # Send updated information to the user
            self.bot.send_message(chat_id, f"✅ Event \"{event_name}\" updated!\n"
                                           f"📆 New date: {event_date} at {event_time}\n"
                                           f"🔔 Reminder updated!\n"
                                           f"🌍 <a href='{event_link}'>View in Google Calendar</a>",
                                  parse_mode="HTML")
        except ValueError:
            self.bot.send_message(chat_id, "❌ Invalid time format. Use HH:MM.")
            self.bot.register_next_step_handler(message, self.set_new_event_time, event_id)

    def invite_command(self, message):
        """Handles the invite command."""
        chat_id = message.chat.id
        events = list_events(chat_id, self.events_data)
        if not events:
            self.bot.send_message(chat_id, "❌ No events found to invite guests.")
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for event in events:
                markup.add(event['id'])
            self.bot.send_message(chat_id, "Select the event to invite guests:", reply_markup=markup)
            self.bot.register_next_step_handler(message, self.select_event_to_invite)

    def select_event_to_invite(self, message):
        """Handles the selection of an event to invite guests."""
        chat_id = message.chat.id
        event_id = message.text
        if event_id in self.events_data['events']:
            event = self.events_data['events'][event_id]
            guest_list = "\n".join([f"Guest Name: {guest_name}" for guest_name in event.get('guests', [])])
            self.bot.send_message(chat_id, f"Guests for event '{event['name']}']:\n{guest_list}")
            self.bot.send_message(chat_id, "📩 Enter the names of participants separated by commas to invite:")
            self.bot.register_next_step_handler(message, self.process_invitees, event_id)
        else:
            self.bot.send_message(chat_id, "❌ Invalid event ID.")
            self.bot.register_next_step_handler(message, self.select_event_to_invite)

    def process_invitees(self, message, event_id):
        """Processes and sends invitations to participants."""
        chat_id = message.chat.id
        try:
            invitees = [name.strip() for name in message.text.split(",")]
            for invitee_name in invitees:
                try:
                    self.bot.send_message(chat_id, f"📩 You have invited {invitee_name} to the event \"{self.events_data['events'][event_id]['name']}\"!\n"
                                                   f"📅 Date: {self.events_data['events'][event_id]['date']}\n"
                                                   f"⏰ Time: {self.events_data['events'][event_id]['time']}")
                    self.events_data['events'][event_id].setdefault('guests', []).append(invitee_name)
                except Exception as e:
                    print(f"Failed to process invitation for {invitee_name}: {e}")
            self.bot.send_message(chat_id, "✅ Invitations sent successfully.")
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ An error occurred: {e}")

    def rsvp_command(self, message):
        """Handles the RSVP command."""
        handle_rsvp(self.bot, message, self.events_data)

    def guest_list_command(self, message):
        """Handles the guest list command."""
        chat_id = message.chat.id
        self.bot.send_message(chat_id, "📋 Enter the event ID to see the guest list:")
        self.bot.register_next_step_handler(message, self.show_guest_list)

    def show_guest_list(self, message):
        """Shows the list of guests who responded 'yes'."""
        chat_id = message.chat.id
        event_id = message.text
        if event_id in self.events_data['events']:
            event = self.events_data['events'][event_id]
            yes_rsvps = event.get('yes_rsvps', [])
            if yes_rsvps:
                guest_list = "\n".join(yes_rsvps)
                self.bot.send_message(chat_id, f"Guests who responded 'yes' for event '{event['name']}':\n{guest_list}")
            else:
                self.bot.send_message(chat_id, "No guests have responded 'yes' yet.")
        else:
            self.bot.send_message(chat_id, "❌ Invalid event ID.")
            self.bot.register_next_step_handler(message, self.show_guest_list)

    def run(self):
        print("Bot is running...")
        self.bot.infinity_polling()

def get_bot():
    return RSVPBot(BOT_TOKEN).bot

if __name__ == "__main__":
    rsvp_bot = RSVPBot(BOT_TOKEN)
    rsvp_bot.run()