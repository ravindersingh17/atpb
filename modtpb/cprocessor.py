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
                    results = piratebay.getsearches(term)
                    print(results)
            else:
                await asyncio.sleep(1)


