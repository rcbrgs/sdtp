from sqlalchemy import (Boolean, Column, Float, Integer, String, Table)
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class AliasTable(Base, Table_abstract):
    __tablename__ = "alias"
    aid = Column(Integer, primary_key = True)
    steamid = Column(Integer)
    alias = Column(String)

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "alias" : { "multiplicity" : 0 } }
