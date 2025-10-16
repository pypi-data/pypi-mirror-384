**Separate DB client from DivineGift**

# How to use it

## Install this packages before use

* cx_Oracle             - Oracle driver
* sqlalchemy-pytds      - MSSQL driver
* psycopg2-binary       - Postgres driver

## Usage

You should define dict with db_conn creditional.
For example:

### Oracle
Install oracle driver:
```
pip install cx_oracle
```
```
db_conn = {
    "db_user": "dbuser",             # username
    "db_pass": "dbpass",             # password
    "db_host": "dbhost",             # host (ip, fqdn). could be empty if we connect via tns
    "db_port": "",                   # port (string). could be empty if we connect via tns
    "db_name": "dbname",             # database name
    "db_schm": "",                   # db scheme if not equal username
    "dialect": "oracle"              # if use cx_Oracle or oracle+another_dialect
}
```
### MSSQL
Install mssql driver:
```
pip install sqlalchemy-pytds
```
```
db_conn = {
    "db_user": "dbuser",             # username
    "db_pass": "dbpass",             # password
    "db_host": "",                   # host (ip, fqdn). could be empty if we connect via tns
    "db_port": "",                   # port (string). could be empty if we connect via tns
    "db_name": "dbname",             # database name
    "db_schm": "",                   # db scheme if not equal username
    "dialect": "mssql+pytds"         # mssql dialect
}
```
### Postgres
Install postgres driver:
```
pip install psycopg2
```
```
db_conn = {
    "db_user": "dbuser",             # username
    "db_pass": "dbpass",             # password
    "db_host": "",                   # host (ip, fqdn). could be empty if we connect via tns
    "db_port": "",                   # port (string). could be empty if we connect via tns
    "db_name": "dbname",             # database name
    "db_schm": "",                   # db scheme if not equal username
    "dialect": "postgresql+psycopg2" # dialect
}
```

### Create connection

Use class DBClient to create connection to DB. Old-styled functions, which contained in *divinegift.db* module directly, are deprecated but still works.
```
from divinegift.db import DBClient
connection = DBClient(db_conn)            # db_conn - variable which was described above
# Describe which fields you wants to method get_conn will returned (possible fields are 'engine', 'conn' and 'metadata')
engine, conn, metadata = connection.get_conn(fields=['engine', 'conn', 'metadata'])  
```

If you need to call stored procedure with db cursors you should use raw connection.
```
from divinegift.db import DBClient
connection = DBClient(db_conn, do_initialize=False)            # db_conn - variable which was described above
connection.set_raw_conn()
conn = connection.get_conn(fields='conn')  
```

### Get data from sript (file or just string)

After you got "connection" variable you can  get data from file or from str variable directly.

```
from divinegift.db import DBClient
connection = DBClient(db_conn)

result = connection.get_data('path/to/scripts/some_script.sql')
# or you can use str variable:
script = 'select * from dual'
result = connection.get_data(script)
print(result)
>>>[{'dummy': 'X'}]
```

You can use specific encoding for your files (by default it's 'cp1251').
Just put it into args:
```
result = connection.get_data('path/to/scripts/some_script.sql', encoding='utf8')
```

Also you can add some variables into your script (e.g. date) and then you can pass it into a function:
```
from divinegift.db import DBClient
connection = DBClient(db_conn)

script = """select * from dual
where dummy = '$param'"""
parameters = {'param': 'X'}
result = connection.get_data(script, **parameters)
# Or another variant
result = connection.get_data(script, param='X')
print(result)
>>>[{'dummy': 'X'}]
```

### Run script without getting data

You can run script without recieving data.
You should use *divinegift.db.DBClient.run_script* for this like get_data, e.g.:
```
from divinegift.db import Connection
connection = Connection(db_conn)
connection.run_script('path/to/scripts/some_script.sql')
```