from sqlalchemy import (Boolean, Column, Float, Integer, String, Table)
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class TableCooldowns(Base, Table_abstract):
    __tablename__ = "cooldowns"
    aid = Column(Integer, primary_key = True)
    steamid = Column(Integer)
    bears = Column(Integer, default = 0)
    challenge = Column(Integer, default = 0)
    portals_player = Column(Integer, default = 0)
    portals_portal = Column(Integer, default = 0)
    relax = Column(Integer, default = 0)
    
    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "bears" : { "multiplicity" : 0 },
               "challenge": {"multiplicity": 0},
               "portals_player": {"multiplicity": 0},
               "portals_portal": {"multiplicity": 0},
               "relax": {"multiplicity": 0}}
