## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Document my assumptions in the Gramps data (sources have a Type attribute, and a note to describe them; bio info in a Description attribute)
* Add a browseable tree interface (maybe try dTree first).
* Add Quilt Chart.

### References
Gramps API:
* https://www.gramps-project.org/wiki/index.php?title=Using_database_API
* The Gramps codebase, e.g. https://github.com/gramps-project/gramps/blob/master/gramps/gen/lib/person.py
* https://genealogy.stackexchange.com/questions/1431/accessing-data-natively-in-gramps

Tree visualisation:
* https://github.com/bartfeenstra/betty
* https://github.com/PeWu/topola-viewer
* https://github.com/trongthanh/family-tree
* https://github.com/ErikGartner/dTree
