import argparse
from pathlib import Path
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List, Set

from flask import Flask, render_template
from flask_frozen import Freezer
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
    OTHER = 3

class SourceQuality(Enum):
    GOOD = 1
    FINE = 2
    MEDIOCRE = 3
    MISSING = 4

@dataclass
class Source:
    title: str
    gramps_id: str
    description: str
    quality: SourceQuality

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
    gramps_id: str
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
    num_ancestors: Optional[int]
    num_descendents: Optional[int]
    generation_number: Optional[int]
    bio_cites: List[Cite]

@dataclass
class CiteStats:
    count: int = 0
    good: int = 0
    fine: int = 0
    mediocre: int = 0
    missing: int = 0

    ids_for_mediocre: Set[str] = field(default_factory=set)
    ids_for_missing: Set[str] = field(default_factory=set)

    def record(self, gramps_id: str, q: SourceQuality):
        self.count += 1
        if q == SourceQuality.GOOD:
            self.good += 1
        elif q == SourceQuality.FINE:
            self.fine += 1
        elif q == SourceQuality.MEDIOCRE:
            self.mediocre += 1
            self.ids_for_mediocre.add(gramps_id)
        elif q == SourceQuality.MISSING:
            self.missing += 1
            self.ids_for_missing.add(gramps_id)
        else:
            raise Exception("Unknown source quality type.")

    def record_missing(self, gramps_id: str):
        self.count += 1
        self.missing += 1
        self.ids_for_missing.add(gramps_id)

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
                parts.append(f"<sup class='{get_cite_class(src)}'>")
                parts.append(f"[{label}]")
                parts.append("</sup>")
                parts.append("</a>")
    return "".join(parts)

def format_person_events_table(person: PersonInfo, page_cites: PageCites) -> str:
    events = person.events[:]
    for fam in person.families_as_partner:
        for ev in fam.events:
            if not any(other.gramps_id == ev.gramps_id for other in events):
                events.append(ev)
    return format_events_table(events, page_cites)

def format_events_table(events: List[Event], page_cites: PageCites) -> str:
    if events:
        # Not sure if sorting on the Date type works with None.
        events_no_date = [ev for ev in events if not ev.date]
        events_dated = sorted([ev for ev in events if ev.date],
                              key=lambda ev: ev.date)
        events = events_dated + events_no_date
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

def format_names_index() -> str:
    global people
    names = []
    for perp in people:
        for name in perp.names:
            names.append((perp.gramps_id, name))
    names.sort(key=lambda tup: " ".join([tup[1].first, tup[1].surname]))
    parts = [f"""<p><table class='bordered-centered-table'>
<tr><th>Names count</th><td>{len(names)}</td></table></p>
<p><table class='bordered-centered-table'>
<tr><th>Name</th><th>Title</th><th>Type</th></tr>"""]
    for person_id, name in names:
        parts.extend([
            f"<tr><td><a href='/person/{person_id}.html'>",
            f"{name.first} {name.surname}</a></td>",
            f"<td>{name.title}</td>",
            f"<td>{name.name_type}</td></tr>"
        ])
    parts.append("</table></p>")
    return "".join(parts)

def format_cite_section(page_cites: PageCites) -> str:
    parts = []
    for src in page_cites.srclist:
        src_number = page_cites.get_src_number(src)
        parts.append(f"<p><span id='cite{src_number}' class='person-citation'>")
        parts.append(f"<span class='{get_cite_class(src)}'>[{src_number}]</span> ")
        parts.append(src.title)

        parts.append(f" <a href='/source/{src.gramps_id}.html'>(source page)</a>")
        parts.append("</span>")
        for cite, letter in page_cites.get_cite_letter_pairs(src):
            parts.append(f"<br><span class='indent person-citation' id='cite{page_cites.get_cite_label(cite)}'>↳ ({letter}) <i>{cite.description}</i></span>")
        parts.append("</p>")
    return "".join(parts)

def format_citation_stats(stats: CiteStats) -> str:
    parts = ["""<table class='bordered-centered-table'>
<tr><td></td><th>Missing</th><th>Mediocre</th><th>Fine</th><th>Good</th><th>Total</th></tr>
<tr><th>Count</th>"""]
    ns = [stats.missing, stats.mediocre, stats.fine, stats.good, stats.count]
    for n in ns:
        parts.append(f"<td>{n}</td>")
    parts.append("</tr>")
    parts.append("<tr><th>Percentage</th>")
    for n in ns[:-1]:
        pct = (100.0*(n/stats.count)) if stats.count > 0 else 0
        parts.append(f"<td>{pct:.2f}%</td>")
    parts.append("</tr>")
    parts.append("</table>")
    parts.append(f"<p>IDs with mediocre: {', '.join(gid for gid in stats.ids_for_mediocre)}</p>")
    parts.append(f"<p>IDs with missing: {', '.join(gid for gid in stats.ids_for_missing)}</p>")
    return "".join(parts)

def get_cite_class(src: Source) -> str:
    q = src.quality
    if q == SourceQuality.GOOD:
        return "citegood"
    elif q == SourceQuality.FINE:
        return "citeokay"
    elif q == SourceQuality.MEDIOCRE:
        return "citemediocre"
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
    gather_people_stats(people)

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
        None,
        None,
        None,
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
    quality = SourceQuality.MEDIOCRE
    found_q = False
    if src_obj.attribute_list:
        for attr in src_obj.attribute_list:
            if attr.type == "Quality":
                quality = parse_source_quality(attr.value)
                found_q = True
    if not found_q:
        print(f"WARN: source {gramps_id} does not have a Quality attribute.")
    source = Source(src_obj.title, gramps_id, description, quality)

    sources_map[gramps_id] = source
    return source

def parse_source_quality(s: str) -> SourceQuality:
    if s == "good":
        return SourceQuality.GOOD
    if s == "fine":
        return SourceQuality.FINE
    return SourceQuality.MEDIOCRE

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

def gather_people_stats(people: List[PersonInfo]):
    for person in people:
        count_ancestors(person)
        count_descendents(person)
        count_generations(person)
    propagate_generations(people[0], people[0].generation_number, set())

def best_cite_quality(cites: List[Cite]) -> SourceQuality:
    if not cites:
        return SourceQuality.MISSING
    best = cites[0].source.quality
    for cite in cites:
        q = cite.source.quality
        if q.value < best.value:
            best = q
    return best

def count_ancestors(person: PersonInfo) -> int:
    global people_map
    if not person.num_ancestors:
        count = 0
        for fam in person.families_as_child:
            if is_birth_family(person, fam):
                if fam.parent1_id:
                    count += 1 + count_ancestors(people_map[fam.parent1_id])
                if fam.parent2_id:
                    count += 1 + count_ancestors(people_map[fam.parent2_id])
                break # there should only be 1 birth family per person
        person.num_ancestors = count
    return person.num_ancestors

def get_child_relationship(child: PersonInfo, family: Family) -> str:
    return next(rel_type
                for (child_id, rel_type) in family.children
                if child_id == child.gramps_id)

def count_descendents(person: PersonInfo) -> int:
    global people_map
    if not person.num_descendents:
        count = 0
        for fam in person.families_as_partner:
            for child_id, rel_type in fam.children:
                if rel_type == "Birth":
                    count += 1 + count_descendents(people_map[child_id])
        person.num_descendents = count
    return person.num_descendents

def count_generations(person: PersonInfo) -> int:
    # Assuming that the tree is a directed acyclic graph.
    # i.e. no incest in the family between different generations (yikes).
    global people_map
    if not person.generation_number:
        gen = 1
        has_birth_family = False
        for fam in person.families_as_child:
            if is_birth_family(person, fam):
                gen = 1 + calc_max_parent_generation(person, fam)
                has_birth_family = True
                break
        person.generation_number = gen
    return person.generation_number

def calc_max_parent_generation(person: PersonInfo, family: Family) -> int:
    p1, p2 = None, None
    g1, g2 = None, None
    if family.parent1_id:
        p1 = people_map[family.parent1_id]
        g1 = count_generations(p1)
    if family.parent2_id:
        p2 = people_map[family.parent2_id]
        g2 = count_generations(p2)
    if not p1 and not p2:
        return 0
    if p1 and not p2:
        return p1.generation_number
    if not p1 and p2:
        return p2.generation_number
    if g1 < g2:
        propagate_generations(p1, g2, set([p2.gramps_id]))
        return g2
    if g1 > g2:
        propagate_generations(p2, g1, set([p1.gramps_id]))
        return g1
    return g1

def propagate_generations(person: PersonInfo, gen: int, visited: Optional[Set[str]]):
    global people_map
    # Don't bother propagating if we haven't even calculated
    # someone's generation number yet, we'll get to them later.
    if person.generation_number and not person.gramps_id in visited:
        visited.add(person.gramps_id)
        person.generation_number = gen
        next_gen = gen - 1
        for fam in person.families_as_child:
            if is_birth_family(person, fam):
                if fam.parent1_id:
                    propagate_generations(people_map[fam.parent1_id], next_gen, visited)
                if fam.parent2_id:
                    propagate_generations(people_map[fam.parent2_id], next_gen, visited)
                break
        for fam in person.families_as_partner:
            if fam.parent1_id:
                propagate_generations(people_map[fam.parent1_id], gen, visited)
            if fam.parent2_id:
                propagate_generations(people_map[fam.parent2_id], gen, visited)
            for child_id, rel_type in fam.children:
                if rel_type == "Birth":
                    propagate_generations(people_map[child_id], gen+1, visited)



def is_birth_family(person: PersonInfo, family: Family) -> bool:
    return get_child_relationship(person, family) == "Birth"

def get_existence_cites(person: PersonInfo) -> List[Cite]:
    result = []
    seen = set()
    def add_cites(cs):
        for c in cs:
            if c.gramps_id not in seen:
                seen.add(c.gramps_id)
                result.append(c)
    add_cites(person.bio_cites)
    for ev in person.events:
        add_cites(ev.cites)
    for name in person.names:
        add_cites(name.cites)
    for note in person.notes:
        add_cites(note.cites)
    for fam in person.families_as_partner:
        add_cites(fam.cites)
        for ev in fam.events:
            add_cites(ev.cites)
    return result

app = Flask(__name__)
app.jinja_env.globals.update(
    format_event_date=format_event_date,
    format_cite=format_cite,
    format_gender=format_gender,
    format_person_row=format_person_row,
    format_child_row=format_child_row,
    format_person_events_table=format_person_events_table,
    format_events_table=format_events_table,
    format_notes_table=format_notes_table,
    format_names_index=format_names_index,
    format_cite_section=format_cite_section,
    format_citation_stats=format_citation_stats,
    get_cite_class=get_cite_class,
    get_existence_cites=get_existence_cites,
    get_person=get_person,
    EventType=EventType)

freezer = Freezer(app)

@app.route("/home.html")
@app.route("/")
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

@app.route("/names.html")
def names_page():
    return render_template("names.html")

@app.route("/citestats.html")
def citestats_page():
    global people, family_map

    peep_stats = CiteStats()
    birth_stats = CiteStats()
    name_stats = CiteStats()
    event_stats = CiteStats()
    fam_stats = CiteStats()
    marriage_stats = CiteStats()
    note_stats = CiteStats()

    for peep in people:
        # Count someone as having a source for their existence if
        # they have a citation attached to them or to one of their events.
        for ev in peep.events:
            event_stats.record(ev.gramps_id, best_cite_quality(ev.cites))

        if peep.birth:
            birth_stats.record(peep.gramps_id, best_cite_quality(peep.birth.cites))
        else:
            birth_stats.record_missing(peep.gramps_id)

        for name in peep.names:
            name_stats.record(peep.gramps_id, best_cite_quality(name.cites))

        for note in peep.notes:
            note_stats.record(peep.gramps_id, best_cite_quality(note.cites))

        peep_stats.record(
            peep.gramps_id,
            best_cite_quality(
                get_existence_cites(peep)))

    for fam in family_map.values():
        fam_stats.record(fam.gramps_id, best_cite_quality(fam.cites))
        has_marriage_event = False
        for ev in fam.events:
            event_stats.record(ev.gramps_id, best_cite_quality(ev.cites))
            if ev.event_type == EventType.MARRIAGE:
                marriage_stats.record(fam.gramps_id, best_cite_quality(ev.cites))
                has_marriage_event = True
        if (fam.relationship_type == "Married") and not has_marriage_event:
            marriage_stats.record_missing(fam.gramps_id)

    return render_template(
        "citestats.html",
        peep_stats=peep_stats,
        birth_stats=birth_stats,
        name_stats=name_stats,
        event_stats=event_stats,
        fam_stats=fam_stats,
        marriage_stats=marriage_stats,
        note_stats=note_stats)

# Need to help Frozen-Flask to find the parameterised page names.
@freezer.register_generator
def person_urls():
    global people
    for person in people:
        yield "person_page", dict(person_id=person.gramps_id)

@freezer.register_generator
def family_urls():
    global family_map
    for fam in family_map.values():
        yield "family_page", dict(family_id=fam.gramps_id)

@freezer.register_generator
def src_urls():
    global sources_map
    for src in sources_map.values():
        yield "source_page", dict(source_id=src.gramps_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dbpath",
        type=str,
        nargs="?",
        help="Path to Gramps database, e.g. ~/.gramps/grampsdb/<tree-id>")
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Whether to generate all the website files and dump them to a build directory.")
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
                    "I001", None, None, Gender.MALE, [], [], [], [],
                    0, 0, 0, []),
                  PersonInfo("person2", "listing2",
                    [Name("Mrs.", "Zello", "Goodbye", "Married Name", [])],
                    "I002", None, None, Gender.FEMALE, [], [], [], [],
                    0, 0, 0, [])]
    if args.freeze:
        print("Building website, saving to build/ directory.")
        freezer.freeze()
    else:
        app.run(port=8000)

if __name__ == "__main__":
    main()
