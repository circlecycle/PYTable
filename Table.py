
## Author: James Robey, jrobey.services@gmail.com, c.2012
## a module to simpilify SQL commands greatly.

import psycopg2, re
    
class Table:
    """ Table makes SQL statements in python easier. Examples:
    
        Instead of:
            SELECT height, age FROM sometable WHERE firstname = 'james', lastname = 'robey';
        you can say:
            Table('sometable').where(firstname='james', lastname='robey').get('height', 'age')
        
        Instead of:
            UPDATE sometable SET firstname = 'james', lastname = 'robey' WHERE person_id = '8823'; -- or INSERT as needed if it's not there
        you can say:
            Table('sometable').where(person_id=8823).set(firstname='james', lastname='robey')
            
        Instead of:
            INSERT INTO sometable (firstname, lastname) VALUES ('james', 'robey'); -- duplicate rows are not an intended use of this system (i.e. PK always assumed)!
        you can say:
            Table('sometable').where(firstname='james', lastname='robey').set()
            
        Instead of:
            DELETE FROM sometable WHERE firstname = 'james', lastname = 'robey';;
        you can say:
            Table('sometable').where(firstname='james', lastname='robey').remove()
    """
    
    #this will be set on the class (as a class attribute) by a (the) server when it starts.
    salt = "NONE"
    
    #This is how we figure how to login. Set it by calling Table.login(user, pass, db) before your first use of the other API.
    credentials = {'user':None, 'password':None, 'dbname':None}
    
    @classmethod
    def login(self, user, password, dbname):
        """ Credentials are shared by all instances. I take the provided credentials and save them for the future instances to use when connecting """
        self.credentials['user'], self.credentials['password'], self.credentials['dbname'] = user, password, dbname
    
    @classmethod 
    def create(self, tableid, schema="key VARCHAR(40) PRIMARY KEY, value TEXT"):
        """ I will create a table using the default schema, or one provided as the 2nd argument
            i.e. Table.create("sometable")
        """
        try:
            connection = psycopg2.connect("dbname=%s user=%s password=%s"%(self.credentials['dbname'], self.credentials['user'], self.credentials['password']))
            connection.cursor().execute("CREATE TABLE %s (%s);"%(tableid, schema))
            connection.commit()
            connection.close()
            
        #make it so we dont raise if we only try (and fail) to overwrite
        except Exception, err:
            if str(err).endswith("already exists\n"):
                print "[Table] Exists %s (%s)"%(tableid, schema)
                return False
            else:
                print "[Table] Error when processing %s (%s)"%(tableid, schema)
                raise err
                
        print "[Table] Created %s (%s)"%(tableid, schema)
        return True
        
    @classmethod 
    def drop(self, tableid):
        """ I will drop a table using the table name provided, i.e. Table.drop("sometable") """
        try:
            connection = psycopg2.connect("dbname=%s user=%s password=%s"%(self.credentials['dbname'], self.credentials['user'], self.credentials['password']))
            connection.cursor().execute("drop table %s;"%(tableid))
            connection.commit()
            
        #make it so we dont raise if we only try (and fail) to overwrite
        except Exception, err:
            if str(err).endswith("already exists\n"):
                return False
            else:
                raise err
            
        finally:
            connection.close()
    
    def __init__(self, tableid):
        """ I use the table name passed as context for all other operations. i.e. Table("sometable") """
        self.tableid = tableid
        self.connection = psycopg2.connect("dbname=%s user=%s password=%s"%(self.credentials['dbname'], self.credentials['user'], self.credentials['password']))
        self.cursor = self.connection.cursor()
        self.join_info = False
        self.query_string = ""
        self.where_joins = False
        
    def where(self, **args):
        """ I return myself; I provide the context for the CRUD operations other methods use 
            i.e. Table('sometable').where(key='a').doSomething(x) 
        """
        self.where_names, self.where_values, self.where_pairs, self.where_joins = self.dictToSQLFragments(args)
        return self
        
    def join(self, table, column):
        # modify the where joins to include the new table
        ##self.where_names = "%s.%s = %s.%s"%(table, column, self.tableid, column)
        ##self.where_pairs = "%s.%s = %s.%s"%(table, column, self.tableid, column)
        
        self.join_info = [table, column]
        return self
    
    def has(self, **args):
        """ I am the only one that doesn't use the where clause -- invoke me on the table instance to return
            true or false if one or moe rows that match exist. This is more efficient then using get() or query()
            i.e. Table("sometable").has(key="1234")
        """
        column_names, column_values, column_pairs, column_joins = self.dictToSQLFragments(args)
        self.cursor.execute("SELECT true FROM %s WHERE %s LIMIT 1;"%(self.tableid, column_joins))
        item = self.cursor.fetchone()
        if not item: return False
        else:        return True
    
    def remove(self):
        """ Presuming the where method has chosen a target, i'll remove the row or rows indicated
            i.e. Table('sometable').where(key='a').remove()
        """
        self.cursor.execute("DELETE FROM %s WHERE %s"%(self.tableid, self.where_joins))
        self.connection.commit()
        return self
     
    def set(self, **args):
        """ Presuming the where method has chosen a target, i'll set the column values on that row using the args 
            i.e. Table('sometable').where(key='a').set(name='james') 
        """
        
        if self.join_info:
            raise "Cannot use .join() with .set(), when trying to save at ", self.where_names
        
        column_names, column_values, column_pairs, column_joins = self.dictToSQLFragments(args)
        
        #if the item already exists (this is quick test) update it, instead of inserting
        self.cursor.execute("SELECT true FROM %s WHERE %s LIMIT 1;"%(self.tableid, self.where_joins))
        item = self.cursor.fetchone()
        
        #if an entry exists...
        if item:    
            #then if they called set() with no args, substitute the where_pairs..
            if not column_pairs: column_pairs = self.where_pairs
            statement = "UPDATE %s SET %s WHERE %s;"%(
                self.tableid, 
                column_pairs, 
                self.where_joins
            )
            
        #else if we need to insert a new record
        else:
            #then add a comma behind column_names and column_values to make them smoothly add to the where_names and where_values
            if column_names:    column_names = ", %s"%(column_names)
            if column_values:   column_values = ", %s"%(column_values)
            
            statement = "INSERT INTO %s (%s%s) VALUES (%s%s);"%(
                self.tableid, 
                self.where_names, column_names, 
                self.where_values, column_values
            )
            
        self.cursor.execute(statement)
        self.connection.commit()
        return self
        
    def _select(self, args=[], limitone=False):
        """
            I will execute a select on the cursor, such that the calling function
            can use self.cursor.fetch.... to get the result.
            
            More: set up the select such that it will return a column or list of rows from the jointable specified 
            where the column name matched on both.

            i.e. Table('trust_message_users').where(user_id=hashed_message_key).join('trust_messages', 'message_id').fetch('value')
            this will get the value of all messages where there is an message_id trust_message_users indicating the user_id has that ownership

            The following is just notes:

            SELECT trust_messages.value 
                FROM trust_messages, trust_message_users
                WHERE trust_message.message_id = trust_message_users.message_id 
                AND trust_message_users.user_id = '520f26294d3de705f3ed3463f0e2872f97f9651b'; 
        """
        
        if limitone:    limitone = "LIMIT 1"
        else:           limitone = ""
        
        #Process the .join() select style statement, if that state was was invoked.
        if self.join_info:
            #get the info on the join to make
            jointable, joincolumn = self.join_info
            
            #if not args, use jointable.*, else use jointable.var1, jointable.var2, etc....
            if not args:
                selectargs = "%s.*"%(jointable)
            else:
                selectargs = ",".join(
                    ["%s.%s"%(jointable, arg) for arg in args]
                )
            
            #run the sql meant to return a list of items from a table other then the init table,
            #and using some extra query string if possible
            statement = "SELECT %s FROM %s, %s WHERE %s.%s = %s.%s AND %s %s %s;"%(
                selectargs, 
                jointable, self.tableid, 
                jointable, joincolumn, 
                self.tableid, joincolumn, 
                self.where_joins, 
                self.query_string,
                limitone
            )
            
        else:
            #make sure the selectargs are either all (*) or the args passed
            selectargs = args
            
            if not selectargs: 
                selectargs = ['*']
                
            #the base statement 
            statement = "SELECT %s FROM %s"%(
                ','.join(selectargs), 
                self.tableid, 
            )
            
            #are there joins?
            if self.where_joins:
                statement = "%s WHERE %s"%(
                    statement,
                    self.where_joins,
                )
                
            #are we getting one or all?
            if limitone:
                statement = "%s %s"%(
                    statement,
                    limitone
                )
                
            #finish it off.
            statement = "%s;"%(statement)
            
        self.cursor.execute(statement)
        
        if limitone:
            return self.cursor.fetchone()
        else:
            return self.cursor.fetchall()
        
    def get(self, *args):
        """ Presuming the where method has chosen a target, I am meant to make it easy to get one (or more)
            column value(s) from a /single/ row efficiently by not loading columns we dont need (i.e. not select *)
            i.e. Table('sometable').where(key='a').get('name') 
        """

        item = self._select(args=args, limitone=True)
        
        #if a single item was asked for, return a single value (not a single value in a list)
        if item:
            if len(item) == 1: 
                return item[0]
            return item
            
        return None   
        
    def fetch(self, *args):
        """ Presuming the where method has chosen a target, i'll return all the rows i get back that match, as 
            in select *. By returning all rows returned, i am the partner of .get(), when all matches are desired.
            i.e. Table('sometable').where(key='a').fetch() 
        """
        
        items = self._select(args=args, limitone=False)

        #if a single item was asked for, return a plain list of just that.
        if len(args) == 1:
            output = []
            for item in items:
                output.append(item[0])
            return output
        else:
            return items
            
    def query(self, query_string):
        self.query_string = "AND %s"%(query_string)
        
    def dictToSQLFragments(self, args):
        """ I will return a tuple of information needed to abstract a dictionary 
            into the formats that methods compositing SQL statements generally need.
            Makes for short methods, above. It is escaped here instead of .excute() parameters
            Beacuse 
        """
        
        if len(args) == 0:
            return ("", "", "", "")
        
        keys = args.keys()

        #calculate first item for each type
        column_names = keys[0]
        column_values = "'%s'"%(args[keys[0]])
        column_pairs = "%s = '%s'"%(keys[0], args[keys[0]])
        column_joins = "%s = '%s'"%(keys[0], args[keys[0]])

        #all the rest of the items for each type (diff. in having a delimiter)
        if len(keys) > 1:
            for f in keys[1:]:
                column_names = "%s, %s"%(column_names, f)
                column_values = "%s, '%s'"%(column_values, args[f])
                column_pairs = "%s, %s = '%s'"%(column_pairs, f, args[f])
                column_joins = "%s AND %s = '%s'"%(column_joins, f, args[f])

        #outputs properly delimited strings for each type
        return (column_names, column_values, column_pairs, column_joins)
        
    
### a set of test commands.
if __name__ == "__main__":    
    print "\nBASIC SET AND GET TESTING ##################################################\n"
    
    #we have to login
    print """Table.login('jrobey', 'letmein', 'files')""",\
        Table.login('jrobey', 'letmein', 'files')
    
    #we have to create a table (default is 40 char key and text i.e. key value store, i.e. sha1+anything)
    print """Table.create("SomeTable")""",\
        Table.create("SomeTable")
    
    #make a reference to a table object pointing at it.    
    store1 = Table("SomeTable") 
    
    #and store a new row.
    store1.where(key="hi", value="there").set()
    
    #then, see if we found what we just inserted
    print "store1.has('1234')",\
        store1.has(key="1234")
        
    #this time, find the entry where key=1234 and update it 
    print """store1.where(key="1234").set(value="4567")""",\
        store1.where(key="1234").set(value="4567")
        
    #did that work?
    print "store1.has('1234')",\
        store1.has(key="1234")
        
    #now try getting one entire row as a result
    print """store1.where(key="1234").get()""",\
        store1.where(key="1234").get()
    
    #now try removing all keys with 1234
    print """store1.where(key="1234").remove()""",\
        store1.where(key="1234").remove()
        
    #did it work?
    print """store1.where(key="1234").get()""",\
        store1.where(key="1234").get()
    
    #lets test tables with more advanced schema
    print "\nKWARGS TESTING ##################################################\n"
    
    #make a table called test2 with the postgres schema statement you see in the quotes:
    print """Table.create("test2", ...)""",\
        Table.create("test2", """
            key VARCHAR(40) PRIMARY KEY, identity TEXT, pubsignkey TEXT, groups TEXT, lastlogin VARCHAR(100)
        """)
    
    #and make a reference
    store2 = Table("test2")
    
    #try updating the key 1234 row with all these values (if not there, will be made)
    print """store2.where(key="1234").set(...)""",\
        store2.where(key="1234").set(
            identity="94092ijgjks", 
            pubsignkey="4gjnef24hig", 
            groups="groupsA, groupsB", 
            lastlogin="last1"
        )
        
    #try setting a new key side by side
    print """store2.where(key="1235").set(...)""",\
        store2.where(key="1235").set(
            identity="90dkwemgo4j95k", 
            pubsignkey="k0492ijrkkrhg", 
            groups="groupsC, groupsD", 
            lastlogin="last2"
        )
    
    #did it all work? (get key 1235)
    print """store2.where(key='1235').get()""",\
        store2.where(key='1235').get()
    
    #lets try setting a single var on 1235
    print """store2.where(key='1235').set(identity='identity')""",\
        store2.where(key='1235').set(identity='identity')
        
    #try getting two values from the row with key=1235
    print "store2.get(key='1235', ('identity', 'groups'))",\
        store2.where(key='1235').get('identity', 'groups')
    
    #lets test using the framework in regards to insert/select
    print "\nINSERT/SELECT TESTING ##################################################\n"
    
    #make a simple table to work with
    print """Table.create("test3", ...)""",\
        Table.create("test3", "key VARCHAR(40) PRIMARY KEY, name VARCHAR(64), color VARCHAR(6)")
        
    #and get a referernce
    store3 = Table('test3')
    
    #see if we can make a new row
    print """store3.where(key="a").set(name="james", color="ff0000")""",\
        store3.where(key="a").set(name="james", color="ff0000")
        
    #another new row
    print """store3.where(key="b").set(name="bob", color="0000ff")""",\
        store3.where(key="b").set(name="bob", color="0000ff")
        
    #an third - note all different name/color values
    print """store3.where(key="c").set(name="jill", color="770077")""",\
        store3.where(key="c").set(name="jill", color="770077")
    
    #see if we can get the row with name james
    print """store3.where(name="james").get()""",\
        store3.where(name="james").get()
        
    #see if we can get the row with color 0000ff
    print """store3.where(color="0000ff").get()""",\
        store3.where(color="0000ff").get()
        
    #see if we can get just the color with row key='c' (NOT an array, just the value)
    print """store3.where(key="c").get('color')""",\
        store3.where(key="c").get('color')
        
    #see if we can get a list of all colors where key="c"
    print """store3.where(key="c").fetch()""",\
        store3.where(key="c").fetch('color')
    
    #try removing all rows with key=c
    print """store3.where(key="c").remove()""",\
        store3.where(key="c").remove()
        
    #did it work?
    print """store3.where(key="c").get()""",\
        store3.where(key="c").get()
        
    #that sums it up
    print "\nFINIS. ##########################"
    
"""
    Hope you enjoyed.
    Author: James Robey, jrobey.services@gmail.com, c.2012
    A module to simpilify SQL commands greatly.
"""
