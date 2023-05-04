import requests
import os

# Gets a specified number of messages from a specified Discord channel
def get_messages(channel_id, amount):
    return requests.get("https://discord.com/api/v9/channels/{:}/messages?limit={:}".format(channel_id, amount), headers={"authorization": os.getenv("AUTH_TOKEN")})

# Gets all the channels from a specified Discord server
def get_channels(server_id):
    return requests.get("https://discord.com/api/v9/guilds/{:}/channels".format(server_id), headers={"authorization": os.getenv("AUTH_TOKEN")})