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

BOOK_TITLE = "Pact"
DATA = pathlib.Path(f"data/{BOOK_TITLE}")

# NOTE: Pale is not yet finished
first_chapters = {
    "Worm": "https://parahumans.wordpress.com/2011/06/11/1-1/",
    "Pact": "https://pactwebserial.wordpress.com/2013/12/17/bonds-1-1/",
    "Twig": "https://twigserial.wordpress.com/2014/12/24/taking-root-1-1/",
    "Ward": "https://www.parahumans.net/2017/10/21/glow-worm-0-1/",
    "Pale": "https://palewebserial.wordpress.com/2020/05/05/blood-run-cold-0-0/",
}

# Set to True if you want to skip already downloaded files
skip_downloaded = False

#############
# FUNCTIONS #
#############

def modify_interlude_title(book_title: str, chapter_title: str) -> str:
    """TODO

    Args:
        book_title: The title of the book. Should always be the parameter BOOK_TITLE but who knows
        chapter_title: The title of the chapter contained on one webpage. If it is a normal title,
            it will have the format of f"{arc name} {arc #}.{chapter #}". If it is an interlude,
            it varies quite a bit

    Returns:
        The name of the chapter, depending on if it is a normal chapter or an interlude chapter
    """
    if book_title == "Worm":
        if "Interlude" in chapter_title:
            return "Interlude"
        return chapter_title

    elif book_title == "Pact":
        if "Pages" in chapter_title:
            return "Pages"
        if "Histories" in chapter_title:
            return "Histories"
        # The numbering is messed up for this chapter
        # It actually is not, this chapter skip was intentaional on part of the author to note that
        # time was skipped
        if chapter_title == "Subordination 6.12":
            pass
            # return "Subordination 6.11"
        return chapter_title

def update_arc_chapter(
    book_title: str, chapter_title: str, current_arc: int, current_chapter: int) -> (int, int):
    """TODO

    Args:
        book_title: The title of the book. Should always be the parameter BOOK_TITLE but who knows
        chapter_title: The title of the chapter contained on one webpage. If it is a normal title,
            it will have the format of f"{arc name} {arc #}.{chapter #}". If it is an interlude,
            it varies quite a bit

    Returns:
        The name of the chapter, depending on if it is a normal chapter or an interlude chapter
    """

    # Process Worm
    if book_title == "Worm":

        # The "e." chapters are the epilogue chapters
        if "e." in title:
            if current_arc != 31:
                return 31, 1
            else:
                return 31, current_chapter + 1
        if chapter_title == "Interlude":
            return current_arc, current_chapter + 1

        # Get the current arc number from the title
        arc_number = int(chapter_title.split(" ")[-1].split(".")[0])

        if arc_number != current_arc:
            return arc_number, 1
        else:
            return current_arc, current_chapter + 1

    # Process Pact
    elif book_title == "Pact":
        
        # The epilogue chapter is obviously the epilogue (only one in Pact)
        if "Epilogue" in title:
            return 17, 1
        if chapter_title == "Pages" or chapter_title == "Histories":
            return current_arc, current_chapter + 1

        # Get the current arc number from the title
        arc_number = int(chapter_title.split(" ")[-1].split(".")[0])

        if arc_number != current_arc:
            return arc_number, 1
        else:
            return current_arc, current_chapter + 1

########
# CODE #
########

# Verify the input BOOK_TITLE is valid
if not BOOK_TITLE in first_chapters.keys():
    raise ValueError

################################
# GET ALL THE INDIVIDUAL PAGES #
################################

# Create the "data/" folder if it doesn't exist
if not os.path.exists(DATA):
    os.makedirs(DATA)

# Sometimes, we want to skip multiple chapters in a row
skip_n = 0

# Keep track of the arc/chapter numbers. Sometimes, there are interludes in the middle of the 
# arc making numbering somewhat inconsistent
arc = 1
chapter = 0

n = 0

# Repeat until all pages are downloaded
next_page = first_chapters[BOOK_TITLE]
while True:

    # Get the contents of the webpage
    r = requests.get(next_page)
    soup = bs4.BeautifulSoup(r.text, "html5lib")

    # Filter to only the actual content (remove headers and comments)
    soup.find("div", id="comments").decompose()

    # Get the title of the chapter
    for h1 in soup.findAll("h1"):

        # Ignore some other header stuff
        if "navigation" in h1.text:
            continue
        
        # Special Pact override
        if BOOK_TITLE == "Pact" and arc == 1 and chapter == 0:
            title = "Bonds 1.1"
            break

        title = h1.text

    # If the title of the chapter is an interlude, then some additional modifications have to be
    # done.
    title = modify_interlude_title(BOOK_TITLE, title)

    # Based on the title of the chapter, the arc/chapter numbers may need to be updated
    arc, chapter = update_arc_chapter(BOOK_TITLE, title, arc, chapter)

    # Write the contents to a local file
    fn = f"{str(arc).zfill(2)}.{str(chapter).zfill(2)} {title}.md"

    # Skip if the file already exists and the setting is set
    if (DATA / fn).is_file() and skip_downloaded:
        print(f"Skipped {fn}")

    # Download otherwise
    else:
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
                    skip_n = 1
                    continue
                elif skip_n > 0:
                    skip_n -= 1
                    continue

                # Do some additonal processing on the text
                text = ""
                for fragment in p.contents:

                    # Replace all images with the alternate text
                    if fragment.name == "img":
                        print("WARNING: IMAGE FOUND")
                        text += fragment["alt"]

                    # Otherwise just add the content
                    else:
                        text += str(fragment)

                # If the text contains only the character "■", we leave it as is. This is typically
                # used in the middle of a chapter to denote a major setting shift (usually
                # flashback kind of stuff) or a POV change (like in some interludes)
                if text.strip() == "■":
                    f.write(text + "\n\n")
                    continue

                # Replace double spaces with single spaces
                text = text.replace("\xa0", " ")
                text = text.replace("  ", " ")

                # Before fixing italicize and bold, escape any current * characters
                text = text.replace("*", "\\*")

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
                        # text = text.replace("<br/>\n", "\n> ")

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

#######################################
# Combine all the pages into one EPUB #
#######################################

# Create the mega md document
mgra_md = DATA.parent / f"{BOOK_TITLE}.md"
with open(mgra_md, "w", encoding="utf8") as f:

    # Get all the files to combine together
    files = DATA.glob("**/*")

    # Append all the files together
    for file in files:

        # Open one of the md files
        with open(file, "r", encoding="utf8") as to_append: 
            f.write(to_append.read())
            f.write("\n")

# Create the metadata file
meta = DATA.parent / f"{BOOK_TITLE}_meta.txt"
with open(meta, "w", encoding="utf8") as f:
    f.write(textwrap.dedent(f"""
        ---
        title: {BOOK_TITLE}
        author: John "Wildbow" McCrae
        language: en-US
        ---"""))

# Call pandoc to combine the data together
subprocess.run(f"pandoc {mgra_md} -o {BOOK_TITLE}.epub --metadata-file={meta}", shell=True)