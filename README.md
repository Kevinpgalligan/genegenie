## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Add sources for biographical information.
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
* Describe assumptions in the data (sources have a Type attribute, and a note to describe them; bio info in a Description attribute)

### Brainstorming
I'm not sure how to handle sourcing for biographical information. There's a source associated with events like birth, death and so on. Fine. Wherever those events / dates are displayed, we also show their source.

There's the "existence" source. The existence of someone of that name & gender. Not sure where to display that on the page, or how to communicate that the source is for the existence / basic information.

Can there be separate sources for each name? For example, Dad knows some of his aunts only by their chosen names, as nuns. From the census, I can figure out their birth names. So do I want a separate source for each name?

Perhaps... for the gender, we use the person sources. For the names, we use person sources *if no more specific source is provided*. Or, maybe it's simpler to just dump all the sources for names into the list of sources for the person.

Finally, there's the Family-level sources. Who's in a family, what's the nature of the family, etc. I think each family has its own sources to account for all that. Perhaps those family sources can be displayed next to the different families on a person's page.
