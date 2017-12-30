import socket
import threading
import sys, os, signal
import logging
import time
import requests
from modtpb.daemon import Daemon
from hashlib import sha1
from hashlib import md5
import hmac
import json
from urllib.parse import parse_qs
import asyncio, aiohttp

PORT = 2500
LOG_FILE = "/var/log/atpbd.log"
MAX_INACTIVE = 1800
CHECK_SERVER = "8.8.8.8"
ACCESS_FILE = "/var/run/atpbd/lastactivity.dat"
TPB_HOOK = "https://w00t.in/tpbhook.php"
SECRET_FILE = "/etc/tpbtowoot.secret"

#Removed Daemon, do not fork for testing
class AtpbDaemon():

    def __init__(self, pidfile):
        #super().__init__(pidfile)
        logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

    async def client(self, reader, writer):
        while True:
            data = await reader.readline()
            if not data:
                break
            foo = self.process(data)
            writer.write(foo + b"\r\n")

    def run(self):
        loop = asyncio.get_event_loop()
        server = asyncio.start_server(self.client, host=None, port=PORT)
        loop.run_until_complete(asyncio.gather(server, self.check_activity()))
        loop.run_forever()

    def process(self, data):
        return data


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
            lastactivity = int(open(ACCESS_FILE).read())
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
                logging.info("Here we will anounce we are online")
                await self.announce_online()

    async def announce_online(self):
        logging.info("Announcing online status")
        message = "tpb server online"
        tpbrecipient = "all"
        payload = json.dumps({"message": message, "tpbrecipient": tpbrecipient}).encode("utf-8")
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

##DEBUG REMOVE THIS
if __name__ == "__main__":
    d = AtpbDaemon("/var/run/atpbd/atpbd.pid")
    d.run()
