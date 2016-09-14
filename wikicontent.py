"""
Methods for converting Mediawiki content to the Dokuwiki format.

Uses mwlib to parse the Mediawiki markup.

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import re, string, dokuwiki, visitor
from mwlib.parser import *
from mwlib import uparser

# Regex to match any known File: namespace (can be updated based on the mediawiki installation language)
mw_file_namespace_aliases = re.compile("^(Image|File):", re.IGNORECASE)
dw_file_namespace = "File:"

def set_file_namespaces(canonical_alias, aliases):
    """
    Allow the mediawiki parser to match localised namespaces for files/images

    Arguments:
    canonical_alias is the single namespace that dokuwiki will use (default File:)
    aliases is a list of alternative namespace names that will be converted to the canonical alias
    """
    global mw_file_namespace_aliases
    global dw_file_namespace
    dw_file_namespace = canonical_alias + ":"
    mw_file_namespace_aliases = re.compile("^(%s):" % "|".join(aliases), re.IGNORECASE)

def is_file_namespace(target):
    """
    Is this target URL part of a known File or Image path?
    """
    return re.match(mw_file_namespace_aliases, target)

def canonicalise_file_namespace(target):
    """
    Convert any known File: or Image: (or alias) namespace link to be File:
    ... mediawiki stores all these under a common namespace, so dokuwiki has no choice but to import
    them all under a single canonical
    """
    return re.sub(mw_file_namespace_aliases, dw_file_namespace, target)

def convert_pagecontent(title, content):
    """
    Convert a string in Mediawiki content format to a string in
    Dokuwiki content format.
    """

    # this is a hack for mwlib discarding the content of <nowiki> tags
    # and replacing them with plaintext parsed HTML versions of the
    # content (pragmatic, but not what we want)
    nowiki_plaintext = []

    # Instead we save the content here, replace it with the "magic" placeholder
    # tag <__yamdwe_nowiki> and the index where the content was saved, then pass
    # the list of nowiki content into the parser as context.
    def add_nowiki_block(match):
        nowiki_plaintext.append(match.group(0))
        return "<__yamdwe_nowiki>%d</__yamdwe_nowiki>" % (len(nowiki_plaintext)-1,)
    content = re.sub(r"<nowiki>.+?</nowiki>", add_nowiki_block, content)

    root = uparser.parseString(title, content) # create parse tree
    context = {}
    context["list_stack"] = []
    context["nowiki_plaintext"] = nowiki_plaintext # hacky way of attaching to child nodes
    result = convert(root, context, False)

    # mwlib doesn't parse NOTOC, so check for it manually
    if re.match(r"^\s*__NOTOC__\s*$", content, re.MULTILINE):
        result = "~~NOTOC~~"+("\n" if not result.startswith("\n") else "")+result
    return result

def convert_children(node, context):
    """Walk the children of this parse node and call convert() on each.
    """
    result = ""
    for child in node.children:
        res = convert(child, context, result.endswith("\n"))
        if type(res) is str:
            res = unicode(res)
        if type(res) is not unicode:
            print("Got invalid response '%s' when processing '%s'" % (res,child))
        result += res
    return result

@visitor.when(Article)
def convert(node, context, trailing_newline):
    return convert_children(node, context)

@visitor.when(Paragraph)
def convert(node, context, trailing_newline):
    return convert_children(node, context) + "\n"

@visitor.when(Text)
def convert(text, context, trailing_newline):
    if text._text is None:
        return ""
    m = re.match(r"<__yamdwe_nowiki>([0-9]+)</__yamdwe_nowiki>", text._text)
    if m is not None: # nowiki content!
        index = int(m.group(1))
        return context["nowiki_plaintext"][index] # nowiki_plaintext entry includes <nowiki> tags
    else:
        return text.caption

@visitor.when(Section)
def convert(section, context, trailing_newline):
    result = ""
    if section.tagname == "p":
        pass
    elif section.tagname == "@section":
        level = section.level
        heading = convert(section.children.pop(0), context, trailing_newline).strip()
        heading_boundary = "="*(8-level)
        result = "\n%s %s %s\n" % (heading_boundary, heading, heading_boundary)
    else:
        print("Unknown tagname %s" % section.tagname)

    return result + convert_children(section, context)

@visitor.when(Style)
def convert(style, context, trailing_newline):
    formatter = {
        ";" :  ("**", r"**\\"),     # definition (essentially boldface)
        "''" : ("//", "//"),        # italics
        "'''" :("**", "**"),        # boldface
        ":"   : ("", ""),           # other end of a definition???
        "sub" : ("<sub>","</sub>"),
        "sup" : ("<sup>","</sup>"),
        "big" : ("**", "**"),       # <big> not in dokuwiki so use bold
        "-" : ("<blockquote>", "</blockquote>"), # use dokuwikis Blockquote Plugin for this
        "u" : ("", "")              # <br> already handled in TagNode @visitor
        }.get(style.caption, None)
    if formatter is None:
        print("WARNING: Ignoring unknown formatter %s" % style.caption)
        formatter = ("","")
    return formatter[0] + convert_children(style, context) + formatter[1]

@visitor.when(NamedURL)
def convert(url, context, trailing_newline):
    text = convert_children(url, context).strip(" ")
    url = url.caption
    if len(text):
        return u"[[%s|%s]]" % (url, text)
    else:
        return u"%s" % (url)

@visitor.when(URL)
def convert(url, context, trailing_newline):
    return url.caption

@visitor.when(ImageLink)
def convert(link, context, trailing_newline):
    suffix = ""
    if link.width is not None:
        if link.height is None:
            suffix = "?%s" % link.width
        else:
            suffix = "?%sx%s" % (link.width, link.height)
    else:
        try:
            if link.in_gallery: # see below for Tag->gallery handling
                suffix = "?160" # gallery images should be thumbnailed
        except AttributeError:
            pass # not in a gallery
    prealign = " " if link.align in [ "center", "right" ] else ""
    postalign = " " if link.align in [ "center", "left" ] else ""
    target = canonicalise_file_namespace(link.target)
    target = convert_internal_link(target)
    return "{{%s%s%s%s}}" % (prealign, target, suffix, postalign)

@visitor.when(ArticleLink)
def convert(link, context, trailing_newline):
    text = convert_children(link, context).strip(" ")
    pagename = convert_internal_link(link.target)
    if len(text):
        return u"[[%s|%s]]" % (pagename, text)
    else:
        return u"[[%s]]" % pagename

@visitor.when(CategoryLink)
def convert(link, context, trailing_newline):
    # Category functionality can be implemented with plugin:tag, but not used here
    return ""

@visitor.when(NamespaceLink)
def convert(link, context, trailing_newline):
    if is_file_namespace(link.target): # is a link to a file or image
        filename = dokuwiki.make_dokuwiki_pagename(canonicalise_file_namespace(link.target))
        caption = convert_children(link, context).strip()
        if len(caption) > 0:
            return u"{{%s%s}}" % (filename, caption)
        else:
            return u"{{%s}}" % filename

    print("WARNING: Ignoring namespace link to " + link.target)
    return convert_children(link, context)


@visitor.when(ItemList)
def convert(itemlist, context, trailing_newline):
    context["list_stack"].append("* " if itemlist.tagname == "ul" else "- ")
    converted_list = convert_children(itemlist, context)
    context["list_stack"].pop()
    return converted_list

@visitor.when(Item)
def convert(item, context, trailing_newline):
    item_content = convert_children(item, context)
    list_stack = context["list_stack"]
    return "  "*len(list_stack) + list_stack[-1] + item_content

@visitor.when(Table)
def convert(table, context, trailing_newline):
    # we ignore the actual Table tags, instead convert each Row & Cell individually
    return convert_children(table, context)

@visitor.when(Cell)
def convert(cell, context, trailing_newline):
    marker = "^" if cell.tagname == "th" else "|"
    result = u"%s %s" % (marker, convert_children(cell, context).replace('\n','').strip())
    return result

@visitor.when(Row)
def convert(row, context, trailing_newline):
    return convert_children(row, context) + " |\n"

@visitor.when(PreFormatted)
def convert(pre, context, trailing_newline):
    in_list = len(context["list_stack"]) > 0
    if trailing_newline and not in_list: # in its own paragraph, use a two space indent
        return "  " + convert_children(pre, context).replace("\n","\n  ").strip(" ")
    else: # inline in a list or a paragraph body, use <code> tags
        return "<code>" + convert_children(pre, context) + "</code>"

@visitor.when(TagNode)
def convert(tag, context, trailing_newline):
    # dict maps mediawiki tag name to tuple of starting, ending dokuwiki tag
    simple_tagitems = {
        "tt" : ("''", "''"),
        "ref" : ("((","))"), # references converted to footnotes
        "code" : ("<code>","</code>"),
    }
    if tag.tagname in simple_tagitems:
        pre,post = simple_tagitems[tag.tagname]
        return pre + convert_children(tag, context) + post
    elif tag._text is not None:
        if tag._text.replace(" ","").replace("/","") == "<br>":
            return "\n" # this is a oneoff hack for one wiki page covered in <br/>
        return tag._text # may not work for non-selfclosing tags
    elif tag.tagname == "gallery":
        # with a lot of cleverness we could use the gallery plugin for this,
        # but this should do. We flag each child image as in the gallery, then
        # deal with the ImageLinks above
        for child in tag.children:
            child.in_gallery = True
    elif tag.tagname == "references":
        print("WARNING: <references> tag has no equivalent in Dokuwiki, ignoring...")

    return convert_children(tag, context)

@visitor.when(Math)
def convert(node, context, trailing_newline):
    """
    Convert <math></math> tags for rendering of math terms
    there are a couple of extension to support this in dokuwiki
    tested successfully with MathJax plugin
    """
    if "\n" in node.math:
        # multiple lines are a formula block
        return "$$" + node.math + "$$"
    # anything else is inline term
    return "$" + node.math + "$"

# catchall for Node, which is the parent class of everything above
@visitor.when(Node)
def convert(node, context, trailing_newline):
    if node.__class__ != Node:
        print("WARNING: Unsupported node type: %s" % (node.__class__))
    return convert_children(node, context)

def convert_internal_link(mw_target):
    """
    Convert an internal Mediawiki link, with or without an anchor # in the middle.

    Same as converting a plain pagename, only we want to preserve any #s in the target text.
    """
    if "#" in mw_target:
        page,anchor = mw_target.split("#",1)
    else:
        page = mw_target
        anchor = None
    if len(page):
        page = dokuwiki.make_dokuwiki_pagename(page)
    if anchor is not None:
        page = page + "#" + dokuwiki.make_dokuwiki_heading_id(anchor)
    return page
