Seven Days To Py
================

This is an application that helps you administer a Seven Days to Die server, and adds a few capabilities to the game server.

It is the third iteration of an idea originally by Benjamin Keller, and developed by Renato Callado Borges (rc when in-game).

It consists of a linux Python script that runs on the command-line. All interaction is done via the game chat.

Installation
============

First, clone the github repo:

    git clone https://github.com/rcbrgs/sdtp.git

Install all the libraries upon which sdtp depends. Which unfortunately change depending on your distribution. In a Fedora machine, these are:

    sudo dnf install python3-sqlalchemy python3-googletrans 

Install sdtp in your system:

    sudo python3 sdtp/setup.py install

Notice: running the above command from the incorrect directory will give errors, because setup.py's is very picky concerning relative directories.

Configuration
=============

SDTP will save two files: one is a JSON file with the configuration parameters (including a PLAIN TEXT VERSION OF YOUR TELNET PASSWORD - use at your own risk), the other is a SQLite database. In Linux, these files are in the directory where you run sdtp.

When running for the first time, please configure your telnet connection. Once that is done, all functionalities should be available, and the app should be self-explanatory.

A log file with all the info from SDTP is also saved on the same directory as the config and database files, and is named sdtp.log. It is advised to turn off the "debug" level of logging, or that file might grow by several hundred megabytes per day. If that happens, this file can be deleted safely.

The recipe for configuration is: first, create a directory to contain the files from sdtp:

    mkdir your_server_name
    cd your_server_name

Then, run sdtp; wait a few seconds and stop it with Ctrl+C.

    sdtp
    ^C

Now you will have a few files in the current folder. The configuration file is sdtp_preconfig.json, so go ahead and edit it:

    emacs sdtp_preconfig.json

After you selected mods to be enabled and the parameters values, save the file and run sdtp again:

    sdtp

Nothing will be printed in the screen, but you can see the log in sdtp.log in the same folder as you are running sdtp.

Updating
========

Once in a while sdtp will be updated. When that happens, you should update your cloned repository, rebuild and re-run the mod. The instructions are:

    cd sdtp
    git pull
    cd ..
    python3 sdtp/setup.py install
    
    cd your_server_name
    sdtp

    