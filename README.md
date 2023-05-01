[[_TOC_]]

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
|`_class`|The Java Class of the JDBC driver to use|net.snowflake.client.jdbc.SnowflakeDriver|
|`_driver`|The driver name to be placed between `jdbc:` and `://` in the jdbc connection string. `jdbc:<driver>://`| snowflake |
|`_jars`| path(s) to the jar files for JDBC driver given as a string or string representation of a list of paths | `/path/to/driver.jar` or `[/path/to/driver1.jar,/path/to/driver2.jar,...]`|
|`_libs`| path(s) which contain jar files for the JDBC driver | `/path/to/myDrivers/` |
|`_jvmpath`| path to the Java Virtual Machine (`jvm.so`, `jvm.dll`) to be used instead of the default JVM within the path pointed to by the `JAVA_HOME` os environment variable. | `/path/to/jvm.so` |
|`_jvmargs`| arguments be be passed to `jpype.startJVM()`| see [jpype JVM Functions Documentation](https://jpype.readthedocs.io/en/latest/api.html#jpype.startJVM)

### Query Arguments
The default behavior is to assume query parameters are separated from the host url by a question mark (`?`) and each parameter name and value are separated by ampersands (`&`) with an equal sign (`=`) used to separate the name and value for each parameter pair.

`jdbc:driver://host`__`?`__`name`**`=`**`value`__`&`__`name`__`=`__`value`__`&`__`...`

This is the most typical pattern found across the various JDBC Driver implementations.  However, there are some drivers that deviate from this convention.  One such example is the [Teradata JDBC Driver](https://teradata-docs.s3.amazonaws.com/doc/connectivity/jdbc/reference/current/frameset.html) which uses the forwardslash character (`/`) to denote the start of the query parameters and a comma (`,`) to separate each parameter `name=value` pair.

`jdbc:teradata://host`**`/`**`name=value`**`,`**`name=value`**`,`**`...`

SQLAlchemy translates and converts each parameter into a python collection and then builds back the query from its parameter parts which will ultimately be used to construct the JDBC Connection String.  In order to provide the Teradata JDBC Driver with the connection string format that it expects we need to tell SQLAlchemy to use alternative symbols when reconstructing the query string.  These options are described below:

|argument|description|default|
|--------|-----------|-------|
|`_start`|The charactor used to denote the start of the url query string| `?`|
|`_end`| The charactor used to denote the end of the url query string| None|
|`_assoc`| The charactor used to associate a parameter name with a parameter value| `=`|
|`_sep`| The charactor used to separate parameter name-value pairs| `&`|

The Teradata JDBC connection string differs from default JDBC connection sting behavior for the starting charactor (`_start`) and separation charactor (`_sep`).  We would need to provide the alternative charactors to use in the SQLAlchemy engine connection string as follows:

```
sqlajdbc://host?_start=/&_sep=,...
```

> You would also have to provide the JDBC class name and JDBC driver name with the `_class` and `_driver` properties but those have been omitted for brevity above.
> The full SQLAlchemy Engine Connection String would be as follows:
> `sqlajdbc://host?_start=/&_sep=,&_driver=teradata&_class=com.teradata.jdbc.TeraDriver`

## Database Flavor Examples