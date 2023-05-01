# sqlalchemy-jdbc-generic
Generic JDBC dialect for SQLAlchemy.

The overall purpose of this dialect is to allow -- _at a minimum_ -- conectivity and consumer query access to any database with an available JDBC driver.

The genesis of this codebase was heavily influenced by `JayDeBeAPI` and `sqlalchemy-jdbcapi`.

> [JayDeBeAPI](https://pypi.org/project/JayDeBeApi/) by [Bastion Bowe](https://github.com/baztian)

> [sqlalchemy-jdbcapi](https://pypi.org/project/sqlalchemy-jdbcapi/) by [Danesh Patel](https://github.com/daneshpatel) 

## Install

Build and install using `pip` and `setuptools`:

1. Clone repository
2. Navigate to cloned directory
3. Build wheel
    ```
    python -m build -w
    ```
4. pip install from built wheel file
    ```
    python -m pip install --find-links=dist sqlalchemy-jdbc-generic
    ```
> codebase has not yet been submitted to pypi.  This will happen in future releases.
>    ```
>    pip install sqlalchemy-jdbc-generic
>    ```

## Usage

Simple example of connecting to an sqlite local db file when an applicable SQLite JDBC jar file is available in your system path.
> See [JVM Options](#jvm-options) section for instructions on how to ensure your JDBC jar files are accessible.

To connect to an SQLite database file where the jdbc connection string is: `jdbc:sqlite://local.db` :

```python
from sqlalchemy import create_engine

eng = create_engine(
    'sqlajdbc://local.db?_class=org.sqlite.JDBC&_driver=sqlite'
    )

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
    
```

Alternatively, you can use the SQLAlchemy `URL.create()` method instead of an engine URL string:

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    host='local.db',
    query={
        '_class':'org.sqlite.JDBC',
        '_driver':'sqlite'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

## Arguments

> All arguments consumed by `sqlajdbc` are prefaced with an underscore (`_`) to ensure compatability and differentiation from any JDBC Driver argument that may be leveraged by the actual JDBC Driver being used.

The `sqlajdbc` dialect requires the jdbc class (`_class`) and drivername (`_driver`) be passed in the query section of the engine URL.

Other arguments specific to `sqlajdbc` can be passed to change the behavior of how your engine connection string is interpreted and are described below:

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
|`_jars`| path(s) to the **jar files** for JDBC driver given as a string or string representation of a list of paths | `/path/to/driver.jar` or `[/path/to/driver1.jar,/path/to/driver2.jar,...]`|
|`_libs`| path(s) which contain jar files for the JDBC driver | `/path/to/myDrivers/` |
|`_jvmpath`| path to the **Java Virtual Machine** driver (`jvm.so`, `jvm.dll`) to be used instead of the default JVM within the path pointed to by the `JAVA_HOME` os environment variable. | `/path/to/jvm.so` |
|`_jvmargs`| **JVM arguments** be be passed to `jpype.startJVM()`| see [jpype JVM Functions Documentation](https://jpype.readthedocs.io/en/latest/api.html#jpype.startJVM)

### Query Arguments
The default behavior is to assume query parameters are separated from the host url by a question mark (`?`) and each parameter name and value are separated by ampersands (`&`) with an equal sign (`=`) used to separate the name and value for each parameter pair.

`jdbc:driver://host`__`?`__`name`**`=`**`value`__`&`__`name`__`=`__`value`__`&`__`...`

This is the most typical pattern found across the various JDBC Driver implementations.  However, there are some drivers that deviate from this convention.  One such example is the [Teradata JDBC Driver](https://teradata-docs.s3.amazonaws.com/doc/connectivity/jdbc/reference/current/frameset.html) which uses the forwardslash character (`/`) to denote the start of the query parameters and a comma (`,`) to separate each parameter **name-value** pair.

`jdbc:teradata://host`**`/`**`name=value`**`,`**`name=value`**`,`**`...`

SQLAlchemy translates and converts each parameter into a python collection and then builds back the query from its parameter parts which will ultimately be used to construct the JDBC Connection String.  In order to provide the Teradata JDBC Driver with the connection string format that it expects we need to tell SQLAlchemy to **use alternative symbols** when reconstructing the **query string**.  These options are described below:

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
JDBC Drivers leverage the Java programming language to setup and expose DBAPI patterns that allow SQLAlchemy to "_do its thing_".  

Much like Python, Java leverages a runtime environment when executing actual code instructions and code written in one version of Java may not be compatible with all runtime environments.

In my testing and everyday use I have found that most JDBC drivers work just fine using JAVA 8 however I have ran into a few that require a newer version -- such as JAVA 11.

### `_jvmpath`

Your environment default Java Runtime Environment uses the OS Environment Variable named `JAVA_HOME` to point to the root folder for your JRE.  If you want to use an alternative version of JAVA or if `JAVA_HOME` is not defined you can use the `_jvmpath` connection string argument to provide the path to the desired JVM driver file.

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

eng_url = URL.create(
    drivername='sqlajdbc',
    ...
    query={
        '_jvmpath':'/path/to/jvm.dll',
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
        '_jvmpath':'/path/to/jvm.dll',
        '_jvmargs':'--add-opens=java.base/java.nio=ALL-UNNAMED',
        ...
    }
)

eng = create_engine(eng_url)
```

## Database Flavor Examples
This section shows some example patterns for connection to different database versions.  All database hosts, usernames and passwords are either omitted or ficticious -- for obvious reasons.

> In all of the below patterns I am implicitly referring to the JDBC Driver jar file(s) -- `'_jars': '*.jar'` -- I used in testing and providing links to the source from which they were obtained in the notes at the beginning of each section.  
> Normally I would place these jar files in a directory defined within my OS Level `PATH` environment variable.  However, in these examples we assume that the jar files exist in the same directory as the python file being executed.

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
        '_class':'org.sqlite.JDBC',
        '_driver':'sqlite',
        '_jars': 'sqlite-jdbc-3.41.2.1.jar'
    }
)

eng = create_engine(eng_url)

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
```

### Oracle
> SQLAlchemy supports Oracle natively so there may be no legitimate reason to leverage the Oracle JDBC driver over the native oracle dialect but you could if you wanted to.


### MySQL
> Tested -- Documentation Pending

### MariaDB
> Tested -- Documentation Pending

### Microsoft SQL Server
> Testing

### PostgreSQL
> Testing

### MongoDB
> Testing

### Redis
> Testing

### IBM DB2
> Testing

### Elasticsearch
> Testing

### Microsoft Access
> Testing

### Snowflake
> Tested -- Documentation Pending

### Cassandra
> Testing

### Databricks
> Testing

### Teradata
> Tested -- Documentation Pending

### Microsoft Azure SQL Database
> Testing

### Vertica
> Testing

### Palantir Foundry
> Tested -- Documentation Pending