from sqlalchemy import (Boolean, Column, Float, Integer, String, Table)
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class llp_table(Base, Table_abstract):
    __tablename__ = "llp"
    aid = Column(Integer, primary_key = True)
    steamid = Column(Integer)
    latitude = Column(Integer)
    longitude = Column(Integer)
    height = Column(Integer)
    alarm_type = Column(String)

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "longitude" : { "multiplicity" : 0 },
               "height" : { "multiplicity" : 0 },
               "latitude" : { "multiplicity" : 0 },
               "alarm_type" : { "multiplicity" : 0 } }
