import sys
import threading
import asyncio

import easy_cli as cli

old_print = print
def print(text:str="",end:str="\n") -> None:
    sys.stdout.write(text)
    sys.stdout.write(end)
    sys.stdout.flush()
    return

def token_input() -> str:
    filling_char = "*"
    text = "Please enter your token > "
    endtext = (cli.change_terminal_color(style="RESET") if cli.supports_colors else "") + " < "
    result = ""
    key = b""
    col = ""
    while key != cli.ctrl["C"]:
        if cli.supports_colors: col = cli.change_terminal_color("RED") if len(result)!=72 else cli.change_terminal_color("GREEN")
        sys.stdout.write(f"\r{text}{col}{filling_char*len(result)}{endtext}")
        sys.stdout.flush()
        key = cli.get_key()
        if key in cli.text_keys:
            result+= key.decode()
        if key == cli.backspace:
            sys.stdout.write(f"\r{text}" + " "*len(result) + endtext)
            result = result[:-1]
        if key == cli.enter:
            sys.stdout.write("\n")
            break
    else:
        exit()
    sys.stdout.flush()
    return result

token = token_input()
if len(token) != 72:
    print("Invalid token")
    exit()

def clierror_screen(text:str="", next_line:str="Press any key to continue...") -> None:
    cli.clear_screen()
    print(text)
    print(next_line)
    cli.get_key()

print(f"using token \"{token[:5]}{'*'*62}{token[-5:]}\"")

import discord

def choose_from_list(choices:list[str],start:int=0,see_distance:int=4) -> int:
    if len(choices) < 1: return 0
    choice = start % len(choices)
    key = b""
    while key != cli.ctrl["C"]:
        cli.clear_screen()
        if choice > see_distance: print("...")
        for i in range(max(0, choice-see_distance), min(len(choices), choice+see_distance)):
            print(f"{'> ' if i == choice else '  '}{choices[i]}")
        if choice < len(choices)-see_distance: print("...")
        key = cli.get_key()
        if key == cli.up_arrow: choice = (choice-1) % len(choices)
        if key == cli.down_arrow: choice = (choice+1) % len(choices)
        if key == cli.enter:
            break
        if key == cli.escape:
            return -1
    else:
        exit()
    return choice

def text_channel_screen(text: str, messages: list[discord.Message], tsize: tuple[int, int], cls: bool=True):
    if cls:
        cli.clear_screen()
    current_line = tsize[1]
    for i, message in enumerate(messages):
        current_line-= int(len(message.content)/tsize[0])+1
        if current_line <= 1:
            break
        cli.move_cursor(current_line, 1)
        sys.stdout.write(f" {message.content}\n")
        if len(messages)-(i+1) and messages[i+1].author == message.author:
            continue
        current_line-= int(len(f"{message.author.display_name} {message.created_at.strftime('%d/%m - %H:%M')}")/tsize[0])+1
        if current_line <= 1:
            break
        cli.move_cursor(current_line, 1)
        sys.stdout.write(f"{message.author.display_name} {message.created_at.strftime('%H:%M')}\n")
    # f"{message.author.display_name} {message.created_at.strftime('%H:%M')}\n {line}"

    cli.move_cursor(tsize[1], 1)
    sys.stdout.write(f"> {text}     ")
    cli.move_cursor(tsize[1], len(text)+3)
    sys.stdout.flush()


class aclient(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(intents=intents)
        self.ready = False
        self.text = ""
        self.messages = []

    async def reload_messages(self):
        self.messages = [message async for message in self.channel.history()]
        text_channel_screen("", self.messages, cli.get_terminal_size())

    def extra_functions(self, server: discord.Guild):
        options = ["leave server", "create invite", "view members"]
        option = choose_from_list(options)
        if input(f"\nAre you sure you want to {options[option]} (y/n):") == "y":
            match option:
                case 0:
                    asyncio.run_coroutine_threadsafe(server.leave(), self.loop).result()
                case 1:
                    sys.stdout.flush()
                    cli.clear_screen()
                    invites: list[discord.Invite] = asyncio.run_coroutine_threadsafe(server.invites(), self.loop).result()
                    invite = None
                    user_padding = " "*(max([len(_.inviter.name) for _ in invites if _.inviter] + [3])+2)
                    for inv in invites:
                        if inv.inviter == client.user:
                            invite = inv
                            break
                        else:
                            print(f"{user_padding} invite: {inv.url}\r{inv.inviter.name if inv.inviter else 'Unknown'}'s")
                    if not invite and input(f"\nDo you want to create a separate invite (y/n)? ") == "y":
                        if not server.channels:
                            clierror_screen("Could not create invite, no channels.")
                            return
                        invite = asyncio.run_coroutine_threadsafe(server.channels[0].create_invite(), self.loop).result()
                    if invite:
                        print(f"{user_padding} invite: {invite.url}\rBot's")
                        
                    input("press enter to exit this screen:")
                    cli.clear_screen()
                case _:
                    clierror_screen("Unknown Error")
                    return

    def main(self):
        self.ready = False
        self.servers: list[discord.Guild] = list(self.guilds)
        server_i = 0
        channel_i = 0
        while True:
            self.ready = False
            server_i = choose_from_list([_.name for _ in self.servers], server_i, (cli.get_terminal_size()[1]//2)-2)
            if server_i == -1: server_i = 0; break
            self.server = self.servers[server_i]
            while True:
                self.ready = False
                channel_i = choose_from_list([_.name for _ in self.server.text_channels] + ["... extra functions ..."], channel_i, (cli.get_terminal_size()[1]//2)-2)
                if channel_i == -1: channel_i = 0; break
                if channel_i == len(self.server.text_channels):
                    self.extra_functions(self.server)
                    continue
                self.channel = self.server.text_channels[channel_i]
                asyncio.run_coroutine_threadsafe(self.reload_messages(), self.loop)
                self.ready = True
                
                text_channel_screen("", self.messages, cli.get_terminal_size())
                last_messages = self.messages
                self.text = ""
                key = cli.get_key()
                while key != cli.escape:
                    text_channel_screen(self.text, self.messages, cli.get_terminal_size(), last_messages != self.messages)
                    key = cli.get_key()
                    if key in cli.text_keys:
                        self.text+= key.decode()
                    if key == cli.backspace:
                        self.text = self.text[:len(self.text)-1]
                    if key == cli.enter and self.text:
                        cli.clear_screen()
                        asyncio.run_coroutine_threadsafe(self.channel.send(self.text), self.loop)
                        self.text = ""
        cli.clear_screen()
        asyncio.run_coroutine_threadsafe(client.close(), self.loop)

    async def on_ready(self):
        await self.wait_until_ready()
        print(f"We have logged in as {self.user}.")
        threading.Thread(
            target=self.main,
            daemon=True
        ).start()

    async def on_message(self, message: discord.Message):
        if not self.ready: return
        if message.channel == self.channel:
            self.messages.insert(0, message)
            text_channel_screen(self.text, self.messages, cli.get_terminal_size())
        if message.author == self.user:
            return


client = aclient()
client.run(token)