## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Family pages.
  `-> Fill out sources on family page.
* Refactoring: make name type an enum? And remove "Birth Name" hardcoded value.
  `-> Same for child relationship types & partner rel type.
* [Person & Family pages] Events.
  `-> Update families on person page w/ "marriage date"
* [Person & Family pages] Descriptions.
  `-> Update families on person page w/ "# notes"
* Maybe an /event/... endpoint?
  `-> Event descriptions might come from Description attribute or
      elsewhere, need to streamline the convention.
* Names index? Include all names for all people.
* Fix sources vs. citations, some info is hidden in citations.
* Generation number, to display in people page. Makes it clearer how old people are.
* Stats like total people & unique surnames.
* Document my assumptions in the Gramps data (sources have a Type attribute, and a note to describe them; bio info in a Description attribute)
* Add a browseable tree interface.
* Add the cool plot to show relationships.

### Data entry
* Marriage of Martin Clarke & Honor Kelly is not associated with Honor (referring to the event).
* "Honor" etymology, I guess that's where "Norah" comes from.
  https://www.libraryireland.com/names/women/onora-honor.php
* There are a bunch of events not associated with anyone or anything.
* "Bríd" is listed as mam's nickname, should be "also known as".
* "Sean Galligan", I0188, might be a duplicate?

### References
* https://www.gramps-project.org/wiki/index.php?title=Using_database_API
* The Gramps codebase, e.g. https://github.com/gramps-project/gramps/blob/master/gramps/gen/lib/person.py
* https://genealogy.stackexchange.com/questions/1431/accessing-data-natively-in-gramps
