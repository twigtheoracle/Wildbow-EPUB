# Eric Liu
# 2023-04-29

###########
# IMPORTS #
###########

import pandoc
import pathlib

import textwrap

##########
# CONFIG #
##########

DATA = pathlib.Path("data/")

#############
# FUNCTIONS #
#############

# Nothing :(

########
# CODE #
########

# Create the mega markdown document
with open("Worm.md", "w", encoding="utf8") as f:

    # Get all the files to combine together
    files = DATA.glob("**/*")

    # Append all the files together
    for file in files:

        # Open one of the markdown files
        with open(file, "r", encoding="utf8") as to_append: 

            f.write(to_append.read())

# Create the metadata file
with open("meta.txt", "w", encoding="utf8") as f:
    f.write(textwrap.dedent("""\
        ---
        title: Worm
        author: John "Wildbow" McCrae
        language: en-US
        ---"""))