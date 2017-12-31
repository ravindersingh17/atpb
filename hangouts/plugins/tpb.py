import os, logging

import hangups

import plugins
import re

logger = logging.getLogger(__name__)


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
        else:
            # Check if tpb is online
            await bot.coro_send_message(event.conv.id_, "Checking if tpb is online")

