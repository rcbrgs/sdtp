from sqlalchemy import (Boolean, Column, Float, Integer, String, Table)
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class FriendshipsTable(Base, Table_abstract):
    __tablename__ = "friendships"
    aid = Column(Integer, primary_key = True)
    player_steamid = Column(Integer)
    friend_steamid = Column(Integer)
    
    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "player_steamid" : { "multiplicity" : 0 },
               "friend_steamid" : { "multiplicity" : 0 }}
