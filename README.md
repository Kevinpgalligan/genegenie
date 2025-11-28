## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Fix flaky close.
```
^CTraceback (most recent call last):
  File "/home/kg/proj/genegenie/app.py", line 82, in <module>
    app.run(port=8000)
  File "/home/kg/proj/genegenie/app.py", line 79, in main
    sys.exit(1)
  File "/home/kg/proj/genegenie/app.py", line 52, in close_db
    state.get_database().close()
  File "/usr/lib/python3/dist-packages/gramps/gen/db/generic.py", line 739, in close
    self._close()
  File "/usr/lib/python3/dist-packages/gramps/plugins/db/dbapi/dbapi.py", line 199, in _close
    self.dbapi.close()
  File "/usr/lib/python3/dist-packages/gramps/plugins/db/dbapi/sqlite.py", line 190, in close
    self.__connection.close()
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 139822815704640 and this is thread id 139822887157760.
```
* Bigger text, higher contrast link colour.
* More columns in People page, e.g. birth date, death date, ... (check Gramps's People tab).
* Fill out the Person page.
* Sources page? Events page? Tree browser?
* Aesthetic polishing.
