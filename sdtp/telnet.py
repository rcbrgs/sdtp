# -*- coding: utf-8 -*-

import logging
import re
import socket
import sys
import telnetlib
import time
import threading

class TelnetClient(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.ready = False
        self.auto_connect = False
        self.connectivity_level = 0
        self.latest_handshake = 0
        self.ongoing_handshake = False
        self.output_matchers = [ re.compile ( b'^.*\n' ),
                                 re.compile ( b'^Day [\d]+, [\d]{2}:[\d]{2} ' ),
                                 re.compile ( b'Total of [\d]+ in the game' ) ]
        self.telnet = None

    def run(self):
        self.controller.dispatcher.register_callback(
            "password incorrect", self.close_connection_wrapper)
        while (self.keep_running):
            self.ready = False
            if (not self.check_connection()):
                time.sleep(1)
                continue
            line = self.chomp()
            if line == '':
                continue
            try:
                line_string = ""
                if line:
                    line_string = line.decode('utf-8')
                    line_string = line_string.strip ( )
            except Exception as e:
                self.logger.error("Error {} while processing line.decode('{}')".format(e, line))
            self.logger.debug(line_string)
            self.controller.parser.enqueue(line_string)
        self.close_connection()

    def stop ( self ):
        self.keep_running = False

    # Connection methods
    def check_connection ( self ):
        """
        Should return True if everything is fine with the connection.
        Do not rely on metadata for this; this function is supposed to be
        reliable, and the metadata set according to its results.
        """
        if self.controller.config.values["auto_connect"]:
            self.open_connection()
        if self.connectivity_level != 2:
            return False
        if self.telnet == None:
            return False
        if not isinstance(self.telnet.get_socket(), socket.socket):
            return False
        self.ready = True
        return True

    def close_connection(self):
        self.logger.info("Closing connection.")
        if self.connectivity_level == 2:
            self.handshake_bye()
        self.controller.telnet_ongoing = False
        self.telnet = None
        self.connectivity_level = 0

    def handshake_bye ( self ):
        self.write("exit")
        time.sleep(1)
        self.telnet.close()
        self.connectivity_level = 1
        self.logger.debug("Telnet connection closed.")

    def close_connection_wrapper(self, match_groups):
        self.close_connection()

    def create_telnet_object(self):
        self.telnet = telnetlib.Telnet(timeout = 10)
        if self.telnet != None:
            self.connectivity_level = 1
        self.logger.debug("Telnet step 1 completed.")

    def handshake_hi ( self ):
        if time.time ( ) - self.latest_handshake < 10:
            self.logger.info("Sleeping 10 seconds before attempting to connect again." )
            time.sleep(10)
        self.latest_handshake = time.time()
        try:
            self.telnet.open(self.controller.config.values['telnet_IP'],
                             self.controller.config.values['telnet_port'],
                             timeout = 5 )
            self.telnet.read_until(b"Please enter password:")
            self.logger.debug("Password requested by server.")
            self.write(self.controller.config.values['telnet_password'])
            self.logger.debug("Password was sent to server.")
        except Exception as e:
            self.logger.error("Error while opening connection: %s." % str(e))
            self.ongoing_handshake = False
            return
        self.logger.debug("Waiting for 'Logon successful.'")
        try:
            linetest = self.telnet.read_until(b'Logon successful.')
        except Exception as e:
            self.logger.error("linetest exception: {}.".format(e))
            self.ongoing_handshake = False
            return
        if b'Logon successful.' in linetest:
            self.logger.debug(linetest.decode('utf-8'))
            self.logger.info("Telnet connected successfully.")
        else:
            self.logger.error("Logon failed.")
            self.ongoing_handshake = False
            return
        self.logger.debug("Telnet step 2 completed." )
        self.connectivity_level = 2
        self.ongoing_handshake = False

    def open_connection ( self ):
        if self.ongoing_handshake:
            self.logger.debug("Attempted connection during handshake, ignoring call.")
            return
        self.ongoing_handshake = True
        if self.connectivity_level == 2:
            self.logger.debug("Attempted to re-open connection, ignoring call." )
            return
        self.logger.info("Trying to open connection.")
        if self.connectivity_level == 0:
            self.create_telnet_object ( )
        if self.connectivity_level == 1:
            self.handshake_hi ( )
        if self.connectivity_level != 2:
            self.logger.warning("open_connection failed.")
            self.close_connection ( )
            return
        self.controller.telnet_ongoing = True

    # I/O methods
    def chomp ( self ):
        try:
            result = self.telnet.expect ( self.output_matchers, 5 )
            self.logger.debug("result = {}".format ( result ))
            if len ( result ) == 3:
                line = result [ 2 ]
                if result [ 0 ] == -1:
                    if result [ 2 ] != b'':
                        self.logger.debug(
                            "expect timed out on '{}'.".format(result[2]))
                        return
                elif result [ 0 ] != 0:
                    self.logger.debug("output_matcher[{}] hit. result = '{}'.".format(result[0], result))
        except EOFError as e:
            self.logger.warning("chomp EOFError '{}'.".format(e))
            self.close_connection ( )
            return
        except Exception as e:
            if not self.check_connection ( ):
                self.logger.warning("chomp had an exception, because the connection is off.")
                self.close_connection ( )
                return
            if "[Errno 104] Connection reset by peer" in str ( e ):
                self.logger.warning("chomp: game server closed the connection.")
                self.close_connection ( )
                return
            self.logger.error("Exception in chomp: {}, sys.exc_info = '{}'.".format(e, sys.exc_info()))
            self.logger.error("type(self.telnet) == {}".format(type( self.telnet)))
            self.logger.error("isinstance(self.telnet.get_socket(), socket.socket) = {}".format(self.check_connection()))
            self.close_connection ( )
            return
        return line

    def write ( self, input_msg ):
        if self.connectivity_level == 0:
            self.logger.info("Ignoring attempt to write  with level 0 connectivity." )
            return

        if self.connectivity_level == 1:
            self.logger.debug("Writing with level 1 connectivity.")
        self.logger.debug("Type(input_msg) == {}".format(type(input_msg)))
        try:
            msg = input_msg + "\n"
        except Exception as e:
            self.logger.error("Newline exception: {}".format(e))
            return
        self.logger.debug("Raw write")
        try:
            self.telnet.write(msg.encode("utf8", "replace"))
        except Exception as e:
            self.logger.error("telnet.write had exception: {}".format(e))
            return
        self.logger.debug("Message written.")
