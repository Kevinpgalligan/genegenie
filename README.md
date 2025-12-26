## genegenie
Work-in-progress website generator for Gramps family trees.

This will be very specific to how I use the Gramps software, and the conventions I've adopted. However, it might be useful as a basis for someone who wants to develop their own Gramps-related software.

### Requirements
* Gramps 5.1 (haven't tested with other versions).
* The Gramps Python package should be on your Python path. I achieved this by installing Gramps through my Ubuntu package manager: `apt install gramps`.
* Flask (Python web server... I will eventually freeze the requirements in a requirements.txt).

### TODO
* Fix 0000-00-00 death date, I0148.
* Improve date display.
  `-> Just print year when months & days are 0s.
  `-> "~" instead of "abt"
  `-> figure out difference between "est" and "abt"
  `-> how to do ranges?
  `-> maybe distinguish dead & unknown death date from not dead?
      ? for dead & unknown, - for not dead (or maybe not dead)
* Stats like total people & unique surnames.
* Fill out the Person page.
* Sources page? Events page? Tree browser?
