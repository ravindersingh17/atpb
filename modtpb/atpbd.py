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

PORT = 60001
LOG_FILE = "/var/log/atpbd.log"
MAX_INACTIVE = 1800
CHECK_SERVER = "8.8.8.8"
ACCESS_FILE = "/var/run/atpbd/lastactivity.dat"
TPB_HOOK = "https://w00t.in/tpbhook.php"
SECRET_FILE = "/etc/tpbtowoot.secret"


class AtpbDaemon(Daemon):

    def __init__(self, pidfile):
        super().__init__(pidfile)
        logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

    async def client(self, reader, writer):
        while True:
            data = await reader.readline()
            self.process(data)
            writer.write("OK")

    def run(self):
        loop = syncio.get_event_loop()
        server = asyncio.start_server(self.client, host=None, port=PORT)
        loop.run_until_complete(server)
        loop.run_forever()

    def process(self):
        pass


    def check_activity(self):

        if time.time() - lastchecked > 300:
            logging.info("Now checking if we have been inactive")
            lastchecked = time.time()

        time.sleep(.1)
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
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((CHECK_SERVER, 53))
            online = True
        except:
            logging.info("we are offline")
        if online:
            logging.info("We are online")
            f = open(ACCESS_FILE, "w")
            f.write(str(time.time()))
            f.close()
            if inactive:
                self.announce_online()

    def announce_online(self):
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
            r = requests.post(TPB_HOOK, data=payload, headers=headers)
            logging.info("Hook returned {}".format(r.text))
        except Exception as e:
            logging.critical("error: {}".format(e))
