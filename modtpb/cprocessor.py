import asyncio
import re
from modtpb import piratebay

class cprocessor:

    def __init__(self, interface):
        self.interface = interface
        self.downloads = []
        self.commands = []
        self.results = []
        self.chatstates = {}

    def addcommand(self, sender, command):
        self.commands.append({"sender": sender, "command": command})
        return "Processing command..."

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
                if re.match("\d+", command["command"].strip()):
                    choice = int(command["command"])
                    sender = command["sender"]
                    if command["sender"] in self.chatstates:
                        if choice > 0:
                            try:
                                pagenum = self.chatstates["sender"]["page"]
                                link = piratebay.gettorrent(self.chatstates[sender]["results"][pagenum*3 + choice - 1]["link"])
                            except IndexError:
                                self.interface.send_message(sender, "Invalid choice")
                        if choice == 0:
                            self.chatstates[sender]["page"] += 1
                            self.sendsearches(sender, self.chatstates[sender]["page"], self.chatstates[sender]["results"])
            else:
                await asyncio.sleep(1)

    async def sendsearches(self, sender, page, results):
        message = ""
        for i in range(3):
            if page*3 + i >= len(results):
                continue
            message += "<b>{}</b><br />".format(i + 1)
            message += "<b>Title:</b>" + results[page*3 + i]["text"] + "<br />"
            message += "<b>Size: </b>" + results[page*3 + i]["size"] + "<br /><br />"

        if message == "":
            await self.interface.send_message(sender, "No results")
        else:
            await self.interface.send_message(sender, message)
            await self.interface.send_message(sender, "Use 0 for next page")


