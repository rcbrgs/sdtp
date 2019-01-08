import argparse
import asyncio
import discord
import logging
import zmq

class DiscordClient(discord.Client):
    def __init__(self, listen_socket):
        super().__init__()
        self.listen_socket = listen_socket
        
        self.logger = logging.getLogger(__name__)
        
        self.channel = None
        
    async def on_message(self, message):
        self.logger.info("{}: {}".format(message.author, message.content))
        if message.author == self.user:
            self.logger.info("Dropping self message.")
            return
        #self.channel = message.channel
        self.listen_socket.send_string("{}: {}".format(
            message.author, message.content))
        self.listen_socket.recv()

    async def on_ready(self):
        self.logger.info(
            'Logged in as {} with id {}.'.format(self.user.name, self.user.id))

        self.logger.info(
            "Member of the following guilds: {}".format(self.guilds))
        guild = None
        for item in self.guilds:
            if item.id == int(args.guild_id):
                guild = item
        self.logger.info("guild = {}".format(guild))
        self.logger.debug("channels = {}".format(guild.channels))
        channel = None
        for c in guild.channels:
            if c.name == args.channel:
                self.channel = c
        self.logger.info("channel = {}".format(self.channel))
        
    async def talk(self, msg):
        self.logger.info("msg = {}".format(msg))
        if self.channel is not None:
            await self.channel.send("[chat] {}".format(msg))
        else:
            self.logger.warning("self.channel is None.")

logging.basicConfig(
    filename="discord.log", level = logging.INFO,
    format="%(asctime)s %(levelname)-4.4s %(module)-6.6s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

argparser = argparse.ArgumentParser()
argparser.add_argument("token")
argparser.add_argument("listen_port")
argparser.add_argument("talk_port")
argparser.add_argument("guild_id")
argparser.add_argument("channel")
args = argparser.parse_args()

context = zmq.Context()
listen_socket = context.socket(zmq.REQ)
listen_socket.connect('tcp://127.0.0.1:{}'.format(args.listen_port))
logger.info("Listen socket connected.")

async def talk_to_discord(discord_client):
    logger = logging.getLogger(__name__)

    talk_socket = context.socket(zmq.REP)
    talk_socket.bind('tcp://127.0.0.1:{}'.format(args.talk_port))
    logger.info("Talk socket created.")

    poller = zmq.Poller()
    poller.register(talk_socket)
 
    while True:
        try:
            poll = dict(poller.poll(1000))
        except KeyboardInterrupt as e:
            break
        if talk_socket in poll and poll[talk_socket] == zmq.POLLIN:
            msg = talk_socket.recv().decode("utf-8")
            #talk_socket.send(b'ACK')
            logger.info(msg)
            await discord_client.talk(msg)
        else:
            talk_socket.setsockopt(zmq.LINGER, 0)
            talk_socket.close()
            poller.unregister(talk_socket)

            await asyncio.sleep(.1)
            talk_socket = context.socket(zmq.REP)
            talk_socket.bind('tcp://127.0.0.1:{}'.format(args.talk_port))
            poller.register(talk_socket)
                
            logger.debug("Talk socket created.")
            

        await asyncio.sleep(.1)

integration = DiscordClient(listen_socket)
integration.loop.create_task(talk_to_discord(integration))
logger.info("Loop task created.")

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(integration.start(*[args.token], **{}))
except KeyboardInterrupt:
    loop.run_until_complete(integration.logout())
    # cancel all tasks lingering
finally:
    loop.close()
