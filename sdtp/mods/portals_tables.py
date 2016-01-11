from sqlalchemy import ( Column, Float, Integer, String, Table )
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base ( )

class portals_table ( Base ):
    __tablename__ = "portals"
    aid = Column ( Integer, primary_key = True )
    steamid = Column ( Integer )
    name = Column ( String )
    latitude = Column ( Integer )
    longitude = Column ( Integer )
    height = Column ( Integer )

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )
