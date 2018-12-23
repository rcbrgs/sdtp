from sqlalchemy import ( Boolean, Column, Float, Integer, String, Table )
from sqlalchemy.ext.declarative import declarative_base

from sdtp.Table_abstract import Table_abstract

Base = declarative_base ( )

class ChatTranslatorTable ( Base, Table_abstract ):
    __tablename__ = "chat_translator"
    aid = Column ( Integer, primary_key = True )
    steamid = Column ( Integer )
    enable = Column ( Boolean, default = False )
    languages_known = Column ( String )
    target_language = Column ( String )

    def create ( self, engine ):
        global Base
        Base.metadata.create_all ( engine )

    fields = { "aid" : { "multiplicity" : 0 },
               "steamid" : { "multiplicity" : 0 },
               "enable" : { "multiplicity" : 0 },
               "languages_known": {"multiplicity": 0},
               "target_language": {"multiplicity": 0}}
