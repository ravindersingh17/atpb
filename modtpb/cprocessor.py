import asyncio
import re
from modtpb import piratebay
from modtpb.tor import Tor

class cprocessor:

    def __init__(self, interface):
        self.interface = interface
        self.tor = Tor()
        self.tor.interface = self.interface
        self.downloads = []
        self.commands = []
        self.results = []
        self.chatstates = {}

    def addcommand(self, sender, command):
        self.commands.append({"sender": sender, "command": command})
        return "."

    async def processcommand(self):
        while True:
            if len(self.commands):
                command = self.commands.pop(0)

                commandparts = re.split("\s+", command["command"], 1)
                if commandparts[0] == "search" or commandparts[0] == "s":
                    if commandparts[1].strip() != "":
                        match = re.match("\"(.*?)\"", commandparts[1])
                        if not match:
                            term = commandparts[1]
                        else:
                            term = match.group(1)
                    else:
                        await self.interface.send_message(command["sender"], "Enter a valid search term")
                        return
                    await self.interface.send_message(command["sender"], "Searching...")
                    results = await piratebay.getsearches(term)
                    self.chatstates[command["sender"]] = {"page": 0, "results": results}
                    await self.sendsearches(command["sender"], 0, results)
                elif commandparts[0] == "list" or commandparts[0] == "l":
                    torData = self.tor.getallstatus()
                    message = ""
                    for id in torData:
                        message += "<b>{0})</b> {1} {2:.2f}% {3:.2f}kb/s {4}<br />".format(id, torData[id][0], torData[id][1], torData[id][2], torData[id][3])
                    if message == "":
                        await self.interface.send_message(command["sender"], "No torrents in queue")
                    else:
                        await self.interface.send_message(command["sender"], message)

                elif commandparts[0] == "pause":
                    if re.match("\d+", commandparts[1].strip()):
                        id = int(commandparts[1].strip())
                        if self.tor.pause(id):
                            await self.interface.send_message(command["sender"], "Paused torrent")
                        else:
                            await self.interface.send_message(command["sender"], "Failed, no such torrent")
                    elif commandparts[1].strip() == "":
                        self.tor.pauseall()
                        await self.interface.send_message(command["sender"], "Paused all torrents")
                    else:
                        await self.interface.send_message(command["sender"], "Unknown command")

                elif commandparts[0] == "resume":
                    if re.match("\d+", commandparts[1].strip()):
                        id = int(commandparts[1].strip())
                        if self.tor.resume(id):
                            await self.interface.send_message(command["sender"], "Resumed torrent")
                        else:
                            await self.interface.send_message(command["sender"], "Failed, no such torrent")
                    elif commandparts[1].strip() == "":
                        self.tor.resumeall()
                        await self.interface.send_message(command["sender"], "Resumed all torrents")
                    else:
                        await self.interface.send_message(command["sender"], "Unknown command")

                elif commandparts[0] == "remove":
                    if not re.match("\d+", commandparts[1].strip()):
                        await self.interface.send_message(command["sender"], "ID missing")
                    else:
                        id = int(commandparts[1].strip())
                        self.tor.remove(id)

                elif commandparts[0] == "help" or commandparts[0] == "h":
                    await self.interface.send_message(command["sender"], "Type \"tpb register\" to register<br/> \"tpb s <search term>\" to search. Eg:<br /> \"tpb s youre the worst 4-10\" <br />This searches for Season 4 Episode 10 of You're the worst<br />Type 1, 2 or 3 to choose one of the results or 0 for next page.<br /> That's it")

                if re.match("\d+", command["command"].strip()):
                    choice = int(command["command"])
                    sender = command["sender"]
                    if command["sender"] in self.chatstates:
                        if choice > 0:
                            try:
                                pagenum = self.chatstates[sender]["page"]
                                link =  await piratebay.gettorrent(self.chatstates[sender]["results"][pagenum*3 + choice - 1]["link"])
                                await self.interface.send_message(sender, "Got torrent link. Starting download. Use tpb [l]ist to view progress")
                                self.tor.add(link, sender)
                            except IndexError:
                                self.interface.send_message(sender, "Invalid choice")
                        if choice == 0:
                            self.chatstates[sender]["page"] += 1
                            await self.sendsearches(sender, self.chatstates[sender]["page"], self.chatstates[sender]["results"])
            else:
                await asyncio.sleep(1)

    async def sendsearches(self, sender, page, results):
        message = ""
        for i in range(3):
            if page*3 + i >= len(results):
                break
            message += "<b>{}</b><br />".format(i + 1)
            message += "<b>Title:</b>" + results[page*3 + i]["text"] + "<br />"
            message += "<b>Size: </b>" + results[page*3 + i]["size"] + "<br />"
            message += "<b>S/L: </b>" + results[page*3 + i]["seeders"][0] + "/" + results[page*3 + i]["seeders"][1] + "<br /><br />"

        if message == "":
            await self.interface.send_message(sender, "No results")
        else:
            await self.interface.send_message(sender, message)
            await self.interface.send_message(sender, "Use 0 for next page")


