## genegenie
A website generator for Gramps family trees.

![the people page, a table with name, gender, birth, death etc.](https://github.com/Kevinpgalligan/genegenie/blob/master/img/people.png)

See **docs/conventions.md** for a list of conventions I follow in my Gramps project, which the software makes use of.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask web server.

## Usage
Install Python dependencies:

```
pip3 install -r requirements.txt
```

Run the server:

```
python3 app.py ~/.gramps/grampsdb/<your-tree-id>/
```

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

### TODO
* Add a browseable tree interface (maybe try dTree first).
* Ability to dump a frozen version of the website.
* Add Quilt Chart.
