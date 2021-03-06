import socket
import threading
import sys, os, signal
import logging
import time
import requests
from modtpb.daemon import Daemon
from modtpb.cprocessor import cprocessor
from hashlib import sha1
from hashlib import md5
import hmac
import json
from urllib.parse import parse_qs
import asyncio, aiohttp
import subprocess
import signal


PORT = 2500
LOG_FILE = "/var/log/atpbd.log"
MAX_INACTIVE = 1800
CHECK_SERVER = "8.8.8.8"
ACCESS_FILE = "/tmp/lastactivity.dat"
TPB_HOOK = "https://w00t.in/tpbhook.php"
SECRET_FILE = "/etc/tpbtowoot.secret"

#Removed Daemon, do not fork for testing
class AtpbDaemon():

    def __init__(self, pidfile):
        #super().__init__(pidfile)
        logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
        self.cprocessor = cprocessor(self)
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    async def client(self, reader, writer):
        while True:
            data = await reader.readline()
            if not data:
                break
            foo = self.process(data)
            writer.write(foo)

    async def control_client(self, reader, writer):
        while True:
            data = await reader.readline()
            if not data:
                break
            if data.strip() == b"GET":
                status = self.cprocessor.tor.getallstatus()
                message = ""
                for id in status:
                    message += "{0}: {1} {2:.2f}% {3:.2f}kb/s {4}\r\n".format(id, status[id][0], status[id][1], status[id][2], status[id][3])
                    writer.write(message.encode("utf-8"))

    def run(self):
        loop = asyncio.get_event_loop()
        server = asyncio.start_server(self.client, host=None, port=PORT)
        control_server = asyncio.start_server(self.control_client, host="localhost", port=2501)
        try:
            loop.run_until_complete(asyncio.gather(server,
                self.check_activity(),
                control_server,
                self.repairtunnel(),
                self.cprocessor.processcommand(),
                self.cprocessor.tor.eventprocess()
                ))
            loop.run_forever()
        except KeyboardInterrupt:
            self.cleanup(None, None)
            sys.exit(0)

    def cleanup(self, signal, frame):
        print("Here we will cleanup")
        logging.info("Exit called cleaning up")
        sys.exit(0)

    def process(self, data):
        if data.strip() == b"HELO":
            return data
        else:
            data = data.decode("utf-8")
            dataparts = data.split(" ", 1)
            addresult = self.cprocessor.addcommand(dataparts[0], dataparts[1])
            return addresult.encode("utf-8") + b"\r\n"


    async def check_activity(self):
        lastchecked = 0

        if time.time() - lastchecked < 300:
            logging.info("Less than 5 minutes have passed since we last checked")
            return

        lastchecked = time.time()

        """
        Check when we were last online. Announce we are online if time is >threshold
        Put in place so we can check if VM was resumed, intead of restarted
        """
        inactive = False
        try:
            lastactivity = float(open(ACCESS_FILE).read())
        except FileNotFoundError:
            lastactivity = 0

        if time.time() - lastactivity > MAX_INACTIVE:
            inactive = True
            logging.info("We have been inactive")

        online = False
        try:
            reader, writer = await asyncio.open_connection(host=CHECK_SERVER, port=53)
            online = True
        except Exception:
            logging.info("we are offline")
        if online:
            logging.info("We are online")
            f = open(ACCESS_FILE, "w")
            f.write(str(time.time()))
            f.close()
            if inactive:
                await self.announce_online()

    async def announce_online(self):
        await self.send_message("all", "tpb server online")

    async def send_message(self, recipient, message):
        payload = json.dumps({"message": message, "tpbrecipient": recipient}).encode("utf-8")
        try:
            secret = open(SECRET_FILE).read().strip().encode("utf-8")
        except FileNotFoundError:
            logging.critical("key file not found")
            sys.exit(-1)
        signature = hmac.new(secret, payload, sha1).hexdigest()
        headers = {"Content-Type": "application/json", "X-Tpb-Signature": signature}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(TPB_HOOK, data=payload, headers=headers) as resp:
                    logging.info("Hook returned {}".format(await resp.text()))
        except Exception as e:
            logging.critical("error: {}".format(e))


    async def repairtunnel(self):
        while True:
            connected = False
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host="w00t.in", port=8085), 40)
                writer.write(b"HELO\r\n")
                response = await asyncio.wait_for(reader.readline(), 40)
                print("Response {}".format(response))
                logging.debug("Response {}".format(response))
                assert response.strip() == b"HELO"
                connected = True
            except asyncio.TimeoutError:
                logging.debug("Timed out")
            except Exception as e:
                logging.debug("Error {}".format(e))

            if not connected:
                logging.debug("Not connected no response from woot")
                await self.execcommand("pkill autossh")
                logging.debug("Executed pkill")
                await self.execcommand("autossh -M 20004 -f -N ubuntu@w00t.in -R 8085:localhost:2500 -C")
                logging.debug("Sleep a bit")
                await asyncio.sleep(10)
            else:
                logging.debug("We are connected")

            await asyncio.sleep(20)

    async def execcommand(self, command):
        logging.debug("Executing {}".format(command))
        p = subprocess.Popen(command, shell=True)
        while p.poll() is None:
            logging.debug("Awaiting command to finish")
            await asyncio.sleep(.1)
        return p.wait()

##DEBUG REMOVE THIS
