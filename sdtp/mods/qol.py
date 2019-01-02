# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import random
import re
import threading
import time

from sdtp.lkp_table import lkp_table

class Qol(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_qol_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.animals_spawned_today = []
        self.gimmes_given = {}
        self.help_animals = {
            "animals": "Will spawn a few animals around you."}
        self.controller.help.registered_commands["animals"] = self.help_animals
        self.help_day7 = {
            "day7": "Will tell how many days until blood moon."}
        self.controller.help.registered_commands["day7"] = self.help_day7
        self.help_gimme = {
            "gimme": "Will give you a random item."}
        self.controller.help.registered_commands["gimme"] = self.gimme
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.register_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "player joined", self.announce_player_connected)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.deregister_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "player connected", self.announce_player_connected)
        
    def check_for_commands(self, match_groups):
        self.logger.debug("match_groups = {}".format(match_groups))
        command = ""
        matcher = re.compile(r"^/animals$")
        match = matcher.search(match_groups[11])
        if match:
            command = "animals"
        self.logger.debug(match_groups)
        matcher = re.compile(r"^/day7$")
        match = matcher.search(match_groups[11])
        if match:
            command = "day7"
        matcher = re.compile(r"^/gimme$")
        match = matcher.search(match_groups[11])
        if match:
            command = "gimme"
        if command == "":
            return
        player = self.controller.database.blocking_consult(
            lkp_table,
            [(lkp_table.steamid, "==", match_groups[7])])[0]
        self.logger.debug("Parsing command '{}'.".format(command))
        if command == "animals":
            self.spawn_animals(player)
            return
        if command == "day7":
            self.print_blood_moon_count(player)
            return
        if command == "gimme":
            self.gimme(player)
            return

    # Mod specific
    ##############

    def print_blood_moon_count(self, player):
        today = self.controller.worldstate.day
        if today % 7 == 0:
            self.controller.telnet.write('say "Blood moon is tonight, baby. Woohoo!"')
            return
        if today % 7 == 6:
            self.controller.telnet.write('say "Blood moon is tomorrow! OMG!"')
            return
        self.controller.telnet.write('say "Blood moon is in {} days."'.format(
            7 - int(today % 7)))

    def reset_daily_counts(self, match_groups):
        self.logger.debug(match_groups)
        self.animals_spawned_today = []

    def spawn_animals(self, player):
        if player["steamid"] in self.animals_spawned_today:
            self.controller.telnet.write('pm {} "You already spawned your animals for today."'.format(player["steamid"]))
            return
        self.animals_spawned_today.append(player["steamid"])
        for count in range(self.controller.config.values["mod_qol_animals_quantity"]):
            animal = random.choice([81, 82, 83, 84])
            self.controller.telnet.write(
                "se {} {}".format(player["player_id"], animal))

    def gimme(self, player):
        now = time.time()
        if player["steamid"] in self.gimmes_given.keys():
            if now - self.gimmes_given[player["steamid"]] < self.controller.config.values["mod_qol_gimme_cooldown_minutes"] * 60:
                self.controller.telnet.write('pm {} "Your gimme is in cooldown."'.format(player["steamid"]))
                return
        self.gimmes_given[player["steamid"]] = now
        food_items = [
            "foodHoney",
            "foodCanBeef",
            "foodCanChicken",
            "foodCanLamb",
            "foodCanCatfood",
            "foodCanDogfood",
            "foodCanChili",
            "foodCanTuna",
            "foodCanHam",
            "foodCanPasta",
            "foodCanSalmon",
            "foodCanMiso",
            "foodCanPeas",
            "foodCanPears",
            "foodCanSoup",
            "foodCanStock",
            "foodCornOnTheCob",
            "foodCornBread",
            "foodMoldyBread",
            "foodShamSandwich",
            "foodCharredMeat",
            "foodGrilledMeat",
            "foodBoiledMeat",
            "foodMeatStew",
            "foodSteakAndPotato",
            "foodShamChowder",
            "foodHoboStew",
            "foodFishTacos",
            "foodChiliDog",
            "foodBakedPotato",
            "foodBlueberryPie",
            "foodEggBoiled",
            "foodBaconAndEggs",
            "foodVegetableStew",
            "foodRawMeat",
            "foodRottingFlesh",
            "foodEgg",
            "foodCornMeal",
            "foodCropBlueberries",
            "foodCropCorn",
            "foodCropGraceCorn",
            "foodCropPotato",
            "foodCropMushrooms",
            "foodCropYuccaFruit",
            ]
        
        if self.controller.config.values["mod_qol_gimme_what"] == "food":
            prize = random.choice(food_items)
        else:
            prize = self.controller.config.values["mod_qol_gimme_what"]
            
        self.controller.telnet.write(
            "give {} {} {}".format(player["player_id"], prize, self.controller.config.values["mod_qol_gimme_quantity"]))

    def announce_player_connected(self, match_groups):
        self.logger.debug(match_groups)
        db = self.controller.database.blocking_consult(
            lkp_table, [(lkp_table.name, "==", match_groups[7])])
        if len(db) != 1:
            self.logger.error("Player db entry non unique.")
            return
        player = db[0]
        self.controller.telnet.write('pm {} "{}"'.format(
            player["steamid"], self.controller.config.values[
                "mod_qol_greeting"]))
