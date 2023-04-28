# sqlalchemy-jdbc-generic
Generic JDBC dialect for SQLAlchemy.

The overall purpose of this dialect is to allow -- _at a minimum_ -- conectivity and consumer query access to any database with an available JDBC driver.

The genesis of this codebase was heavily influenced by `JayDeBeAPI` and `sqlalchemy-jdbcapi`.

> [JayDeBeAPI](https://pypi.org/project/JayDeBeApi/) by [Bastion Bowe](https://github.com/baztian)

> [sqlalchemy-jdbcapi](https://pypi.org/project/sqlalchemy-jdbcapi/) by [Danesh Patel](https://github.com/daneshpatel) 

## Install

Install using pip:

```
pip install sqlalchemy-jdbc-generic
```

## Usage

Simple example of connecting to an sqlite local db file when an applicable SQLite JDBC jar file is available in your system path.

```python

from sqlalchemy import create_engine

eng = create_engine(
    'sqlajdbc://local.db?jclass=org.sqlite.JDBC&jdriver=sqlite'
    )

with eng.connect() as c:
    res = c.execute('SELECT CURRENT_DATE').fetchall()
    print(res)
    
```