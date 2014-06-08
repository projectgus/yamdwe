import re, string, dokuwiki

def convert_pagecontent(content):
    """
    Convert a string in Mediawiki content format to a string in
    Dokuwiki content format.
    """
    content = _convert_tables(content)
    for (search, replace) in PATTERNS:
        content = re.sub(search, replace, content)
    return content

def _convert_tables(content):
    """
    Convert simple wikitables to dokuwiki tables, in a fairly braindead way (not a proper parser)

    Doesn't support || or | single row syntax yet, will probably mangle multirow cells
    """
    table = None
    row = None
    output = []
    for line in content.split("\n"):
        if table is None: # not in a table
            if line.startswith("{|"):
                table = []
                row = []
            else:
                output.append(line)
        else: # in a table
            if line.startswith("|-"): # new row
                if row is not None:
                    table.append(row)
                row = []
            elif line.startswith("|}"): # end of table
                table.append(row)
                # output table in dokuwiki format
                for row in table:
                    output.append("|%s|" % "|".join(cell.ljust(16) for cell in row))
                row = None
                table = None
            elif line.startswith("|") or line.startswith("!"): # cell or header
                row.append(line[1:])
            else: # don't know what this is(!), probably a multirow cell(?) so add to previous cell
                row[-1] += line
    return "\n".join(output)

RE_MW_IMG_SCALE =  re.compile(r'\|x?(\d+(x\d+)?)px(\||$)')
RE_MW_IMG_CENTER = re.compile(r'\|center(\||$)')
RE_MW_IMG_LEFT =   re.compile(r'\|left(\||$)')
RE_MW_IMG_RIGHT =  re.compile(r'\|right(\||$)')

def convert_image_embed(match):
    """
    Convert an embedded image from a mediawiki embed to a dokuwiki embed (matched by patterns below)

    Also matches some simpl embedding formats
    """
    imagename = dokuwiki.clean_id(match.group(1), keep_slashes=True)
    options = match.group(2)

    if options is None:
        options = ""

    # look for size options
    width_suffix = ""
    # dokuwiki doesn't support by-height scaling, this gets translated as a by-width scale
    match = re.search(RE_MW_IMG_SCALE, options)
    if match is not None:
        width_suffix = "?%s" % (match.group(1))

    # look for alignment options
    align_pre = ""
    align_post = ""
    if re.search(RE_MW_IMG_CENTER, options):
        align_pre = " "
        align_post = " "
    elif re.search(RE_MW_IMG_LEFT, options):
        align_post = " "
    elif re.search(RE_MW_IMG_RIGHT, options):
        align_pre = " "

    return "{{%sfile:%s%s%s}}" % (align_pre, imagename, width_suffix, align_post)

def convert_heading(match):
    level = min(len(match.group(1)), 5)
    syntax = "="*(6-level) # dokuwiki is opposite, more =s for higher level headings
    title = match.group(2)
    return "%s %s %s" % (syntax, title, syntax)

"""
    Most of the regex patterns and replacements used here were originally written as Perl oneliners
    by Johannes Buchner <buchner.johannes [at] gmx.at>

    Tuples are ( <regex to search for>, <replacement> ) as arguments to re.sub()
"""
PATTERNS = [
    # Headings
    (r'^([=]+) *([^=]+) *[=]+ *$', convert_heading),
    (r'</?h1>', '======'),
    (r'</?h2>', '====='),
    (r'</?h3>', '===='),
    (r'</?h4>', '==='),
    (r'</?h5>', '=='),
    (r'</?h6>', '='),

    # lists
    (r'^[\*#]{4}\*', '          * '),
    (r'^[\*#]{3}\*', '        * '),
    (r'^[\*#]{2}\*', '      * '),
    (r'^[\*#]{1}\*', '    * '),
    (r'^\*', '  * '),
    (r'^[\*#]{4}#', '          - '),
    (r'^[\*\#]{3}\#', '      - '),
    (r'^[\*\#]{2}\#', '    - '),
    (r'^[\*\#]{1}\#', '  - '),
    (r'^\#', '  - '),

    #[link] => [[link]]
    (r'([^\[])\[([^\[])', '\\1[[\\2'),
    (r'^\[([^\[])', '[[\\1'),
    (r'([^\]])\]([^\]])', '\\1]]\\2'),
    (r'([^\]])\]$', '\\1]]'),

    #[[File:image]] => {{file:image}}
    (r'\[\[File:(.+?)(\|(.*))?\]\]', convert_image_embed),

    #[Category:blah] => Nothing (could convert to the 'tag' plugin format if necessary)
    (r'\[\[Category:(.+?)\]\]', ''),

    #[[url text]] => [[url|text]]
    (r'(\[\[[^| \]]*) ([^|\]]*\]\])', '\\1|\\2'),

    # bold, italic
    (r"'''", "**"),
    (r"''", r"\\"),

    # preformatted
    (r"^ (.+)$", r'  \1'),

    # talks
    (r"^[ ]*:", ">"),
    (r">:", ">>"),
    (r">>:", ">>>"),
    (r">>>:", ">>>>"),
    (r">>>>:", ">>>>>"),
    (r">>>>>:", ">>>>>>"),
    (r">>>>>>:", ">>>>>>>"),

    (r"<pre>", "<code>"),
    (r"</pre>", "</code>"),
    ]
# precompile the regexes we're searching for
PATTERNS = [ (re.compile(search, re.MULTILINE), replace) for (search, replace) in PATTERNS]

