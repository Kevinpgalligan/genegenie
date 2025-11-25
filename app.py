import argparse
from pathlib import Path
import sys

from flask import Flask
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person
from gramps.gen.db.utils import make_database

# TODO:
# Implement the various pages.
#   a) /person/<id>
#   b) /people.html   [list of all people]
#   etc.

app = Flask(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dbpath", type=str)

    args = parser.parse_args()
    dbpath = Path(args.dbpath)

    if not dbpath.exists():
        print("Invalid path to grampsdb:", dbpath, file=sys.stderr)
        sys.exit(1)
    
    state = DbState()
    state.change_database(make_database("sqlite"))
    def dummy_callback(v): pass
    state.db.load(args.dbpath, dummy_callback, "r")

    for i, (handle, person_data) in enumerate(state.db.get_person_cursor()):
        person = Person(person_data)
        name = person.get_primary_name()
        print(i, name.get_name())

    state.get_database().close()

    #app.run(port=8000)

if __name__ == "__main__":
    main()
