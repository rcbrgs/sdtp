# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import googletrans
import logging
import re
import threading
import time

from sdtp.lkp_table import lkp_table
from sdtp.lp_table import lp_table
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
        if not self.controller.config.values["mod_chat_translator_enable"]:
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
            "translate <language code>*": "will set the language to translate to."}
        self.controller.help.registered_commands["translate"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.parse_chat_message)
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
        self.translator = googletrans.Translator()
        self.known_languages = ["en",
                                "es",
                                "fr",
                                "ko",
                                "pt",
                                "ru",
                                "zh"]

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
        for player in self.controller.world_state.online_players:
            self.controller.database.consult(
                ChatTranslatorTable,
                [(ChatTranslatorTable.steamid, "==", player["steamid"])],
                self.parse_chat_message_2,
                {"player": player, "detect": detect, "message": message, "emitter": match_groups[10]})

    def parse_chat_message_2(self, answer, player, detect, message, emitter):
        if len(answer) != 1:
            self.logger.error("DB entry not unique.")
            return
        chat_translator = answer[0]
        if not chat_translator["enable"]:
            return
        if detect.lang in chat_translator["languages_known"]:
            return
        translation = self.translator.translate(message, dest=chat_translator["target_language"])
        self.logger.info("Translation to {}: {}".format(
            chat_translator["target_language"], translation))
        self.controller.telnet.write('pm {} "{}: {}"'.format(
            player["steamid"], emitter, translation.text))

    def check_for_commands(self, match_groups):
        matcher = re.compile(r"^/translate[\w]*(.*)$")
        match = matcher.search(match_groups[11])
        if not match:
            self.logger.debug("No match for command regex: {}". format(match_groups[11]))
            return
        command = match.groups()[0].strip()
        self.controller.database.consult(
            lkp_table,
            [(lkp_table.name, "==", match_groups[10])],
            self.check_for_commands_2,
            {"command": command})

    def check_for_commands_2(self, answer, command):
        if len(answer) != 1:
            self.logger.error("Player name not unique in db.")
            return
        player = answer[0]
        self.logger.debug("Parsing command '{}'.".format(command))
        if command == "":
            self.list_languages(player)
            return
        if command == "*":
            self.toggle_enable_translations(player)              
            return
        if command in self.known_languages:
            self.toggle_language(player, command)
            return
        if command[-1] == "*":
            self.set_target_language(player, command[:-1])
            return
        if command == "help":
            self.print_help_message(player)
            return

    def list_languages(self, player):
        self.controller.database.consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])],
            self.list_languages_2,
            {"player": player})

    def list_languages_2(self, answer, player):
        if len(answer) == 0:
            self.controller.telnet.write('pm {} "You don\'t have any languages configured."'.format(player["steamid"]))
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
        self.controller.telnet.write('pm {} "{}"'.format(player["steamid"], response))
        
    def toggle_enable_translations(self, player):
        self.logger.info("Trying to toggle translations for player {}.".format(player["name"]))
        self.controller.database.consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])],
            self.toggle_enable_translations_2,
            {"player": player})

    def toggle_enable_translations_2(self, answer, player):
        self.logger.info("toggle_enable_translations_2")
        if len(answer) != 1:
            self.logger.error("Entry not unique in db.")
            if len(answer) == 0:
                self.logger.debug("Player has no entry in chat_translator_table.")
                self.controller.telnet.write('pm {} "First define a language you know with /translate language"'.format(player["steamid"]))
            return
        row = answer[0]
        self.logger.info("Before toggling, enable is {}.".format(row["enable"]))
        row["enable"] = not row["enable"]
        self.controller.database.update(
            ChatTranslatorTable,
            row,
            print)
        if row["enable"]:
            self.controller.telnet.write('pm {} "Translations are now enabled to {}."'.format(
                player["steamid"], row["target_language"]))
        else:
            self.controller.telnet.write('pm {} "Translations are now disabled."'.format(
                player["steamid"]))

    def toggle_language(self, player, language):
        self.controller.database.consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])],
            self.toggle_language_2,
            {"player": player, "language": language})

    def toggle_language_2(self, answer, player, language):
        if len(answer) == 0:
            self.logger.info("New entry on chat_translator_table.")
            self.controller.database.add_all(
                ChatTranslatorTable,
                [ChatTranslatorTable(
                    steamid = player["steamid"],
                    enable = True,
                    languages_known = language,
                    target_language = language)],
                print)
            self.controller.telnet.write('pm {} "Language {} added to your database. Also, translations have been enabled to this target language."'.format(
                player["steamid"], language))
            return
        if len(answer) == 1:
            self.logger.info("Updating db entry.")
            db_entry = answer[0]
            matcher = re.compile(language)
            match = matcher.search(db_entry["languages_known"])
            if not match:
                db_entry["languages_known"] += " " + language
                self.controller.telnet.write('pm {} "Language {} added to your database."'.format(player["steamid"], language))
            else:
                db_entry["languages_known"] = db_entry["languages_known"].replace(language, "")
                self.controller.telnet.write('pm {} "Language {} removed from your database."'.format(player["steamid"], language))
                if db_entry["target_language"] == language:
                    db_entry["target_language"] = None
                    db_entry["enable"] = False
            self.controller.database.update(
                ChatTranslatorTable,
                db_entry,
                print)
            return
        if len(answer) > 1:
            self.logger.error("Entry not unique in db.")
            return
        
    def set_target_language(self, player, language):
        if language not in self.known_languages:
            self.controller.telnet.write('pm {} "Language not known to system."'.format(player["steamid"]))
        self.controller.database.consult(
            ChatTranslatorTable,
            [(ChatTranslatorTable.steamid, "==", player["steamid"])],
            self.set_target_language_2,
            {"player": player, "language": language})

    def set_target_language_2(self, answer, player, language):
        if len(answer) != 1:
            self.log.error("DB entry is not unique.")
            return
        chat_translator = answer[0]
        if language not in chat_translator["languages_known"]:
            self.toggle_language(player, language)
        chat_translator["target_language"] = language
        self.controller.database.update(
            ChatTranslatorTable,
            chat_translator,
            print)
        self.controller.telnet.write('pm {} "Your target language for translations in now {}."'.format(
            player["steamid"], language))

    def print_help_message(self, player):
        text = "/translate will list your current configuration."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/translate <language code> will toggle if you know a language."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/translate * will enable or disable translations."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/translate <language code>* will set the language to translate to."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
