import argparse
from pathlib import Path
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List

from flask import Flask, render_template
# We reuse some types from the Gramps lib, like
# EventType and Date, but we create our own versions
# of others.
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person, EventType
from gramps.gen.db.utils import make_database
from gramps.gen.lib.date import Date

class Gender(Enum):
    MALE = 1
    FEMALE = 2
    OTHER = 2

class SourceType(Enum):
    # Someone's recollections, from talking to them.
    RECOLLECTIONS = 1
    # Primary source, e.g. birth cert.
    PRIMARY = 2
    # Another family tree or genealogical document.
    TREE = 3
    # Website or web database.
    WEB = 4
    # Only for mistakes.
    UNKNOWN = 5

def parse_source_type(name: str) -> SourceType:
    try:
        return SourceType[name.upper()]
    except:
        # Should only throw when it's an unknown source type. Ugly tho.
        return SourceType.UNKNOWN

@dataclass
class Source:
    title: str
    gramps_id: str
    description: str
    source_type: SourceType

class PageSources:
    def __init__(self):
        self.num = 1
        self.src_to_num = {}
        self.ordered_list = []

    def get_src_number(self, src: Source) -> int:
        if src.gramps_id not in self.src_to_num:
            self.src_to_num[src.gramps_id] = self.num
            self.num += 1
            self.ordered_list.append(src)
        return self.src_to_num[src.gramps_id]

@dataclass
class Event:
    gramps_id: str
    date: Optional[Date]
    description: str
    place: str
    event_type: EventType
    sources: List[Source]

@dataclass
class PersonInfo:
    display_name: str
    listing_name: str
    gramps_id: str
    birth: Optional[Event]
    death: Optional[Event]
    gender: Gender
    bio_sources: List[Source]

def format_event_date(event: Optional[Event], page_sources: Optional[PageSources] = None) -> str:
    """If page_sources supplied, then a citation will be added."""
    if not event or not event.date:
        return "-"
    s = format_date(event.date)
    if page_sources:
        return format_cite(s, event.sources, page_sources)
    return s

def format_cite(s: str, sources: List[Source], page_sources: PageSources) -> str:
    parts = [s]
    if not sources:
        parts.append("<sup class='citebad'>[citation needed]</sup>")
    else:
        for src in sources:
            parts.append(f"<sup class='{get_cite_class(src.source_type)}'>")
            parts.append(f"[{page_sources.get_src_number(src)}]")
            parts.append("</sup>")
    return "".join(parts)

def format_source(src: Source, page_sources: PageSources) -> str:
    parts = []
    parts.append(f"<span class='{get_cite_class(src.source_type)}'>[{page_sources.get_src_number(src)}]</span> ")
    parts.append(src.title)
    if src.description:
        parts.append(f" ({src.description})")
    return "".join(parts)

def get_cite_class(src_type: SourceType) -> str:
    if src_type in [SourceType.PRIMARY, SourceType.WEB]:
        return "citegood"
    elif src_type in [SourceType.RECOLLECTIONS, SourceType.TREE]:
        return "citeokay"
    return "citebad"

def format_date(d: Optional[Date]) -> str:
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
    format_event_date=format_event_date,
    format_cite=format_cite,
    format_gender=format_gender,
    format_source=format_source)

people = None
sources_map = {}

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

    return [make_person_info(person, gramps_db)
            for person in gramps_persons]

def make_person_info(person, gramps_db):
    return PersonInfo(extract_display_name(person),
                      person.get_primary_name().get_name(),
                      person.get_gramps_id(),
                      get_event(person, person.birth_ref_index, gramps_db),
                      get_event(person, person.death_ref_index, gramps_db),
                      extract_gender(person),
                      get_bio_sources(person, gramps_db))

def get_bio_sources(person, gramps_db) -> List[Source]:
    return get_sources_from_cites(person, gramps_db)

def make_source(src_obj, gramps_db) -> Source:
    """Takes a Gramps Source object and creates one of ours."""
    global sources_map

    # Use the cached source if we can.
    gramps_id = src_obj.gramps_id
    if gramps_id in sources_map:
        return sources_map[gramps_id]

    # We assume that there's at most one note associated with a
    # source, and that this is its description.
    description = ""
    if src_obj.note_list:
        description = gramps_db.get_note_from_handle(src_obj.note_list[0]).text
    src_type = SourceType.UNKNOWN
    if src_obj.attribute_list:
        for attr in src_obj.attribute_list:
            if attr.type == "Type":
                src_type = parse_source_type(attr.value)
    source = Source(src_obj.title, gramps_id, description, src_type)

    sources_map[gramps_id] = source
    return source

def extract_gender(person):
    g = person.get_gender()
    if g == Person.MALE:
        return Gender.MALE
    if g == Person.FEMALE:
        return Gender.FEMALE
    return Gender.OTHER

def get_event(person, index, gramps_db):
    if index < 0:
        return None
    event_obj = gramps_db.get_event_from_handle(person.event_ref_list[index].ref)
    return Event(event_obj.get_gramps_id(),
                 event_obj.date,
                 event_obj.get_description(),
                 event_obj.place if event_obj.place else "",
                 event_obj.get_type(),
                 get_sources_from_cites(event_obj, gramps_db))

def get_sources_from_cites(gramps_obj, gramps_db):
    sources = []
    for cite_handle in gramps_obj.citation_list:
        cite = gramps_db.get_citation_from_handle(cite_handle)
        src_obj = gramps_db.get_source_from_handle(cite.source_handle)
        src = make_source(src_obj, gramps_db)
        if src not in sources:
            sources.append(src)
    return sources

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
    page_sources = PageSources()
    person = next((p
                   for p in get_people()
                   if p.gramps_id == person_id),
                  None)
    return render_template("person.html",
                           person=person,
                           page_sources=page_sources)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dbpath",
        type=str,
        nargs="?",
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
