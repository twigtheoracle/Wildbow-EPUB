# Eric Liu
# 2023-04-29

###########
# IMPORTS #
###########

import bs4
import requests 
import re
import textwrap

import os
import pathlib
import subprocess

##########
# CONFIG #
##########

first_chapter = "https://parahumans.wordpress.com/2011/06/11/1-1/"

DATA = pathlib.Path("data/Worm/")

#############
# FUNCTIONS #
#############

# Nothing :(

########
# CODE #
########

################################
# Get all the individual pages #
################################

# Create the "data/" folder if it doesn't exist
if not os.path.exists(DATA):
    os.makedirs(DATA)

# Keep track of the arc/chapter numbers. Sometimes, there are interludes in the middle of the 
# arc making numbering somewhat inconsistent
arc = 1
chapter = 0

# Sometimes, we want to skip two lines instead of one. Use this flag
skip_two = False

# Repeat until all pages are downloaded
next_page = first_chapter
while True:

    # Get the contents of the webpage
    r = requests.get(next_page)
    soup = bs4.BeautifulSoup(r.text, "html5lib")

    # Filter to only the actual content (remove headers and comments)
    soup.find("div", id="comments").decompose()

    # Get the title of the chapter
    for h1 in soup.findAll("h1"):
        title = h1.text

    # If the title is an interlude, we don't care about the interlude number
    if "Interlude" in title:
        title = "Interlude"

    # Update the arc number if necessary
    if title != "Interlude" and ("e." in title or int(title.split(" ")[1].split(".")[0]) != arc):
        if "e." in title:
            if arc != 31:
                arc = 31
                chapter = 1
            else:
                chapter += 1
        else:
            arc = int(title.split(" ")[1].split(".")[0])
            chapter = 1
    else:
        chapter += 1

    # Write the contents to a local file
    fn = f"{str(arc).zfill(2)}.{str(chapter).zfill(2)} {title}.html"
    with open(DATA / fn, "w", encoding="utf8") as f:

        print(fn)

        # # Write the chapter title first
        f.write(f"<h1>{title}</h1>\n")

        # Filter the contents to p tags
        for p in soup.findAll("p"):

            # Ignore some meta text stuff
            if "Next Chapter" in p.text or "Last Chapter" in p.text:
                continue
            elif p.text.startswith("Brief note from the author:"):
                skip_two = True
                continue
            elif skip_two:
                skip_two = False
                continue

            f.write(str(p))
            f.write("\n")

    # Find the next page
    next_page = None
    for a in soup.find_all("a"):
        if a.text.strip() == "Next Chapter":
            next_page = a["href"]

    # If no next page can be found, stop iterating
    if next_page is None:
        break

#######################################
# Combine all the pages into one EPUB #
#######################################

# Create the mega html document
mega_html = DATA.parent / "Worm.html"
with open(mega_html, "w", encoding="utf8") as f:

    # Get all the files to combine together
    files = DATA.glob("**/*")

    # Append all the files together
    for file in files:

        # Open one of the html files
        with open(file, "r", encoding="utf8") as to_append: 
            f.write(to_append.read())
            f.write("\n")

# Create the metadata file
meta = DATA.parent / "Worm_meta.txt"
with open(meta, "w", encoding="utf8") as f:
    f.write(textwrap.dedent("""\
        ---
        title: Worm
        author: John "Wildbow" McCrae
        language: en-US
        ---"""))

# Call pandoc to combine the data together
subprocess.run(f"pandoc {mega_html} -o Worm.epub --metadata-file={meta}", shell=True)