import argparse
from pathlib import Path
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from flask import Flask, render_template
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person
from gramps.gen.db.utils import make_database
from gramps.gen.lib.date import Date

class Gender(Enum):
    MALE = 1
    FEMALE = 2
    OTHER = 2

@dataclass
class PersonInfo:
    display_name: str
    listing_name: str
    gramps_id: str
    birth_date: Optional[Date]
    death_date: Optional[Date]
    gender: Gender

def format_date(d: Optional[Date]):
    if d is None:
        return "-"
    # We don't account for all modifier types here. E.g. no spans, only
    # ranges. I think spans are supposed to represent the gap between
    # two dates, which we would never use for our purposes, e.g. birthdays.
    assert d.modifier != Date.MOD_SPAN
    if d.modifier == Date.MOD_TEXTONLY:
        return str(d)
    if d.modifier == Date.MOD_RANGE:
        start = format_date_tuple(d.get_start_date())
        stop = format_date_tuple(d.get_stop_date())
        return f"{start} - {stop}"

    prefix = ""
    if d.modifier == Date.MOD_AFTER:
        prefix = ">"
    elif d.modifier == Date.MOD_BEFORE:
        prefix = "<"
    elif d.modifier == Date.MOD_ABOUT:
        prefix = "~"

    return format_ymd(d.get_year(), d.get_month(), d.get_day(), prefix)

def format_date_tuple(tup: Tuple) -> str:
    # I'm not sure what the last thing in the tuple means, tbh.
    # From the Gramps codebase, Date.get_start_date():
    """
    If the date is a compound date (range or a span), it is the first part
    of the compound date. If the date is a text string, a tuple of
    (0, 0, 0, False) is returned. Otherwise, a date of (DD, MM, YY, slash)
    is returned. If slash is True, then the date is in the form of 1530/1.
    """
    d, m, y, _ = tup
    return format_ymd(y, m, d, "")

def format_ymd(year: int, month: int, day: int, prefix: Optional[str]) -> str:
    if year == 0:
        return "-"
    elif month == 0:
        return f"{prefix}{year}"
    elif day == 0:
        return f"{prefix}{year}/{month}"
    return f"{prefix}{year}/{month}/{day}"
    

def format_gender(g: Gender):
    if g == Gender.MALE:
        return "♂️"
    if g == Gender.FEMALE:
        return "♀️"
    return "?"

app = Flask(__name__)
app.jinja_env.globals.update(
    format_date=format_date,
    format_gender=format_gender)

people = None

def get_people():
    global people
    return people

def load_db_data(path: Path):
    global people

    state = DbState()
    # Hardcoded to sqlite, but in earlier versions of Gramps this
    # could be bsddb (or something). If needed, the database ID is
    # saved in a text file in the tree's grampsdb folder.
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

    """
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
            print("   ", vars(ev.date))
            print("   ", str(ev.date))
    """

    return [make_person_info(person, gramps_db)
            for person in gramps_persons]

def make_person_info(person, gramps_db):
    birth_date = get_event_date(person, person.birth_ref_index, gramps_db)
    death_date = get_event_date(person, person.death_ref_index, gramps_db)
    return PersonInfo(extract_display_name(person),
                      person.get_primary_name().get_name(),
                      person.get_gramps_id(),
                      birth_date,
                      death_date,
                      extract_gender(person))

def extract_gender(person):
    g = person.get_gender()
    if g == Person.MALE:
        return Gender.MALE
    if g == Person.FEMALE:
        return Gender.FEMALE
    return Gender.OTHER

def get_event_date(person, index, gramps_db):
    if index < 0:
        return None
    event = gramps_db.get_event_from_handle(person.event_ref_list[index].ref)
    return event.date

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
        people = [PersonInfo("display1", "listing1", "I001", None, None, Gender.MALE),
                  PersonInfo("display2", "listing2", "I002", None, None, Gender.FEMALE)]

    app.run(port=8000)

if __name__ == "__main__":
    main()
