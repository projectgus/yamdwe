import re

def convert_pagecontent(content):
    """
    Convert a string in Mediawiki content format to a string in
    Dokuwiki content format.
    """
    for (search, replace) in PATTERNS:
        content = re.sub(search, replace, content)
    return content

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
print([x for x in PATTERNS if len(x) != 2])
PATTERNS = [ (re.compile(search), replace) for (search, replace) in PATTERNS]

