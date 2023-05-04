from datetime import datetime, timedelta, timezone
from enum import IntEnum, auto, unique
import logging

from discord_requests import get_messages

# fix terminal colors in windows
import colorama
from sys import platform
if platform.startswith('win'):
    colorama.init()

@unique
class WorkshopFields(IntEnum):
    # override parent function to start at 0
    def _generate_next_value_(name, start, count, last_values):
        start = 0
        return IntEnum._generate_next_value_(name, start, count, last_values)

    STRATEGY = auto()
    GOALS = auto()
    PILOT = auto()
    CATEGORY = auto()
    BUDGET = auto()
    TUNERS = auto()
    ROOM = auto()

class Workshop:
    def __init__(self, raw_embed_data):
        self.user_alive = True
        self.no_error = True
        self.__construct_workshop(raw_embed_data)

    def __construct_workshop(self, data):
        print("\nCreating new workshop...")

        try:
            # convert to epoch time
            self.timestamp = datetime.fromisoformat(data["timestamp"])
            self.commander = data["title"]

            # strategy and goals are currently unused for the purpose of this program
            #self.strategy = data["fields"][WorkshopFields.STRATEGY]["value"]
            #self.goals = data["fields"][WorkshopFields.GOALS]["value"]
            # strip off the <@...> from the ID
            self.pilot = data["fields"][WorkshopFields.PILOT]["value"].strip('<').strip('>').strip('@')
            self.category = data["fields"][WorkshopFields.CATEGORY]["value"]
            self.budget = data["fields"][WorkshopFields.BUDGET]["value"]
            self.tuners = data["fields"][WorkshopFields.TUNERS]["value"]
            # strip off the <#...> from the ID
            self.channel_id = data["fields"][WorkshopFields.ROOM]["value"].strip('<').strip('>').strip('#')
            self.tip = None # not yet implemented in workshops

            self.channel_name = "" # needs to be filled in later by the caller

            # fill in conditionals
            if self.tuners == "*none*":
                self.claimed = False
            else:
                self.claimed = True

            now_time = datetime.now(timezone.utc)

            if now_time - self.timestamp < timedelta(weeks=1):
                self.new = True
            else:
                self.new = False
            
            most_recent_message = get_messages(self.channel_id, 1)
            if most_recent_message.ok:
                message_data = most_recent_message.json()[0]
                message_time = datetime.fromisoformat(message_data["timestamp"])
                if now_time - message_time > timedelta(days=20):
                    self.active = False
                else:
                    self.active = True
            else:
                self.no_error = False
                logging.error("HTTP request for workshop {:} message returned status code {:}".format(self.channel_id, most_recent_message.status_code))

            self.dump(False)
        except Exception as e:
            logging.error("Failed to construct workshop: {:}".format(e))
            self.no_error = False
            self.dump(True)

    # If log is true, will log to file. If false, will print to console
    def dump(self, log):
        if log:
            logging.info("---------------------------")
            if self.channel_name:
                logging.info("CHANNEL NAME: {:}".format(self.channel_name))
            logging.info("CHANNEL ID: {:}".format(self.channel_id))
            logging.info("COMMANDER: {:}".format(self.commander),)
            logging.info("PILOT ID: {:}".format(self.pilot))
            logging.info("CATEGORY: {:}".format(self.category))
            logging.info("BUDGET: {:}".format(self.budget))
            if self.tip:
                logging.info("TIP: {:}".format(self.tip))
            logging.info("TIMESTAMP: {:}".format(self.timestamp))
            logging.info("---------------------------")
        else:
            print("---------------------------")
            if self.channel_name:
                print("CHANNEL NAME: {:}".format(self.channel_name))
            print("CHANNEL ID: {:}".format(self.channel_id))
            print("COMMANDER: {:}".format(self.commander))
            print("PILOT ID: {:}".format(self.pilot))
            print("CATEGORY: {:}".format(self.category))
            print("BUDGET: {:}".format(self.budget))
            if self.tip:
                logging.info("TIP: {:}".format(self.tip))
            print("TIMESTAMP: {:}".format(self.timestamp))
            print("---------------------------")