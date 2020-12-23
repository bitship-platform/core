# token = "NzY4NTU0Mzk5MjkwMjI4NzM2.X9M71g.6xE-evAzWkC7zf1-P5l6mRVnmEg"
#
# import discord,time,json
# from discord.ext import commands
#
# bot = commands.Bot(command_prefix=".", self_bot=True,fetch_offline_member=True)
# mention = discord.AllowedMentions(users=True)
#
# @bot.event
# async def on_ready():
#     # print("READY")
#     # alpha = "abcdefghijklmnopqrstuvwxyz!"
#     user_list= []
#     guild = bot.get_guild(786910469503582258)
#     # for i in alpha:
#     #     members = await guild.query_members(limit=100,query=i)
#     #     for member in members:
#     #         if member.id not in user_list:
#     #             user_list.append(member.id)
#     channel = guild.get_channel(786910469503582261)
#     with open('logs.json', 'r') as file:
#         user_list = json.load(file)
#     for i in user_list:
#         await channel.send(f"<@{i}>",allowed_mentions=mention)
#
#
# bot.run(token, bot=False)
# #
# # import requests
# # requests.post("https://discordapp.com/api/v6/invites/v5yb6dp8",headers={'authorization':token})


def check_working(proxy):
    return False

not_working = []

with open("data.txt", "r") as f:
    proxy_list = f.read().split()

for index, proxy in enumerate(proxy_list):
    if not check_working(proxy):
        not_working.append(proxy_list.pop(index))
print(proxy_list)
print(not_working)
