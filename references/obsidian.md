# Property format

Properties are stored in YAML format at the top of the file. YAML is a popular format that is easy for both humans and computers to read.

Property names are separated from their values by a colon followed by a space:

---
name: value
---

While the order of each name-value pair doesn't matter, each name must be unique within a note. For example, you can't have more than one tags property.

Values can be text, numbers, true or false, or even collections of values (arrays).

---
title: A New Hope # This is a text property
year: 1977
favorite: true
cast: # This is a list property
  - Mark Hamill
  - Harrison Ford
  - Carrie Fisher
---

Internal links in Text and List type properties must be surrounded with quotes. Obsidian will automatically add these if you manually enter internal links into properties, but be careful to add them when using templating plugins.

---
link: "[[Link]]" 
linklist: 
  - "[[Link]]" 
  - "[[Link2]]"
---

Number type properties must always be an integer. The integer may contain decimal points, but not operators.

---
year: 1977
pie: 3.14
---

Checkbox type properties are either true or false. An empty property will be treated as false. In Live Preview, this will be represented as a checkbox.

---
favorite: true
reply: false
last: # this will default to false

Date and Date & time type properties are stored in the following format:

---
date: 2020-08-21
time: 2020-08-21T10:30:00
---

The date picker follows your operating system's default date and time format.

