# sqlalchemy-jdbc-generic
Generic JDBC dialect for SQLAlchemy.

The overall purpose of this dialect is to allow -- _at a minimum_ -- conectivity and consumer query access to any database with an available JDBC driver.

>This codebase was heavily influenced by `JayDeBeAPI` and `sqlalchemy-jdbcapi`.
>
>   [JayDeBeAPI](https://pypi.org/project/JayDeBeApi/) by [Bastion Bowe](https://github.com/baztian)
>
>   [sqlalchemy-jdbcapi](https://pypi.org/project/sqlalchemy-jdbcapi/) by [Danesh Patel](https://github.com/daneshpatel) 

## Install
Install using the PyPi Repository:
```
pip install sqlalchemy-jdbc-generic
```

### Install from Source

1. Clone repository
   ```
    git clone https://github.com/bwadle/sqlalchemy-jdbc-generic
   ```
2. Navigate to cloned directory
   ```
    cd sqlalchemy-jdbc-generic
   ```
3. Upgrade PyPA build and build wheel
    ```
    python -m pip install --upgrade build
    python -m build -w
    ```
4. pip install from built wheel file
    ```
    python -m pip install --find-links=dist sqlalchemy-jdbc-generic
    ``` 

## Usage

Simple example of connecting to an sqlite local db file when an applicable SQLite JDBC jar file is available in your system path.
> See [JVM Options](#jvm-options) section for instructions on how to ensure your JDBC jar files are accessible.

To connect to an SQLite database file where the jdbc connection string is `jdbc:sqlite://local.db` :

```python
from sqlalchemy import create_engine

# engine connection string provided directly to the create_engine method.
eng = create_engine(
    'sqlajdbc://local.db?_class=org.sqlite.JDBC&_driver=sqlite'
    )

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
    
```

Alternatively, you can use the SQLAlchemy `URL.create()` method instead of an engine connection string:

> This approach is recommended and will be used for the remainder of this documentation.  You can still opt to create your engines using engine connection strings but they can get quite long and hard to read in most cases.

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

# engine connection URL created using URL.create method
eng_url = URL.create(
    drivername='sqlajdbc',
    host='local.db',
    query={
        '_class': 'org.sqlite.JDBC',
        '_driver': 'sqlite'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

## Arguments

> All arguments consumed by the *sqlajdbc* dialect are prefaced with an underscore (`_`) to ensure differentiation from any JDBC Driver parameter options.

The *sqlajdbc* dialect requires the **JDBC class** (`_class`) and **JDBC driver name** (`_driver`) be passed in the *query* section of the engine URL.

Other arguments specific to the _sqlajdbc_ dialect can be passed to change the behavior of how the engine connection options are interpreted and are described below:

> The examples in the below table are taken from an example connection to a Snowflake Database using the Snowflake JDBC Driver.  
> 
>   `jdbc:snowflake://mysnow.snowflakecomputing.com/?db=mydb`
> 
> A reference to that driver's documentation can be found at the following link:
>   [Snowflake JDBC Driver Documentation](https://docs.snowflake.com/developer-guide/jdbc/jdbc)

|argument|description|example|
|--------|-----------|-------|
|`_class`|The **Java Class** of the JDBC driver to use|net.snowflake.client.jdbc.SnowflakeDriver|
|`_driver`|The **driver name** to be placed between `jdbc:` and `://` in the jdbc connection string. `jdbc:<driver>://`| snowflake |
|`_jars`| path(s) to the **jar files** for JDBC driver given as a string or string representation of a list of paths | see [Where to Place Jar Files](#where-to-place-jdbc-jar-files) section|
|`_jvmpath`| path to the **Java Virtual Machine** driver (`jvm.so`, `jvm.dll`) to be used instead of the default JVM within the path pointed to by the `JAVA_HOME` os environment variable. | `/path/to/jvm.so` |
|`_jvmargs`| **JVM arguments** be be passed to `jpype.startJVM()`| see [jpype JVM Functions Documentation](https://jpype.readthedocs.io/en/latest/api.html#jpype.startJVM)

### Query Arguments
The default behavior is to assume query parameters are separated from the host url by a question mark (`?`) and each parameter name-value pair is separated by ampersands (`&`) with an equal sign (`=`) used to separate the name and value for each.

`jdbc:driver://host`__`?`__`name`**`=`**`value`__`&`__`name`__`=`__`value`__`&`__`...`

This is the most typical pattern found across the various JDBC Driver implementations.  However, there are some drivers that deviate from this convention.  One such example is the [Teradata JDBC Driver](https://teradata-docs.s3.amazonaws.com/doc/connectivity/jdbc/reference/current/frameset.html) which uses the forwardslash character (`/`) to denote the start of the query parameters and a comma (`,`) to separate each parameter **name-value** pair.

`jdbc:teradata://host`**`/`**`name=value`**`,`**`name=value`**`,`**`...`

SQLAlchemy translates and converts each parameter into a python collection and then builds back the query parts which will ultimately be used to construct the JDBC Connection String.  

In order to provide the Teradata JDBC Driver with the connection string format that it expects we need to tell SQLAlchemy to **use alternative symbols** when reconstructing the **query string**.  These options are described below:

|argument|description|default|
|--------|-----------|-------|
|`_start`|The charactor used to denote the **start** of the url query string| `?`|
|`_end`| The charactor used to denote the **end** of the url query string| None|
|`_assoc`| The charactor used to **associate** a parameter name with a parameter value| `=`|
|`_sep`| The charactor used to **separate** parameter name-value pairs| `&`|

The Teradata JDBC connection string differs from default JDBC connection sting behavior for the starting charactor (`_start`) and separation charactor (`_sep`).  We would need to provide the **alternative charactors** to use in the SQLAlchemy engine connection string query pattern as follows:

```python
eng = create_engine('sqlajdbc://host?_start=/&_sep=,...')
```
*Alternatively*, you can use the __URL.create__ method as follows:
```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_start': '/',
        '_sep': ',',
        ...
    }
)

eng = create_engine(eng_url)
```
> You would also have to provide the JDBC class name and JDBC driver name with the `_class` and `_driver` properties but those have been omitted for brevity above.
> The full SQLAlchemy Engine Connection String would be as follows:
> `sqlajdbc://host?_start=/&_sep=,&_driver=teradata&_class=com.teradata.jdbc.TeraDriver`

## JVM Options
JDBC Drivers leverage the Java programming language to setup and expose DBAPI patterns that allow SQLAlchemy to "_do it's magic_".  

Much like Python, Java leverages a runtime environment when executing actual code instructions and code written in one version of Java may not be compatible with all runtime environments.

In my testing and everyday use I have found that most JDBC drivers work just fine using JAVA 8 however I have ran into a few that require a newer version -- such as JAVA 11.

### Where to place JDBC files
> The topic of how the JAVA JVM finds classes and libraries is much larger than I am willing to document here.  While there are surely other ways to organize and access your `.jar` files, I have only ever needed to use one of the three described below. 

You can place your JDBC jar files in a location:
* same as the working directory of the python script being executed with filename(s) defined in `_jar` argument.
* anywhere with an **implicit** filepath(s) defined in `_jar` argument.
* defined in your **System Path** environment variable with no `_jar` argument required.

#### Working Directory
When the JDBC jar driver file(s) are within the same directory as the `.py` file which sets up the SQLAlchemy Engine you only need to provide the filename of the `.jar` file(s) with the `_jars` argument.

```
.
└── myProject/
    ├── myScript.py
    └── some-jdbc-driver.0.0.0.jar
```

```python
# myScript.py

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_class': 'org.somedb.jdbc.driver',
        '_driver': 'somedb',
        '_jars': 'some-jdbc-driver.0.0.0.jar',
        ...
    }
)
```

If you instead want to place your jar files in another directory that can be easily defined by a relative path from your `.py` file you can use relative file names for the `.jar` file(s)

```
.
└── myProject/
    ├── myScript.py
    └── jdbc/
        └── some-jdbc-driver.0.0.0.jar
```

```python
# myScript.py

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_class': 'org.somedb.jdbc.driver',
        '_driver': 'somedb',
        '_jars': 'jdbc/some-jdbc-driver.0.0.0.jar',
        ...
    }
)
```

#### Implicit Directory
When your jar files are somewhere entirely separate from your project or script folder you should refer the the required JDBC jar files with full paths.

```
.
├── .../
│   └── myScript.py
├── ...
├── ...
└── usr/
    └── assets/
        └── jdbc/
            └── some-jdbc-driver.0.0.0.jar
```

```python
# myScript.py

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_class': 'org.somedb.jdbc.driver',
        '_driver': 'somedb',
        '_jars': '/usr/assets/jdbc/somedb-jdbc-driver.0.0.0.jar',
        ...
    }
)
```

#### System Path
If you place your jar files in a directory that is defined in your system's `PATH` environment variable then it is not required to supply a `_jars` argument as those `.jar` files will be included when the JVM attempts to retrive the class provided with the `_class` arguement.

> On Windows OS you can check for jar files on a system path location by running the following command:
>
> `C:> where *.jar`

If your JDBC `.jar` file(s) are accessible on the System Path then you only need to define the `_class` and `_driver` arguements:

```python
# myScript.py

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_class': 'org.somedb.jdbc.driver',
        '_driver': 'somedb',
        ...
    }
)
```

### `_jvmpath`

Your environment default Java Runtime Environment uses the OS Environment Variable named `JAVA_HOME` to point to the root folder for your JRE.  If you want to use an alternative version of JAVA or if `JAVA_HOME` is not defined you can use the `_jvmpath` connection string argument to provide the path to the desired JVM driver file.

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_jvmpath': '/path/to/jvm.dll',
        ...
    }
)

eng = create_engine(eng_url)
```

### `_jvmargs`

In the case of one JDBC driver tested, not only was a different version of Java required but a specific command line argument needed to be supplied to the JVM start arguments.  Fortunately, the Java error that occured happened within a class that provided exceptionally good error descriptions.

> ``` 
> java.lang.RuntimeException: java.lang.RuntimeException: Failed to initialize MemoryUtil. Was Java started with `--add-opens=java.base/java.nio=ALL-UNNAMED`? (See https://arrow.apache.org/docs/java/install.html)
> ```

To fix this we can supply the JVM Argument suggested in the above error to the `_jvmargs` url connection string query argument as follows:

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_jvmpath': '/path/to/jvm.dll',
        '_jvmargs': '--add-opens=java.base/java.nio=ALL-UNNAMED',
        ...
    }
)

eng = create_engine(eng_url)
```

## Database Flavor Examples
This section shows some example patterns for connection to different database versions.  All database hosts, usernames and passwords are either omitted or ficticious -- for obvious reasons.

> In all of the below patterns I am implicitly referring to the JDBC Driver jar file(s) (`'_jars': '*.jar'`) I used in testing and providing links to the source from which they were obtained in the notes at the beginning of each section.  
> 
> Normally I would place these jar files in a directory defined within my OS Level `PATH` environment variable.  However, in these examples we assume that the jar files exist in the same directory as the python file being executed.
> 
> I have also obsfucated any release versioning within the filename of each jar with `#` charactors as versions and releases of these files will no doubt change over time.

### SQLite
> SQLAlchemy supports SQLite natively so there may be no legitimate reason to leverage the SQLite JDBC driver over the native SQLite dialect but you could if you wanted to.
>
>   __DRIVER__: https://github.com/xerial/sqlite-jdbc#download
>
>   __DOCUMENTATION__: https://github.com/xerial/sqlite-jdbc#sqlite-jdbc-driver

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='local.db',
    query={
        '_class': 'org.sqlite.JDBC',
        '_driver': 'sqlite',
        '_jars': 'sqlite-jdbc-#.##.#.#.jar'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

### MySQL
> SQLAlchemy supports MySQL natively so there may be no legitimate reason to leverage the MySQL JDBC driver over the native MySQL dialect but you could if you wanted to.
> 
>   __DRIVER__: https://dev.mysql.com/downloads/connector/j/
>
>   __DOCUMENTATION__: https://dev.mysql.com/doc/connector-j/8.0/en/

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='myMySQLDB.myServer.com',
    username='myUsername',
    password='myFakePa$$w0rd',
    port=3306,
    query={
        '_class': 'com.mysql.cj.jdbc.Driver',
        '_driver': 'mysql',
        '_jars': 'mysql-connector-j-#.#.##.jar'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT current_date').fetchall()
    print(res)
```

### MariaDB
>   __DRIVER__: https://mariadb.org/connector-java/all-releases/
>
>   __DOCUMENTATION__: https://mariadb.com/kb/en/about-mariadb-connector-j/

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='myMariaDB.myServer.com',
    username='myUsername',
    password='myFakePa$$w0rd',
    port=3306,
    query={
        '_class': 'org.mariadb.jdbc.Driver',
        '_driver': 'mariadb',
        '_jars': 'mariadb-java-client-#.#.#.jar'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT current_date').fetchall()
    print(res)
```

### Snowflake
> There is an officially supported SQLAlchemy Dialect for Snowflake which would support far more DBAPI functionality than leveraging this module and the Snowflake JDBC driver.  Unless you have a specific reason to leverage the Snowflake JDBC driver I would recommend using the following dialect instead:
> 
> `snowflake-sqlalchemy` 
> 
> **Snowflake SQLAlchemy Documentation** → https://docs.snowflake.com/developer-guide/python-connector/sqlalchemy

> The Snowflake jdbc pattern for passing the user password in the query needs to be URL encoded in order to be passed properly.  In this pattern I opted to use quote_plus from the urllib module. 
> 
>   __DRIVER__: https://docs.snowflake.com/en/developer-guide/jdbc/jdbc-download
>
>   __DOCUMENTATION__: https://docs.snowflake.com/en/developer-guide/jdbc/jdbc-configure

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from urllib.parse import quote_plus

eng_url = URL.create(
    drivername='sqlajdbc',
    host='my-snowflake-account.snowflakecomputing.com',
    query={
        '_class': 'net.snowflake.client.jdbc.SnowflakeDriver',
        '_driver': 'snowflake',
        '_jars': 'snowflake-jdbc-#.##.#.jar',
        'user': 'myUsername',
        'password': quote_plus('myFakePa$$w0rd'),
        'db': 'MY_SNOW_DB',
        'role': 'MY_SNOW_ROLENAME',
        'schema': 'MY_SNOW_SCHEMA',
        'warehouse': 'MY_SNOW_WAREHOUSE'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

### Teradata
> There is an officially supported SQLAlchemy dialect for Teradata which would support far more DBAPI functionality than leveraging this module and the Teradata JDBC driver.  Unless you have a specific reason to leverage the Teradata JDBC driver I would recommend using the following dialect instead:
> 
> `teradatasqlalchemy` 
>
> **Teradata SQLAlchemy Documentation** → https://pypi.org/project/teradatasqlalchemy/

>The Teradata jdbc connection string query pattern deviates from popular convention with both the start and separator charactors.  These would need to be defined with the `_start` and `_sep` query arguments as shown in the below pattern.
>
>   __DRIVER__: https://downloads.teradata.com/download/connectivity/jdbc-driver
>
>   __DOCUMENTATION__: https://teradata-docs.s3.amazonaws.com/doc/connectivity/jdbc/reference/current/frameset.html

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='myTeradataDB.myServer.com',
    query={
        '_class': 'com.teradata.jdbc.TeraDriver',
        '_driver': 'teradata',
        '_jars': 'terajdbc-##.##.##.##.jar',
        '_start': '/',
        '_sep': ',',
        'DBS_PORT': '1025',
        'user': 'myUsername',
        'password': 'myFakePa$$w0rd'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT current_date').fetchall()
    print(res)
```

### Vertica
> There is an officially supported SQLAlchemy dialect for Vertica which would support far more DBAPI functionality than leveraging this module and the Vertica JDBC driver.  Unless you have a specific reason to leverage the Vertica JDBC driver I would recommend using the following dialect instead:
> 
> `vertica-sqlalchemy-dialect` 
>
> **Vertica SQLAlchemy Documentation** → https://github.com/vertica/vertica-sqlalchemy-dialect

>The vertica jdbc pattern for passing the user password in the query needs to be URL encoded in order to be passed properly.  In this pattern I opted to use quote_plus from the urllib module. 
>
>   __DRIVER__: https://www.vertica.com/download/vertica/client-drivers/
>
>   __DOCUMENTATION__: https://www.vertica.com/docs/11.0.x/HTML/Content/Authoring/ConnectingToVertica/ClientJDBC/JDBCConnectionProperties.htm

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from urllib.parse import quote_plus

eng_url = URL.create(
    drivername='sqlajdbc',
    host='myVerticaDB.myServer.com',
    port=5433,
    query={
        '_class': 'com.vertica.jdbc.Driver',
        '_driver': 'vertica',
        '_jars': 'vertica-jdbc-##.#.#-#.jar',
        'user': 'myUsername',
        'password': quote_plus('myFakePa$$w0rd')
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

### Palantir Foundry
>The Palantir Foundry JDBC connector requires a JAVA 11 JVM and a specific argument be passed to the JVM in order for one of the leveraged Java classes to operate as intended.  If your default JVM is lower than version 11 you will need to specify an alternate jvm using `_jvmpath`.
>
>   __DRIVER__: https://www.palantir.com/docs/foundry/analytics-connectivity/downloads/
>
>   __DOCUMENTATION__: https://www.palantir.com/docs/foundry/analytics-connectivity/odbc-jdbc-drivers/#jdbc-1

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='myDomain.palantirfoundry.com',
    query={
        '_class': 'com.palantir.foundry.sql.jdbc.FoundryJdbcDriver',
        '_driver': 'foundrysql',
        '_jars': 'foundry-sql-jdbc-driver-#.#.#-withdep.jar',
        '_jvmpath': '/path/to/Java/11/jvm.dll'
        '_jvmargs': '--add-opens=java.base/java.nio=ALL-UNNAMED'
        'password': '<token-guid-goes-here>'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

### Oracle
> SQLAlchemy supports Oracle natively so there may be no legitimate reason to leverage the Oracle JDBC driver over the native dialect but you could if you wanted to.
>
> Should work as-is but there may be some idiocyncracies to identify in the JDBC pattern for Oracle Service Names and SIDs.
>
> Will verify in future updates.

### Microsoft SQL Server
> SQLAlchemy supports MSSQL natively so there may be no legitimate reason to leverage the MSSQL JDBC driver over the native dialect but you could if you wanted to.
>
> Should work as-is but the MSSQL JDBC query pattern uses semi-colons as both the start and separator charactor.
>
> Will verify in future updates.

### PostgreSQL
> SQLAlchemy supports PostgreSQL natively so there may be no legitimate reason to leverage the PostgreSQL JDBC driver over the native dialect but you could if you wanted to.

### MongoDB
> Untested

### Redis
> Untested

### IBM DB2
> Untested

### Elasticsearch
> Untested

### Microsoft Access
> Untested