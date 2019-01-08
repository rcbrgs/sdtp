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
        self.listen_socket = self.context.socket(zmq.REP)
        self.listen_socket.bind('tcp://127.0.0.1:{}'.format(
            self.controller.config.values["mod_discordclient_listen_port"]))

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

        self.poller = zmq.Poller()
        self.poller.register(self.listen_socket, zmq.POLLIN)

        self.connect_talk_socket()
        
        self.controller.dispatcher.register_callback(
            "chat message", self.print_on_discord)
    
    def tear_down(self):
        self.wrapper.kill()
        self.controller.dispatcher.deregister_callback(
            "chat message", self.print_on_discord)

    # Mod specific
    ##############

    def connect_talk_socket(self):
        self.talk_socket = self.context.socket(zmq.REQ)
        self.talk_socket.connect('tcp://127.0.0.1:{}'.format(
            self.controller.config.values["mod_discordclient_talk_port"]))
        self.poller.register(self.talk_socket, zmq.POLLIN)        

    def disconnect_talk_socket(self):
        self.talk_socket.setsockopt(zmq.LINGER, 0)
        self.talk_socket.close()
        self.poller.unregister(self.talk_socket)
        
    def listen_for_message(self):
        polling = dict(self.poller.poll(1000))
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
        else:
            self.disconnect_talk_socket()
            self.connect_talk_socket()

    def print_on_discord(self, match_groups):
        self.logger.info(match_groups)
        if match_groups[11] == "Tick":
            return
        if len(match_groups[11]) >= len("[discord]"):
               if match_groups[11][:len("[discord]")] == "[discord]":
                   return               
        self.talk_socket.send_string("{}: {}".format(
            match_groups[10], match_groups[11]))
        #self.logger.info("Waiting for ACK.")
        #polling = dict(self.poller.poll(1000))
        #if self.talk_socket in polling and \
        #   polling[self.talk_socket] == zmq.POLLIN:
        #    self.talk_socket.recv()
        #    self.logger.info("ACK received, returning.")
        #else:
        #    self.logger.info("ACK not received.")
        self.logger.info("Returning.")
