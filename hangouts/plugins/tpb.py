import os, logging

import hangups

import plugins
import re
import asyncio
import subprocess
from tvmaze import TVMaze
logger = logging.getLogger(__name__)
TPB_HOST = "w00t.in"
TPB_PORT = 8085
SSH_PORT = 8082
SSH_USER = "ravinder"

def _initialise(bot):

    plugins.register_handler(process_message, type="allmessages")

async def process_message(bot, event, command):
    if event.user.is_self:
        return
    commandparts = re.split("\s+", event.text)

    if commandparts[0] == "tpb":
        if commandparts[1] == "register":
            """
            If command is for registering we do not need to check if tpb is online
            """
            registered_convs = bot.user_memory_get("0", "tpbregistered")
            if registered_convs is None:
                registered_convs = [event.conv.id_, ]
            else:
                if event.conv.id_ in registered_convs:
                    await bot.coro_send_message(event.conv.id_, "tpb user already registered")
                    return
                registered_convs.append(event.conv.id_)
            bot.user_memory_set("0", "tpbregistered", registered_convs)

            await bot.coro_send_message(event.conv.id_, "tpb user registered")
            for conv in registered_convs:
                await bot.coro_send_message(conv, "New tpb user {} registered".format(event.user.full_name))

        elif commandparts[1] == "info":
            if len(commandparts) < 3:
                await bot.coro_send_message(event.conv.id_, "No data supplied")
                return
            data = TVMaze.search(" ".join(commandparts[2:]))
            message = data["summary"]
            if data["nextepisode"]:
                message += "<br /><b>Next Episode:</b>" + data["nextepisode"]
            if data["previousepisode"]:
                message += "<br /><b>Previous Episode:</b>" + data["previousepisode"]
            await bot.coro_send_message(event.conv.id_, message)
        else:
            # Check if tpb is online
            tpbonline = False
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host=TPB_HOST, port=TPB_PORT), 10)
                writer.write(b"HELO\r\n")
                response = await asyncio.wait_for(reader.readline(), 20)
                assert response.strip() == b"HELO"
            except asyncio.TimeoutError:
                await bot.coro_send_message(event.conv.id_, "tpb is offline, connection timed out")
            except Exception:
                await bot.coro_send_message(event.conv.id_, "tpb is offline, starting the server")
            else:
                tpbonline = True

            if not tpbonline:
                await bot.coro_send_message(event.conv.id_, "Starting the server")
                output = await execcommand('ssh {}@{} -p {} "vbox start \\\"Ubuntu Server VM\\\""'.format(SSH_USER, TPB_HOST, SSH_PORT))
                await bot.coro_send_message(event.conv.id_, "Started the tpb server, server reply: {}".format(output))
                await bot.coro_send_message(event.conv.id_, "Wait for the server's message to inform you of online status")
            else:
                response = await send_to_tpb("{} {}".format(event.conv.id_, event.text[4:]))
                await bot.coro_send_message(event.conv.id_, response)
    else:
        if re.match("\d*", event.text.strip()):
            response = await send_to_tpb("{} {}".format(event.conv.id_, event.text))
            await bot.coro_send_message(event.conv.id_, response)


async def execcommand(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    while p.poll() is None:
        asyncio.sleep(.1)
    return p.stdout.read().decode("utf-8")

async def send_to_tpb(message):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host=TPB_HOST, port=TPB_PORT), 10)
        writer.write(message.encode("utf-8") + b"\r\n")
        response = await asyncio.wait_for(reader.readline(), 20)
        return response.decode("utf-8")
    except asyncio.TimeoutError:
        return "Timed out, make sure tpb is online"
    except Exception as e:
        return "Unknown error {}".format(e)





