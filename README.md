PYTable
=======

PYTable (just Table, really) is a wonderfully compact interface (utilizing psycopg2),that makes using postgres (for simple queries) a pure-python proposition.

LICENSE:

This is licensed under a BSD-compatible license of your choice, provided you send me an email at jrobey.services@gmail.com saying how you heard of the project (although I dont ask you send any identifying information in that email, if you dont want to). Otherwise it's licesnsed under the LGPL v2 or v3, which is, again, your choice if you dont want to send me an email.

Table makes SQL statements in python easier. Examples:
    
Instead of:
    SELECT height, age FROM sometable WHERE firstname = 'james', lastname = 'robey';

you can say:
    Table('sometable').where(firstname='james', lastname='robey').get('height', 'age')
        
Instead of:
    UPDATE sometable SET firstname = 'james', lastname = 'robey' WHERE person_id = '8823'; -- or INSERT as needed if it's not there

you can say:
    Table('sometable').where(person_id=8823).set(firstname='james', lastname='robey')
            
Instead of:
    INSERT INTO sometable (firstname, lastname) VALUES ('james', 'robey'); -- exactly duplicate rows are not an intended use of this system (i.e. PK always assumed)!

you can say:
    Table('sometable').where(firstname='james', lastname='robey').set()
            
Instead of:
    DELETE FROM sometable WHERE firstname = 'james', lastname = 'robey';;

you can say:
    Table('sometable').where(firstname='james', lastname='robey').remove()

NOTE you must first use the login function to use the rest of the API. it requires the username, password, and db name to use.

If you have a question you may email me at jrobey.services@gmail.com with "PYTable" in the subject.


Examples
========

I get started here, usally. Each test builds on the next, all features tested.

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
