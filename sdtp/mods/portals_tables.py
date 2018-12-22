from sqlalchemy import ( Boolean, Column, Float, Integer, String, Table )
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class PortalsTable ( Base, Table_abstract ):
    __tablename__ = "portals"
    aid = Column ( Integer, primary_key = True )
    steamid = Column ( Integer )
    name = Column ( String )
    latitude = Column ( Integer )
    longitude = Column ( Integer )
    height = Column ( Integer )
    public = Column ( Boolean )

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "name" : { "multiplicity" : 0 },
               "longitude" : { "multiplicity" : 0 },
               "height" : { "multiplicity" : 0 },
               "latitude" : { "multiplicity" : 0 },
               "public" : { "multiplicity" : 0 } }
