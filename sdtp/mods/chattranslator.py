# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import googletrans
import logging
import re
import threading
import time

from sdtp.lkp_table import lkp_table
from sdtp.mods.chat_translator_table import ChatTranslatorTable

class ChatTranslator(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.abort = False
        self.start ( )

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_chattranslator_enable"]:
            return
        self.setup()
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.tear_down()
            
    def stop ( self ):
        self.logger.info("Stop.")
        self.keep_running = False

    # Mod specific
    ##############

    def setup(self):
        self.help = {
            "translate": "will list your current configuration.",
            "translate <language code>": "will toggle if you know a language.",
            "translate *": "will enable or disable translations.",
            "translate <language code>*": "will set the language to translate to.",
            "translate codes": "Will list the language codes known to the system."}
        self.controller.help.registered_commands["translate"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.parse_chat_message)
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
        self.translator = googletrans.Translator()

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.parse_chat_message)
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)
        
    def parse_chat_message(self, match_groups):
        reconstructed_message = "[{}] {}: {}".format(
            match_groups[9], match_groups[10], match_groups[11])
        if match_groups[10] == "Server":
            return
        message = match_groups[11]
        if message[0] == "/":
            return
        detect = self.translator.detect(message)
        self.logger.info("Detected language: {}".format(detect.lang))
        for player in self.controller.worldstate.online_players:
            
            answer = self.controller.database.blocking_consult(
                ChatTranslatorTable,
                [(ChatTranslatorTable.steamid, "==", player["steamid"])])
            if len(answer) == 0:
                self.logger.debug("Player hasn't setup translations.")
                return
            if len(answer) != 1:
                self.logger.error("DB entry not unique.")
                return
            chat_translator = answer[0]
            if not chat_translator["enable"]:
                return
            if detect.lang in chat_translator["languages_known"]:
                return
            translation = self.translator.translate(
                message, dest=chat_translator["target_language"])
            self.logger.info("Translation to {}: {}".format(
                chat_translator["target_language"], translation))
            self.controller.server.pm(player, "{}: {}".format(
                emitter, translation.text))

    def check_for_commands(self, match_groups):
        matcher = re.compile(r"^/translate[\w]*(.*)$")
        match = matcher.search(match_groups[11])
        if not match:
            self.logger.debug(
                "No match for command regex: {}". format(match_groups[11]))
            return
        command = match.groups()[0].strip()
        player = self.controller.worldstate.get_player_steamid(
            match_groups[7])
        self.logger.debug("Parsing command '{}'.".format(command))
        if command == "":
            self.list_languages(player)
            return
        if command == "*":
            self.toggle_enable_translations(player)              
            return
        if command in googletrans.LANGUAGES.keys():
            self.toggle_language(player, command)
            return
        if command[-1] == "*":
            self.set_target_language(player, command[:-1])
            return
        if command == "codes":
            self.print_language_codes(player)
            return

    def list_languages(self, player):
        answer = self.controller.database.blocking_consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])])
        if len(answer) == 0:
            self.controller.server.pm(
                player, "You don\'t have any languages configured.")
            return
        if len(answer) != 1:
            self.logger.error("DB entry non-unique.")
            return
        db_entry = answer[0]
        response = "Translations are "
        if db_entry["enable"]:
            response += "enabled to the target language " + db_entry["target_language"]
        else:
            response += "disabled"
        response += ". The languages you know are: " + db_entry["languages_known"]
        self.controller.server.pm(player, response)
        
    def toggle_enable_translations(self, player):
        self.logger.info("Trying to toggle translations for player {}.".format(player["name"]))
        answer = self.controller.database.blocking_consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])])
        if len(answer) != 1:
            self.logger.error("Entry not unique in db.")
            if len(answer) == 0:
                self.logger.debug(
                    "Player has no entry in chat_translator_table.")
                self.controller.server.pm(
                    player, "First define a language you know with /translate " \
                    "language")
            return
        row = answer[0]
        self.logger.info("Before toggling, enable is {}.".format(row["enable"]))
        row["enable"] = not row["enable"]
        self.controller.database.blocking_update(
            ChatTranslatorTable, row)
        if row["enable"]:
            self.controller.server.pm(
                player, "Translations are now enabled to {}.".format(
                    row["target_language"]))
        else:
            self.controller.server.pm(player, "Translations are now disabled.")

    def toggle_language(self, player, language):
        answer = self.controller.database.blocking_consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])])
        if len(answer) == 0:
            self.logger.info("New entry on chat_translator_table.")
            self.controller.database.blocking_add(
                ChatTranslatorTable,
                [ChatTranslatorTable(
                    steamid = player["steamid"],
                    enable = True,
                    languages_known = language,
                    target_language = language)])
            self.controller.server.pm(
                player, "Language {} added to your database. Also, translations"\
                " have been enabled to this target language.".format(language))
            return
        if len(answer) == 1:
            self.logger.info("Updating db entry.")
            db_entry = answer[0]
            matcher = re.compile(language)
            match = matcher.search(db_entry["languages_known"])
            if not match:
                db_entry["languages_known"] += " " + language
                self.controller.server.pm(
                    player, "Language {} added to your database.".format(
                        language))
            else:
                db_entry["languages_known"] = db_entry["languages_known"].replace(language, "")
                self.controller.server.pm(
                    player, "Language {} removed from your database.".format(
                        language))
                if db_entry["target_language"] == language:
                    db_entry["target_language"] = None
                    db_entry["enable"] = False
            self.controller.database.blocking_update(
                ChatTranslatorTable,
                db_entry)
            return
        if len(answer) > 1:
            self.logger.error("Entry not unique in db.")
            return
        
    def set_target_language(self, player, language):
        if language not in googletrans.LANGUAGES.keys():
            self.controller.server.pm(player, "Language not known to system.")
        answer = self.controller.database.blocking_consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])])
        if len(answer) != 1:
            self.log.error("DB entry is not unique.")
            return
        chat_translator = answer[0]
        if language not in chat_translator["languages_known"]:
            self.toggle_language(player, language)
        chat_translator["target_language"] = language
        self.controller.database.blocking_update(
            ChatTranslatorTable,
            chat_translator)
        self.controller.server.pm(
            "Your target language for translations is now {}.".format(
                language))

    def print_language_codes(self, player):
        for key in googletrans.LANGUAGES.keys():
            try:
                response += ", {}:{}".format(key, googletrans.LANGUAGES[key])
            except:
                response = "{}:{}".format(key, googletrans.LANGUAGES[key])
        self.controller.telnet.write('pm {} "{}"'.format(
            player["steamid"], response))
