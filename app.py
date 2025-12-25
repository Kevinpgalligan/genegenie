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

def get_people():
    global people
    return people

def load_db_data(path: Path):
    global people

    state = DbState()
    # Hardcoded to sqlite, but in earlier versions of Gramps this
    # could be bsddb (or something). The database ID should be in
    # a text file in the tree's grampsdb folder.
    state.change_database(make_database("sqlite"))
    def dummy_callback(v): pass
    state.db.load(path, dummy_callback, "r")

    people = sorted(load_people(state.db),
                    key=lambda person: person.listing_name)
    print("Loaded", len(people), "people")

    state.get_database().close()

def load_people(gramps_db):
    gramps_persons = [
        Person(person_data) 
        for handle, person_data
        in gramps_db.get_person_cursor()]
    print(gramps_persons[0].birth_ref_index)
    print(gramps_persons[0].death_ref_index)
    print(gramps_persons[0].event_ref_list)
    print(vars(gramps_persons[0].event_ref_list[0]))
    ev = gramps_db.get_event_from_handle(gramps_persons[0].event_ref_list[0].ref)
    print("Event stuff:", ev.type, type(ev.type), repr(str(ev.type)))
    print("Event date:", ev.date, type(ev.date))
    print("Date vars:", vars(ev.date))
    
    print("ALL THE DATES:")
    for perp in gramps_persons:
        if perp.event_ref_list:
            ev = gramps_db.get_event_from_handle(perp.event_ref_list[0].ref)
            # Need to figure out how to turn the modifier from a number into something understandable.
            # Useful comment from Gramps codebase...
            #   "ui_mods taken from date.py def lookup_modifier(self, modifier):"
            # And then, in date.py, the following code...
            #   "elif self.date1.get_modifier() == Date.MOD_ABOUT:"
            print("   ", vars(ev.date), ev.date.modifier)

    return [PersonInfo(extract_display_name(person),
                       person.get_primary_name().get_name(),
                       person.get_gramps_id())
            for person in gramps_persons]

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
        load_db_data(dbpath)
        print("Loaded Gramps data from", dbpath)
    else:
        global people
        people = [PersonInfo("display1", "listing1", "I001"),
                  PersonInfo("display2", "listing2", "I002")]

    #app.run(port=8000)

if __name__ == "__main__":
    main()
