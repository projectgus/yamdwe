import re, string

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
                row = None
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

"""
    The regex patterns and replacements used here were originally written as Perl oneliners
    by Johannes Buchner <buchner.johannes [at] gmx.at>

    Tuples are ( <regex to search for>, <replacement> ) as arguments to re.sub()
"""
PATTERNS = [
    # Headings
    (r'^[ ]*=([^=])', '<h1> \\1'),
    (r'([^=])=[ ]*$', '\\1 </h1>'),
    (r'^[ ]*==([^=])', '<h2> \\1'),
    (r'([^=])==[ ]*$', '\\1 </h2>'),
    (r'^[ ]*===([^=])', '<h3> \\1'),
    (r'([^=])===[ ]*$', '\\1 </h3>'),
    (r'^[ ]*====([^=])', '<h4> \\1'),
    (r'([^=])====[ ]*$', '\\1 </h4>'),
    (r'^[ ]*=====([^=])', '<h5> \\1'),
    (r'([^=])=====[ ]*$', '\\1 </h5>'),
    (r'^[ ]*======([^=])', '<h6> \\1'),
    (r'([^=])======[ ]*$', '\\1 </h6>'),


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
    (r'^[\*#]{4}#', '          \- '),
    (r'^[\*\#]{3}\#', '      \- '),
    (r'^[\*\#]{2}\#', '    \- '),
    (r'^[\*\#]{1}\#', '  \- '),
    (r'^\#', '  - '),

    #[link] => [[link]]
    (r'([^\[])\[([^\[])', '\\1[[\\2'),
    (r'^\[([^\[])', '[[\\1'),
    (r'([^\]])\]([^\]])', '\\1]]\\2'),
    (r'([^\]])\]$', '\\1]]'),


    #[[url text]] => [[url|text]]
    (r'(\[\[[^| \]]*) ([^|\]]*\]\])', '\\1|\\2'),

    # bold, italic
    (r"'''", "**"),
    (r"''", r"\\"),

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
PATTERNS = [ (re.compile(search), replace) for (search, replace) in PATTERNS]

