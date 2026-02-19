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
from gramps.gen.lib import Person, EventType, AttributeType
from gramps.gen.db.utils import make_database
from gramps.gen.lib.date import Date

CITE_LETTERS = "abcdefghijklmnopqrstuvwxyz"

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

def render_source_type(t: SourceType) -> str:
    if t == SourceType.RECOLLECTIONS:
        return "Recollections"
    elif t == SourceType.PRIMARY:
        return "Primary source"
    elif t == SourceType.TREE:
        return "Another family tree"
    elif t == SourceType.WEB:
        return "Website"
    else:
        return "Unknown"

@dataclass
class Source:
    title: str
    gramps_id: str
    description: str
    source_type: SourceType

@dataclass
class Cite:
    gramps_id: str
    description: Optional[str]
    source: Source

# Tracks all the citations on a certain page and assigns
# labels to them (and their associated sources).
class PageCites:
    def __init__(self):
        self.num = 1
        self.src_to_num = {}
        self.src_to_cite_letter_pairs = {}
        self.srclist = []

    def get_src_number(self, src: Source) -> int:
        src_id = src.gramps_id
        if src_id not in self.src_to_num:
            self.src_to_num[src_id] = self.num
            self.num += 1
            self.srclist.append(src)
            self.src_to_cite_letter_pairs[src_id] = []
        return self.src_to_num[src_id]

    def get_cite_label(self, cite: Cite) -> str:
        src_num = self.get_src_number(cite.source)
        if not cite.description:
            # Only cites with a description need a sublabel, otherwise
            # they're indistinguishable from the others.
            return str(src_num)

        cite_letter_pairs = self.src_to_cite_letter_pairs[cite.source.gramps_id]
        this_letter = None
        for other_cite, letter in cite_letter_pairs:
            if other_cite.gramps_id == cite.gramps_id:
                this_letter = letter
                break
        if not this_letter:
            this_letter = CITE_LETTERS[len(cite_letter_pairs)]
            cite_letter_pairs.append((cite, this_letter))
        return f"{src_num}{this_letter}"

    def get_cite_letter_pairs(self, src: Source) -> List[Tuple[Cite, str]]:
        return self.src_to_cite_letter_pairs[src.gramps_id]

@dataclass
class Note:
    content: str
    cites: List[Cite]

@dataclass
class Event:
    gramps_id: str
    date: Optional[Date]
    description: Optional[str]
    place: Optional[str]
    event_type: EventType
    cites: List[Cite]

@dataclass
class Name:
    title: str
    first: str
    surname: str
    name_type: str
    cites: List[Cite]

@dataclass
class Family:
    family_id: str
    parent1_id: Optional[str]
    parent2_id: Optional[str]
    relationship_type: str
    # Tuples of ID + relationship to parents.
    children: List[Tuple[str, str]]
    events: List[Event]
    notes: List[Note]
    cites: List[Cite]

@dataclass
class PersonInfo:
    display_name: str
    listing_name: str
    names: List[Name]
    gramps_id: str
    birth: Optional[Event]
    death: Optional[Event]
    gender: Gender
    families_as_partner: List[Family]
    families_as_child: List[Family]
    events: List[Event]
    notes: List[Note]
    bio_cites: List[Cite]

def format_child_row(child_id: str, relation_type, date_markers=True) -> str:
    return (format_person_row(child_id, date_markers=date_markers)
            + f"<td>{relation_type}</td>")

def format_person_row(person_id: str, date_markers=True) -> str:
    global people_map
    person = people_map[person_id]
    cells = []
    cells.append(f"<td><a href='/person/{person.gramps_id}.html'>{person.display_name}</a></td>")
    cells.append(f"<td>{format_gender(person.gender)}</td>")
    cells.append(f"<td>{'b. ' if date_markers else ''}{format_event_date(person.birth)}</td>")
    cells.append(f"<td>{'d. ' if date_markers else ''}{format_event_date(person.death, default='-')}</td>")
    return "".join(cells)

def format_event_date(event: Optional[Event], page_cites: Optional[PageCites] = None, default="?") -> str:
    """If page_cites is supplied, then a citation will be added."""
    if not event or not event.date:
        return default
    s = format_date(event.date)
    if page_cites:
        return format_cite(s, event.cites, page_cites)
    return s

def format_cite(s: str, cites: List[Cite], page_cites: PageCites) -> str:
    parts = [s]
    if not cites:
        parts.append("<sup class='citebad'>[citation needed]</sup>")
    else:
        already_added = set()
        for cite in cites:
            src = cite.source
            label = page_cites.get_cite_label(cite)
            if label not in already_added:
                parts.append(f"<a class='citelink' href='#cite{label}'>")
                parts.append(f"<sup class='{get_cite_class(src.source_type)}'>")
                parts.append(f"[{label}]")
                parts.append("</sup>")
                parts.append("</a>")
    return "".join(parts)

def format_events_table(events: List[Event], page_cites: PageCites) -> str:
    if events:
        parts = ["""<table class="bordered-centered-table text-centered">
<tr><th>Type</th><th>Date</th><th>Location</th><th>Description</th><th>Sources</th></tr>"""]
        for ev in events:
            parts.append(f"<tr>{format_event_row(ev, page_cites)}</tr>")
        parts.append("</table>")
        return "".join(parts)
    else:
        return "<p>(none known)</p>"

def format_event_row(ev: Event, page_cites: PageCites) -> str:
    return "".join([
        f"<td>{str(ev.event_type)}</td>",
        f"<td>{format_date(ev.date)}</td>",
        f"<td>{ev.place or '-'}</td>",
        f"<td>{ev.description or '-'}</td>",
        f"<td>{format_cite('', ev.cites, page_cites)}</td>"
    ])

def format_notes_table(notes: List[Note], page_cites: PageCites) -> str:
    if not notes:
        return "<p>(none)</p>"
    parts = ["""<table class="bordered-centered-table">
<tr><th>Content</th><th>Sources</th></tr>"""]
    for note in notes:
        parts.append(f"""<tr><td>{note.content}</td><td>{format_cite("", note.cites, page_cites)}</td></tr>""")
    parts.append("</table>")
    return "".join(parts)

def format_cite_section(page_cites: PageCites) -> str:
    parts = []
    for src in page_cites.srclist:
        src_number = page_cites.get_src_number(src)
        parts.append(f"<p><span id='cite{src_number}' class='person-citation'>")
        parts.append(f"<span class='{get_cite_class(src.source_type)}'>[{src_number}]</span> ")
        parts.append(src.title)

        parts.append(f" <a href='/source/{src.gramps_id}.html'>(source page)</a>")
        parts.append("</span>")
        for cite, letter in page_cites.get_cite_letter_pairs(src):
            parts.append(f"<br><span class='indent person-citation' id='cite{page_cites.get_cite_label(cite)}'>↳ ({letter}) <i>{cite.description}</i></span>")
        parts.append("</p>")
    return "".join(parts)

def get_cite_class(src_type: SourceType) -> str:
    if src_type in [SourceType.PRIMARY, SourceType.WEB]:
        return "citegood"
    elif src_type in [SourceType.RECOLLECTIONS, SourceType.TREE]:
        return "citeokay"
    return "citebad"

def format_date(d: Optional[Date]) -> str:
    if d is None:
        return "?"
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
        return f"{prefix}{month:02d}/{year}"
    return f"{prefix}{day:02d}/{month:02d}/{year}"
    
def format_gender(g: Gender):
    if g == Gender.MALE:
        return "♂️"
    if g == Gender.FEMALE:
        return "♀️"
    return "?"

people = None
people_map = {}
sources_map = {}
family_map = {}
event_map = {}

def get_people():
    global people
    return people

def get_person(person_id: str) -> PersonInfo:
    global people_map
    return people_map[person_id]

def get_event(event_id: str) -> Event:
    global event_map
    return event_map[event_id]

def load_db_data(path: Path):
    global people, people_map

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
    for person in people:
        people_map[person.gramps_id] = person

    state.get_database().close()

def load_people(gramps_db):
    gramps_persons = [
        Person(person_data) 
        for handle, person_data
        in gramps_db.get_person_cursor()]

    return [make_person_info(person, gramps_db)
            for person in gramps_persons]

def make_person_info(person, gramps_db):
    names = extract_names(person, gramps_db)
    person_info = PersonInfo(
        extract_display_name(person),
        person.get_primary_name().get_name(),
        names,
        person.get_gramps_id(),
        get_event_from_idx(person, person.birth_ref_index, gramps_db),
        get_event_from_idx(person, person.death_ref_index, gramps_db),
        extract_gender(person),
        get_families_as_partner(person, gramps_db),
        get_families_as_child(person, gramps_db),
        get_events(person, gramps_db),
        get_notes(person, gramps_db),
        get_bio_cites(person, gramps_db))
    for name in names:
        # If the birth name doesn't have associated sources, then
        # fall back on the "base" source, i.e. the source for
        # their existence.
        # Shouldn't be using a raw string, tho.
        if not name.cites and name.name_type == "Birth Name":
            name.cites = person_info.bio_cites
    return person_info

def get_bio_cites(person, gramps_db) -> List[Source]:
    return get_citations(person, gramps_db)

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
        description = get_note_text_from_ref(src_obj.note_list[0], gramps_db)
    src_type = SourceType.UNKNOWN
    if src_obj.attribute_list:
        for attr in src_obj.attribute_list:
            if attr.type == "Type":
                src_type = parse_source_type(attr.value)
    source = Source(src_obj.title, gramps_id, description, src_type)

    sources_map[gramps_id] = source
    return source

def get_note_text_from_ref(note_ref, gramps_db) -> str:
    return gramps_db.get_note_from_handle(note_ref).text

def get_families_as_partner(person, gramps_db) -> List[Family]:
    return get_families(person.get_family_handle_list(), gramps_db)

def get_families_as_child(person, gramps_db) -> List[Family]:
    return get_families(person.get_parent_family_handle_list(), gramps_db)

def get_families(handle_list, gramps_db) -> List[Family]:
    fams = []
    for handle in handle_list:
        fam_obj = gramps_db.get_family_from_handle(handle)
        fams.append(make_family(fam_obj, gramps_db))
    return fams

def make_family(fam_obj, gramps_db) -> Family:
    global family_map
    gramps_id = fam_obj.get_gramps_id()
    if gramps_id in family_map:
        return family_map[gramps_id]
    children = []
    for child_ref in fam_obj.get_child_ref_list():
        child_obj = gramps_db.get_person_from_handle(child_ref.get_reference_handle())
        children.append(
            (child_obj.get_gramps_id(),
             # Assume it's the same relationship as to
             # the mother.
             str(child_ref.get_father_relation())))
    result = Family(
        gramps_id,
        get_parent_id(fam_obj.get_father_handle(), gramps_db),
        get_parent_id(fam_obj.get_mother_handle(), gramps_db),
        str(fam_obj.get_relationship()),
        children,
        get_events(fam_obj, gramps_db),
        get_notes(fam_obj, gramps_db),
        get_citations(fam_obj, gramps_db))
    family_map[gramps_id] = result
    return result

def get_parent_id(handle, gramps_db) -> Optional[str]:
    if not handle:
        return None
    return gramps_db.get_person_from_handle(handle).get_gramps_id()

def extract_gender(person):
    g = person.get_gender()
    if g == Person.MALE:
        return Gender.MALE
    if g == Person.FEMALE:
        return Gender.FEMALE
    return Gender.OTHER

def get_event_from_idx(person, index, gramps_db) -> Event:
    if index < 0:
        return None
    return get_event_from_ref(person.event_ref_list[index], gramps_db)

def get_events(person_or_family, gramps_db) -> Event:
    return [get_event_from_ref(ref, gramps_db)
            for ref in person_or_family.event_ref_list]

def get_event_from_ref(event_ref, gramps_db) -> Event:
    return make_event(gramps_db.get_event_from_handle(event_ref.ref),
                      gramps_db)

def make_event(event_obj, gramps_db) -> Event:
    global event_map
    event_id = event_obj.get_gramps_id()
    if event_id in event_map:
        return event_map[event_id]
    event = Event(event_id,
                  event_obj.date,
                  event_obj.get_description(),
                  (get_place_from_ref(event_obj.place, gramps_db)
                   if event_obj.place
                   else None),
                  event_obj.get_type(),
                  get_citations(event_obj, gramps_db))
    event_map[event_id] = event
    return event

def get_place_from_ref(ref, gramps_db) -> str:
    # Need to get the "value" as it's a PlaceName object.
    return gramps_db.get_place_from_handle(ref).get_name().get_value()

def get_notes(obj, gramps_db) -> List[Note]:
    result = []
    for attr in obj.attribute_list:
        # The actual content is assumed to be in a single
        # note object, inside the description attribute.
        if (attr.type == AttributeType.DESCRIPTION
                and len(attr.note_list) > 0):
            result.append(Note(
                get_note_text_from_ref(attr.note_list[0], gramps_db),
                get_citations(attr, gramps_db)))
            if len(attr.note_list) > 1:
                print(f"WARNING: {obj.gramps_id} has a description attribute with multiple notes.")
    return result

def get_citations(gramps_obj, gramps_db) -> List[Cite]:
    citations = []
    for cite_handle in gramps_obj.citation_list:
        cite = gramps_db.get_citation_from_handle(cite_handle)
        src_obj = gramps_db.get_source_from_handle(cite.source_handle)
        citations.append(
            Cite(cite.gramps_id,
                 cite.get_page(),
                 make_source(src_obj, gramps_db)))
    return citations

def extract_display_name(person):
    prim_name = person.get_primary_name()
    return f"{prim_name.get_first_name()} {prim_name.get_surname()}"

def extract_names(person, gramps_db) -> List[Name]:
    return [extract_name(n, gramps_db)
            for n in ([person.get_primary_name()]
                      + person.get_alternate_names())]

def extract_name(name_obj, gramps_db) -> Name:
    return Name(name_obj.get_title() or "-",
                name_obj.get_first_name(),
                name_obj.get_surname(),
                str(name_obj.type),
                get_citations(name_obj, gramps_db))

app = Flask(__name__)
app.jinja_env.globals.update(
    format_event_date=format_event_date,
    format_cite=format_cite,
    format_gender=format_gender,
    format_person_row=format_person_row,
    format_child_row=format_child_row,
    format_events_table=format_events_table,
    format_notes_table=format_notes_table,
    format_cite_section=format_cite_section,
    render_source_type=render_source_type,
    get_person=get_person,
    EventType=EventType)

@app.route("/")
@app.route("/home.html")
def home_page():
    return render_template("home.html")

@app.route("/people.html")
def people_page():
    return render_template("people.html", people=get_people())

@app.route("/person/<person_id>.html")
def person_page(person_id):
    global people_map
    return render_template("person.html",
                           person=people_map[person_id],
                           page_cites=PageCites())

@app.route("/sources.html")
def sources_page():
    global sources_map
    return render_template("sources.html", sources=list(sources_map.values()))

@app.route("/source/<source_id>.html")
def source_page(source_id):
    global sources_map
    src = next((src
                for src in sources_map.values()
                if src.gramps_id == source_id),
                None)
    return render_template("source.html", src=src)

@app.route("/family/<family_id>.html")
def family_page(family_id):
    global family_map
    return render_template("family.html",
                           family=family_map[family_id],
                           page_cites=PageCites())

@app.route("/families.html")
def families_page():
    global family_map
    return render_template("families.html", families=list(family_map.values()))

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
        people = [PersonInfo("person1", "listing1",
                    [Name("Mr.", "Hello", "Goodbye", "Birth Name", [])],
                    "I001", None, None, Gender.MALE, [], [], [], [], []),
                  PersonInfo("person2", "listing2",
                    [Name("Mrs.", "Zello", "Goodbye", "Married Name", [])],
                    "I002", None, None, Gender.FEMALE, [], [], [], [], [])]

    app.run(port=8000)

if __name__ == "__main__":
    main()
