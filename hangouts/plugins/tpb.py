import os, logging

import hangups

import plugins
import re

logger = logging.getLogger(__name__)


def _initialise(bot):

    plugins.register_handler(process_message, type="allmessages")

def process_message(bot, event, command):
    if event.user.is_self:
        return
    commandparts = re.split("\s+", event.text)

    if commandparts[0] == "tpb" and commandparts[1] == "register":
        registered_convs = bot.user_memory_get("0", "tpbregistered")
        if registered_convs is None:
            registered_convs = [event.conv.id_, ]
        else:
            if event.conv.id_ in registered_convs:
                yield from bot.coro_send_message(event.conv.id_, "tpb user already registered")
                return
            registered_convs.append(event.conv.id_)
        bot.user_memory_set("0", "tpbregistered", registered_convs)

        yield from bot.coro_send_message(event.conv.id_, "tpb user registered")
        for conv in registered_convs:
            yield from bot.coro_send_message(conv, "New tpb user {} registered".format(event.user.full_name))

