## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* [Person page] Improve formatting of sources list.
  `-> And pick better colour palette for bad/okay/good.
* Add /source/... endpoint, and link to it for each source.
* [Person page] names section.
* [Person page] relatives section.
* [Person page] events section.
* [Person page] description section.
* Maybe an /event/... endpoint?
  `-> Event descriptions might come from Description attribute, need
      to streamline the convention.
* [People list] Distinguish between people who aren't dead (or who may not be dead), and people we know are definitely dead but whose death dates we don't know.
* Generation number, to display in events page. Makes it clearer how old people are.
* Stats like total people & unique surnames.
* Describe assumptions in the data (sources have a Type attribute, and a note to describe them; bio info in a Description attribute)
* Add a browseable tree interface.
* Add the cool box plot to show relationships.

### Data entry
* Marriage of Martin Clarke & Honor Kelly is not associated with Honor (referring to the event).
* "Honor" etymology, I guess that's where "Norah" comes from.
  https://www.libraryireland.com/names/women/onora-honor.php
* There are a bunch of events not associated with anyone or anything.
