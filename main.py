# Eric Liu
# 2023-04-29

###########
# IMPORTS #
###########

import bs4
import requests 
import re

import os
import pathlib

##########
# CONFIG #
##########

first_chapter = "https://parahumans.wordpress.com/2011/06/11/1-1/"

DATA = pathlib.Path("data/")

#############
# FUNCTIONS #
#############

# Nothing :(

########
# CODE #
########

# Create the "data/" folder if it doesn't exist
if not os.path.exists(DATA):
    os.makedirs(DATA)

# Keep track of the arc/chapter numbers. Sometimes, there are interludes in the middle of the 
# arc making numbering somewhat inconsistent
arc = 1
chapter = 0

n = 0

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
    fn = f"{str(arc).zfill(2)}.{str(chapter).zfill(2)} {title}.md"
    with open(DATA / fn, "w", encoding="utf8") as f:

        print(fn)

        # Write the chapter title first
        f.write(f"# {title}\n\n")

        # Filter the contents to p tags
        for p in soup.findAll("p"):

            # Ignore some meta text stuff
            if "Next Chapter" in p.text or "Last Chapter" in p.text:
                continue
            elif p.text.startswith("Brief note from the author:"):
                continue
            elif p.text == "■":
                continue

            # Do some additonal processing on the text
            text = ""
            for fragment in p.contents:
                text += str(fragment)

            # Replace double spaces with single spaces
            text = text.replace("\xa0", " ")
            text = text.replace("  ", " ")

            # Before fixing italicize and bold, escape any current * characters
            text = text.replace("*", "\\*")

            # Replace italicize
            text = text.replace("<em> ", " *")
            text = text.replace("<em>", "*")
            text = text.replace(" </em>", "* ")
            text = text.replace("</em>", "*")

            # Replace bold
            text = text.replace("<strong> ", " **")
            text = text.replace("<strong>", "**")
            text = text.replace(" </strong>", "** ")
            text = text.replace("</strong>", "**")

            # Replace weird indentation with more standard indentation
            text = text.replace("■", "-")

            # Sometimes, text is indented in using padding-left. Instead, we will use ">" in
            # markdown
            tag_style = p.attrs.get("style")
            if tag_style is None:
                pass
            else:
                if "padding-left" in tag_style:
                    f.write("> ")
                    text = text.replace("<br/>\n", "\n> ")

            # Remove extra whitespace
            text = text.strip()

            # Write to file
            f.write(text + "\n\n")

    # Find the next page
    next_page = None
    for a in soup.find_all("a"):
        if a.text.strip() == "Next Chapter":
            next_page = a["href"]

    # If no next page can be found, stop iterating
    if next_page is None:
        break