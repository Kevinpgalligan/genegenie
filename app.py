import argparse
from pathlib import Path
import sys
from dataclasses import dataclass

from flask import Flask, render_template
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person
from gramps.gen.db.utils import make_database

@dataclass
class PersonInfo:
    display_name: str
    listing_name: str
    gramps_id: str

app = Flask(__name__)

people = None
db_path = None
state = None
db_ready = False

def set_db_path(path: Path):
    global db_path
    db_path = path

def get_people():
    global people
    if people is None:
        people = sorted(load_people(),
                        key=lambda person: person.listing_name)
        print("Loaded", len(people), "people")
    return people

def extract_display_name(person):
    prim_name = person.get_primary_name()
    parts = []
    title = prim_name.get_title()
    if title:
        parts.append(title)
    parts.append(prim_name.get_first_name())
    nick = prim_name.get_nick_name()
    if nick:
        parts.append("\"")
        parts.append(nick)
        parts.append("\"")
    parts.append(prim_name.get_surname())
    return " ".join(parts)

def load_people():
    global state
    init_db()
    gramps_persons = [Person(person_data) 
        for handle, person_data
        in state.db.get_person_cursor()]
    return [PersonInfo(extract_display_name(person),
                       person.get_primary_name().get_name(),
                       person.get_gramps_id())
            for person in gramps_persons]

def init_db():
    global db_path, state, db_ready
    if not state:
        state = DbState()
    if not db_ready:
        state.change_database(make_database("sqlite"))
        def dummy_callback(v): pass
        state.db.load(db_path, dummy_callback, "r")
        db_ready = True
        print("Database loaded successfully from", db_path)
    
def close_db():
    global state
    if state and db_ready:
        state.get_database().close()

@app.route("/")
@app.route("/home.html")
def home_page():
    return render_template("home.html")

@app.route("/people.html")
def people_page():
    return render_template("people.html", people=get_people())

@app.route("/person/<person_id>.html")
def person_page(person_id):
    person = next((p
                   for p in get_people()
                   if p.gramps_id == person_id),
                  None)
    return render_template("person.html", person=person)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dbpath",
        type=str,
        required=False,
        help="path to Gramps database, e.g. ~/.gramps/grampsdb/<tree-id>")
    args = parser.parse_args()
    if args.dbpath:
        dbpath = Path(args.dbpath)
        if not dbpath.exists():
            print("Invalid path to grampsdb:", dbpath, file=sys.stderr)
            sys.exit(1)
        set_db_path(dbpath)

    app.run(port=8000)
    close_db()

if __name__ == "__main__":
    main()
