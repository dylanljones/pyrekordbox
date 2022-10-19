# Configuration

Pyrekordbox looks for installed Rekordbox versions and sets up the configuration
automatically. The configuration can be checked by calling:
````python
from pyrekordbox import show_config

show_config()
````

which, for example, will print
````
Pioneer:
   app_dir =      C:\Users\user\AppData\Roaming\Pioneer
   install_dir =  C:\Program Files\Pioneer
Rekordbox 5:
   app_dir =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox
   db_dir =       C:\Users\user\AppData\Roaming\Pioneer\rekordbox
   db_path =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox\datafile.edb
   install_dir =  C:\Program Files\Pioneer\rekordbox 5.8.6
   version =      5.8.6
Rekordbox 6:
   app_dir =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox6
   db_dir =       C:\Users\user\AppData\Roaming\Pioneer\rekordbox
   db_path =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox\master.db
   dp =           FJ9s0iA+hiPZg...
   install_dir =  C:\Program Files\Pioneer\rekordbox 6.5.3
   version =      6.5.3
````

If for some reason the configuration fails the values can be updated by providing the
paths to the directory where Pioneer applications are installed (`pioneer_install_dir`)
and to the directory where Pioneer stores the application data  (`pioneer_app_dir`)
````python
from pyrekordbox.config import update_config

update_config(pioneer_install_dir, pioneer_app_dir)
````

## Configuration files
Alternatively the two paths can be specified in a configuration file under the section
`rekordbox`. Supported configuration files are pyproject.toml, setup.cfg, rekordbox.toml,
rekordbox.cfg and rekordbox.yml.

**pyproject.toml** / **pyrekordbox.toml**
`````toml
[rekordbox]
pioneer-install-dir = "C:/Program Files/Pioneer"
pioneer-app-dir = "C:/Users/user/AppData/Roaming/Pioneer"
`````


**setup.cfg** / **pyrekordbox.cfg**
`````ini
[rekordbox]
pioneer-install-dir = C:/Program Files/Pioneer
pioneer-app-dir = C:/Users/user/AppData/Roaming/Pioneer
`````


**pyrekordbox.yml**
````yaml
rekordbox:
  pioneer-install-dir: C:/Program Files/Pioneer
  pioneer-app-dir: C:/Users/user/AppData/Roaming/Pioneer
````
