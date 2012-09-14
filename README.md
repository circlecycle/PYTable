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
    INSERT INTO sometable (firstname, lastname) VALUES ('james', 'robey'); -- duplicate rows are not an intended use of this system (i.e. PK always assumed)!

you can say:
    Table('sometable').where(firstname='james', lastname='robey').set()
            
Instead of:
    DELETE FROM sometable WHERE firstname = 'james', lastname = 'robey';;

you can say:
    Table('sometable').where(firstname='james', lastname='robey').remove()

NOTE you must first use the login function to use the rest of the API. it requires the username, password, and db name to use.

If you have a question you may email me at jrobey.services@gmail.com with "PYTable" in the subject.
