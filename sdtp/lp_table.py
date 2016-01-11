# -*- coding: utf-8 -*-

from sqlalchemy import ( Column, Float, Integer, String, Table )
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base ( )

class lp_table ( Base ):
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
