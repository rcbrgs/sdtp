Seven Days To Py
================

This is an application that helps you administer a Seven Days to Die server, and adds a few capabilities to the game server.

It is the third iteration of an idea originally by Benjamin Keller, and developed by Renato Callado Borges (rc when in-game).

It consists of a linux Python script that runs on the command-line. All interaction is done via the game chat.

Configuration
=============

SDTP will save two files: one is a JSON file with the configuration parameters (including a PLAIN TEXT VERSION OF YOUR TELNET PASSWORD - use at your own risk), the other is a SQLite database. In Linux, these files are in the directory where you run sdtp.

When running for the first time, please configure your telnet connection. Once that is done, all functionalities should be available, and the app should be self-explanatory.

A log file with all the info from SDTP is also saved on the same directory as the config and database files, and is named sdtp.log. It is advised to turn off the "debug" level of logging, or that file might grow by several hundred megabytes per day. If that happens, this file can be deleted safely.
