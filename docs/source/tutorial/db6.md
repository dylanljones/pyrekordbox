# Rekordbox 6 Database

Pyrekordbox uses [SQLALchemy](https://www.sqlalchemy.org/) as ORM-Framework to handle the
Rekordbox v6 database file (``master.db``). The table declarations can be found in
``pyrekordbox.db6.tables``.

Since the Rekordbox v6 database handler automatically finds the ``master.db`` database file
(see configuration), it can be initialized without any arguments:
````python
from pyrekordbox import Rekordbox6Database

db = Rekordbox6Database()
````

The class has simple getters for executing queries on all the tables, for example:

````python
from pyrekordbox.db6 import DjmdHistory

# Query specific entry in DjmDContent table
content = db.get_content(ID=0)

# Query and sort entries in DjmdHistory table
for history in db.get_history().order_by(DjmdHistory.DateCreated):
    print(history)
````

```{seealso}
See the {ref}`Rekordbox 6 Database Format <Rekordbox 6 Database Format>` documentation for more information.
```

```{note}
More coming soon!
```
