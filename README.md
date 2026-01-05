## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Fill out the Person page (see: <https://www.gramps-project.org/wiki/index.php?title=Using_database_API>)
  `-> Citations for bio info?
  `-> Names.
  `-> Relatives.
  `-> Events (should be relatively easy).
  `-> Description.
* Sources page? Events page? Tree browser?
* In the people list: distinguish between people who aren't dead (or who may not be dead), and people we know are definitely dead but whose death dates we don't know.
* Generation number, to display in events page. Makes it clearer how old people are.
* Stats like total people & unique surnames.
