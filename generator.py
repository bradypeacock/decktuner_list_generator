
# built-in imports
import datetime
from time import time
import logging
from dotenv import load_dotenv
from argparse import ArgumentParser

# Local imports
from workshop import Workshop
from log_formatter import set_up_logging
from discord_requests import get_channels, get_messages

# fix terminal colors in windows
import colorama
from sys import platform
if platform.startswith('win'):
    colorama.init()

# Global vars
workshop_list = []
dead_users_list = []
total_unclaimed = 0
total_inactive = 0
total_inactive_claimed = 0
total_new = 0

def populate_workshops(channel_id):
    messages = get_messages(channel_id, 100)
    if messages.ok:
        for message in messages.json():
            # Create new workshop with embed data (i.e., the "Bounty Card")
            # Embed data returned as a list, but there's only 1 element so grab that one
            workshop = Workshop(message["embeds"][0])
            if workshop.no_error:
                workshop_list.append(workshop)
            else:
                logging.info("Did not append workshop to list as it returned with an error")
                continue

            if not workshop.claimed:
                global total_unclaimed
                total_unclaimed += 1

            if not workshop.active:
                global total_inactive
                total_inactive += 1
                if workshop.claimed:
                    global total_inactive_claimed
                    total_inactive_claimed += 1

            if workshop.new:
                global total_new
                total_new += 1
    else:
        logging.error("HTTP request for tuning board messages returned with status code {:}".format(messages.status_code))

def populate_dead_users(channel_id):
    messages = get_messages(channel_id, 100)
    if messages.ok:
        carl_bot_user_id = "898324431112388638"
        for message in messages.json():
            if message["author"]["id"] == carl_bot_user_id:
                if "Member left" in message["embeds"][0]["title"]:
                    # bot stores the ID in the footer as "ID: <the id>", so split on " " (default)
                    # and the id will be the 2nd result, or index 1
                    dead_user_id = message["embeds"][0]["footer"]["text"].split()[1]
                    logging.info("User {:} has left the server.".format(dead_user_id))
                    dead_users_list.append(dead_user_id)
    else:
        logging.error("HTTP request for spam logs messages returned with status code {:}".format(messages.status_code))

def add_workshop_data(channel):
    for workshop in workshop_list:
        if workshop.channel_id == channel["id"]:
            workshop.channel_name = channel["name"]
            logging.info("Assigned {:} name to workshop ID {:}".format(workshop.channel_name, workshop.channel_id))

            if workshop.pilot in dead_users_list:
                workshop.user_alive = False
                logging.info("Pilot from {:} has left the server.".format(workshop.channel_name))
        
def print_workshops():
    # They are added in order newest -> oldest
    # but, we want to print them in order oldest -> newest
    workshop_list.reverse()

    print("\nWorkshops whose pilots have left:")
    for workshop in workshop_list:
        if workshop.user_alive == False:
            print(" - #{:}".format(workshop.channel_name))

    print("\nInactive (claimed) workshops:")
    for workshop in workshop_list:
        if workshop.active == False and workshop.claimed == True:
            print(" - #{:}".format(workshop.channel_name))

    print("\nUnclaimed workshops:")
    for workshop in workshop_list:
        if workshop.claimed == False:
            print_str = " - #{:}:".format(workshop.channel_name)
            print_str += " {:}".format(workshop.category)
            print_str += " | {:}".format(workshop.budget)
            print_str += " | {:}".format(workshop.commander)
            if workshop.tip:
                print_str += " | **TIP: {:}**".format(workshop.tip)
            if workshop.new:
                print_str += " (new)"

            print(print_str)

    total_open_workshops = len(workshop_list)
    total_workshops = int(workshop_list[-1].channel_name.replace("workshop-", ""))

    print("\nThere are {:} open workshops.".format(total_open_workshops))
    print(" - {:} ({:.2f}%) of them are unclaimed.".format(total_unclaimed, 100*(total_unclaimed/total_open_workshops)))
    print(" - {:} ({:.2f}%) have been created in the past week.".format(total_new, 100*(total_new/total_open_workshops)))
    print(" - {:} ({:.2f}%) have been inactive for more than 20 days.".format(total_inactive, 100*(total_inactive/total_open_workshops)))
    # Avoid dividing by 0. Highly unlikely, but possible if working on a smaller dataset during testing
    if total_inactive != 0:
        print(" - {:} ({:.2f}%) of the inactive workshops have been claimed by a tuner already.".format(total_inactive_claimed, 100*(total_inactive_claimed/total_inactive)))
    print(" - {:} total workshop requests received; {:} ({:.2f}%) of requests completed.".format(total_workshops, total_workshops - total_open_workshops, 100*((total_workshops - total_open_workshops)/total_workshops) ))

def main():
    decktuner_id = "845023235422421056"
    channels = get_channels(decktuner_id)
    if channels.ok:
        for channel in channels.json():
            if "tuning-board" in channel["name"]:
                populate_workshops(channel["id"])

            if "spam-logs" in channel["name"]:
                populate_dead_users(channel["id"])

            # it will always reach tuning-board before any workshop channels because
            # it accesses them by creation date, and tuning-board is one of the oldest channels
            if "workshop" in channel["name"]:
                add_workshop_data(channel)
    else:
        logging.error("HTTP request for channels returned with status code {:}".format(channels.status_code))

    print_workshops()

if __name__ == "__main__":
    # perform overhead first
    parser = ArgumentParser(description="Scrapes DeckTuner Discord server and prints info about workshops")
    parser.add_argument('-l', '--logging',
                        default='CONSOLE', choices=['NONE','CONSOLE','FILE','ALL'],
                        help="What type of logging you want to have. Default: %(default)s")
    
    args = parser.parse_args()

    log_to_console = (args.logging == "CONSOLE" or args.logging == "ALL")
    log_to_file = (args.logging == "FILE" or args.logging == "ALL")

    load_dotenv()

    # Set up logging
    # Filename format: output-YYYY-MM-DD-{time since epoch}.log
    logfile_name = "output-{date}-{time}.log".format(date=datetime.date.today(), time=int(time()))

    if args.logging != "NONE":
        if (not set_up_logging(console_log_output="stderr", console_log_level="info", console_log_color=True, log_to_console=log_to_console,
                                logfile_file=logfile_name, logfile_log_level="debug", logfile_log_color=False, log_to_file=log_to_file,
                                log_line_template="%(timestamp_color)s%(asctime)s:%(color_off)s [%(threadName)s] %(funcName)s:%(lineno)s: %(color_on)s%(levelname)s%(color_off)s: %(message)s")):
            print("Failed to set up logging, aborting.")
            exit()

    # now actually do main
    try:
        main()
    except Exception as e:
        logging.critical("Exception occured: {:}".format(e))