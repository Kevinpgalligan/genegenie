## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* [Person & Family pages] Descriptions.
  `-> Update families on person page w/ "# notes"
* (Possibly more of a data problem)
  Family events are not associated with their participants. Either
  manually add each marriage event to the individuals, or fetch them
  programmatically (for each person, add all family events... maybe
  just from the families in which they were a partner, not a child).
* Check Event conventions. Do any events have a description in a Description attribute?
  Are any of the descriptions long enough that it might be worth adding an events endpoint?
  Does the convention need to be streamlined?
     (one possibility: description attributes are an "extended description" that's
      shown on the event page)
* Names index. Include all names for all people.
* Fix sources vs. citations, some info is hidden in citations.
* Generation number, to display in people page. Makes it clearer how old people are.
* Stats like total number of people & unique surnames.
* Add a browseable tree interface.
* Add the cool plot to show relationships.
* Document my assumptions in the Gramps data (sources have a Type attribute, and a note to describe them; bio info in a Description attribute)

### References
* https://www.gramps-project.org/wiki/index.php?title=Using_database_API
* The Gramps codebase, e.g. https://github.com/gramps-project/gramps/blob/master/gramps/gen/lib/person.py
* https://genealogy.stackexchange.com/questions/1431/accessing-data-natively-in-gramps
