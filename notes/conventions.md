## Gramps Conventions
#### Introduction
This software makes certain assumptions about the conventions followed by a Gramps family tree. For example, some fields are expected to have a limited range of values. Here, we attempt to list these assumptions, so that they can be followed by users of the software, or torn out by anyone who wishes to adapt the software for their own tree. I THINK the software is flexible enough that it'll still work even when the conventions aren't followed; if not, then it counts as a bug.

#### Sources and citations
Sources are expected to have a Quality attribute. It can have one of the following values:

* good
* fine
* mediocre

If the Quality attribute is missing, or has an unknown value, it'll default to Mediocre. The meaning of these terms is somewhat arbitrary. I usually assign "good" to written documents like censuses; "fine" to individuals that I've spoken to, and to certain websites (like memorial sites); and "mediocre" for public family trees that you find on the likes of Ancestry (since the owners of these trees usually aren't too scrupulous about what they add to them).

Sources can also have a description, contained in a single "Note". If there are multiple Notes, then only the first one will be used.

People, events, families, description attributes, and names can all have sources associated with them.

Individual citations can have a short description under the Volume/Page field. This description will be shown in the citations section at the bottom of the page where the citation is used, like you'd see on Wikipedia. Not ideal to put the description under Volume/Page, since it might actually be used for its intended purpose of recording the volume/page...

#### Biographical notes
People can have biographical notes, in the form of Description attributes. The attribute values can contain arbitrary HTML. I mostly use the HTML formatting to separate the descriptions into paragraphs (with the p element), for extended quotes (blockquote element), and for web links (with the 'a' element). 

#### Names
People can have multiple names. In my tree, I manually add a Married name for married women who take their husband's surname. The Title and Type fields are also extracted for each name.

#### Events
Events can contain a description under, well, the Description field. (If needed, I could allow them to have a Description attribute for more extended descriptions). Their location can be provided under the Place field; only the Name of the place is used.

#### Families
In the case of families, a citation/source is intended to provide evidence for the membership of the family (in the case of a marriage relationship, it can also be evidence for the marriage taking place). I haven't decided how to provide more granular sourcing, e.g. we might use one source to prove that a couple got married, and another source to prove that some of the family's children, and another source for the rest of the family.

Families can have Description attributes just like People can.

#### Dates
Various Date types are supported: Regular, Range, Text-only, After, Before, and About.
