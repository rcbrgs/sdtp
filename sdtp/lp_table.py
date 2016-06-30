# -*- coding: utf-8 -*-

from sqlalchemy import ( Column, Float, Integer, String, Table )
from sqlalchemy.ext.declarative import declarative_base
from .Table_abstract import Table_abstract

Base = declarative_base ( )

class lp_table ( Base, Table_abstract ):
    __tablename__ = "lp"
    player_id = Column ( Integer ) # 0
    name = Column ( String ) # 1
    longitude = Column ( Float )
    height = Column ( Float )
    latitude = Column ( Float )
    rotation_longitude = Column ( Float )
    rotation_height = Column ( Float )
    rotation_latitude = Column ( Float )
    remote = Column ( String )
    health = Column ( Integer )
    deaths = Column ( Integer )
    zombies = Column ( Integer )
    players = Column ( Integer )
    score = Column ( Integer )
    level = Column ( Integer )
    steamid = Column ( Integer, primary_key = True )
    ip = Column ( String )
    ping = Column ( Integer )

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "player_id" : { "multiplicity" : 0 },
               "name" : { "multiplicity" : 0 },
               "longitude" : { "multiplicity" : 0 },
               "height" : { "multiplicity" : 0 },
               "latitude" : { "multiplicity" : 0 },
               "rotation_longitude" : { "multiplicity" : 0 },
               "rotation_height" : { "multiplicity" : 0 },
               "rotation_latitude" : { "multiplicity" : 0 },
               "remote" : { "multiplicity" : 0 },
               "health" : { "multiplicity" : 0 },
               "deaths" : { "multiplicity" : 0 },
               "zombies" : { "multiplicity" : 0 },
               "players" : { "multiplicity" : 0 },
               "score" : { "multiplicity" : 0 },
               "level" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "ip" : { "multiplicity" : 0 },
               "ping" : { "multiplicity" : 0 } }
