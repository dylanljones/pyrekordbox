# Rekordbox 6 Database

Pyrekordbox uses [SQLALchemy](https://www.sqlalchemy.org/) as ORM-Framework to handle the
Rekordbox v6 database file (``master.db``). The table declarations can be found in
``pyrekordbox.db6.tables``.

```{seealso}
See the {ref}`Rekordbox 6 Database Format <Rekordbox 6 Database Format>` documentation for more information.
```

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

```{note}
More coming soon!
```

### Incompatible Rekordbox versions

If you are using Rekorbox v6.6.5 or later and have no cached key from a previous
Rekordbox version, the database can not be unlocked automatically.
In this case you have to provide the key manually until a patch fixing this issue is released:
````python
from pyrekordbox import Rekordbox6Database

db = Rekordbox6Database(key="<insert key here>")
````

The key can be found in some other projects (see issue
[#77](https://github.com/dylanljones/pyrekordbox/issues/77)), for example [here][rb6-key].

Alternatively you can update the cache file of the Rekordbox database key
manually. Once the key is cached the database can be opened without providing the key:
````python
from pyrekordbox.config import write_db6_key_cache
from pyrekordbox import Rekordbox6Database

write_db6_key_cache("<insert key here>")  # call once
db = Rekordbox6Database()
````
The command line interface of ``pyrekordbox`` also
provides a command for downloading the key from known sources and writing it to the
cache file:
````shell
python -m pyrekordbox download-key
````



[rb6-key]: https://github.com/mganss/CueGen/blob/19878e6eb3f586dee0eb3eb4f2ce3ef18309de9d/CueGen/Generator.cs#L31
