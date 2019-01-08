# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import random
import re
import subprocess
import threading
import time
import zmq

class DiscordClient(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_discordclient_enable"]:
            return
        self.setup()
        while(self.keep_running):
            #time.sleep(0.1)
            self.listen_for_message()
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.context = zmq.Context()
        self.connect_listen_socket()

        self.wrapper = subprocess.Popen(
            ["python3", "discord_wrapper.py", self.controller.config.values[
                "mod_discordclient_token"], "{}".format(
                    self.controller.config.values[
                        "mod_discordclient_listen_port"]),
             "{}".format(self.controller.config.values[
                 "mod_discordclient_talk_port"]),
             self.controller.config.values[
                 "mod_discordclient_guild_id"],
             self.controller.config.values[
                 "mod_discordclient_channel"]],
            stdout=subprocess.PIPE)
        self.logger.info("Discord wrapper launched.")
        self.logger.info("Sleeping 1s to wait for 0MQ talk port.")
        time.sleep(1)
        self.logger.info("Done sleeping.")

        self.connect_talk_socket()

        self.controller.dispatcher.register_callback(
            "chat message", self.print_on_discord)
    
    def tear_down(self):
        self.disconnect_talk_socket()
        self.disconnect_listen_socket()
        self.wrapper.kill()
        self.controller.dispatcher.deregister_callback(
            "chat message", self.print_on_discord)

    # Mod specific
    ##############

    def connect_listen_socket(self):
        self.listen_socket = self.context.socket(zmq.REP)
        self.listen_socket.bind('tcp://127.0.0.1:{}'.format(
            self.controller.config.values["mod_discordclient_listen_port"]))
        self.listen_poller = zmq.Poller()
        self.listen_poller.register(self.listen_socket, zmq.POLLIN)        

    def disconnect_listen_socket(self):
        self.listen_socket.setsockopt(zmq.LINGER, 0)
        self.listen_socket.close()
        self.listen_poller.unregister(self.listen_socket)
        
    def connect_talk_socket(self):
        self.talk_socket = self.context.socket(zmq.REQ)
        self.talk_socket.connect('tcp://127.0.0.1:{}'.format(
            self.controller.config.values["mod_discordclient_talk_port"]))
        self.talk_poller = zmq.Poller()
        self.talk_poller.register(self.talk_socket, zmq.POLLIN)        

    def disconnect_talk_socket(self):
        self.talk_socket.setsockopt(zmq.LINGER, 0)
        self.talk_socket.close()
        self.talk_poller.unregister(self.talk_socket)
        
    def listen_for_message(self):
        #self.logger.info("Registering listen_socket on poller.")
        polling = dict(self.listen_poller.poll(1000))
        if self.listen_socket in polling and \
           polling[self.listen_socket] == zmq.POLLIN:
            msg = self.listen_socket.recv().decode("utf-8")
            self.logger.info("Got msg '{}'".format(msg))
            
            self.logger.info("Sending ACK.")
            self.listen_socket.send(b'ACK')
            self.logger.info("ACK sent, continuing.")
            
            user = msg.split(": ")[0].split("#")[0]
            message = msg.split(": ", 1)[1]
            self.logger.info("message = {}".format(message))
            if len(message) >= len("[discord]"):
               if message[:len("[discord]")] == "[discord]":
                   return               
            self.controller.server.say("[discord] {}: {}".format(
                user, message))

    def print_on_discord(self, match_groups):
        self.logger.debug(match_groups)
        if match_groups[11] == "Tick":
            return
        if len(match_groups[11]) >= len("[discord]"):
               if match_groups[11][:len("[discord]")] == "[discord]":
                   return
        msg = "{}: {}".format(
            match_groups[10], match_groups[11])
               
        self.logger.info("Sending string '{}'.".format(msg))
        self.talk_socket.send_string(msg)
        
        self.logger.info("Polling for ACK.")
        polling = dict(self.talk_poller.poll(1000))
        
        self.logger.info("Checking polling.")
        if self.talk_socket in polling and \
           polling[self.talk_socket] == zmq.POLLIN:
            self.logger.info("Receiving ACK.")
            self.talk_socket.recv()

        self.logger.info("Returning.")
