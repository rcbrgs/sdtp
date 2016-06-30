# -*- coding: utf-8 -*-

class Table_abstract ( object ):

    def __expr__ ( self ):
        for field in self.__class__.fields.keys ( ):
            try:
                expression += ",{}={}".format ( field, getattr ( self, field ) )
            except UnboundLocalError:
                expression = "<{}({}={}".format ( self.__class__.__name__, field, getattr ( self, field ) )
        expression += ")>"
        return expression

    def __str__ ( self ):
        return self.__expr__ ( )
    
    def create_from_dictionary ( self, dictionary ):
        kwargs = { }
        for field_name in self.__class__.fields.keys ( ):
            if field_name == "aid":
                continue
            field = self.__class__.fields [ field_name ]
            if field [ "multiplicity" ] in [ "0", "1" ]:
                try:
                    kwargs [ field_name ] = dictionary [ field_name ]
                except Exception as e:
                    self.log ( "debug", "Ignoring field {}: exception {}.".format ( field_name, e ) )
        return self.__class__ ( **kwargs )

    def get_dictionary ( self ):
        result = { }
        for field_name in self.fields.keys ( ):
            if self.fields [ field_name ] [ "multiplicity" ] in [ 0, 1 ]:
                result [ field_name ] = getattr ( self, field_name )
                continue
            row_list = getattr ( self, field_name )
            if row_list == None:
                row_list = [ ]
            aid_list = [ ]
            for row in row_list:
                aid_list.append ( row.aid )
            result [ field_name ] = aid_list
        return result

    # cheat sheet:

    # join with multiple foreigns keys between tables:
    # query = session.Query ( class_A )
    # query.join ( class_B.relationship_with_A ) where relationship_with_A is defined on the table class_B.
    
