Seven Days To Py
================

This is an application that helps you administer a Seven Days to Die server, and adds a few capabilities to the game server.

It is a second iteration of an idea originally by Benjamin Keller, and developed by Renato Callado Borges (rc when in-game).

It is a multiplatform app, and rc will regularly build the Linux and Windows 64 bits binaries, which should also self-update when updates are available. It is possible to build Mac binaries, but since rc doesn't have an Apple machine to do this, someone else must step forward to help with this.

Installation in all systems consist of unzipping the file in the directory of your choice (warning: the zip files *do* contain files in the root of the zip, and I cannot avoid this. So please create a folder to hold the files, and unzip the contents there). Then, the executable file sdt can be run.

Configuration
=============

SDTP will save two hidden files: one is a JSON file with the configuration parameters (including a PLAIN TEXT VERSION OF YOUR TELNET PASSWORD - use at your own risk), the other is a SQLite database. In Linux, these files are in the $HOME directory. In Windows, these files are in the %ALLUSERSPROFILE% directory.

When running for the first time, please configure your telnet connection. Once that is done, all functionalities should be available, and the app should be self-explanatory.

A log file with all the info from SDTP is also saved on the same directory as the config and database files, and is named sdtp.log. It is advised to turn off the "debug" level of logging, or that file might grow by several hundred megabytes per day. If that happens, this file can be deleted safely.

