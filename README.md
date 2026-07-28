## genegenie
A website generator for Gramps family trees.

A demo can be found [HERE](https://kevingal.com/genegenie/).

![the people page, a table with name, gender, birth, death etc.](https://github.com/Kevinpgalligan/genegenie/blob/master/img/people.png)

See **notes/conventions.md** for a list of conventions I follow in my Gramps project, which the software makes use of.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask web server.

### Usage
Install Python dependencies:

```
pip3 install -r requirements.txt
```

Run the server:

```
python3 app.py ~/.gramps/grampsdb/<your-tree-id>/
```

...and then open the indicated local URL in a browser.

Or generate all the website files and dump them to a `build` directory:

```
python3 app.py ~/.gramps/grampsdb/<your-tree-id>/ --freeze
```

For the tree visualisation, the family-chart npm package is used. It should just work, but for future reference (and to update the tree configuration code) here's how I set it up:

* Install dependencies: `npm install`.
* Manually copy family-chart CSS: `cp node_modules/family-chart/dist/styles/family-chart.css static/css/`.
* Install webpack, `npm install webpack webpack-cli --save-dev`.
* Run webpack command `webpack ./src/tree.js --mode production --output-path ./static/js/ --output-filename bundle.js --output-library-name tree --output-library-type window`

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
* https://donatso.github.io/family-chart-doc/
