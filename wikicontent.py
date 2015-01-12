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
    print("match localised namespaces for files/images %s <- %s"%(canonical_alias,aliases))
    global mw_file_namespace_aliases
    global dw_file_namespace
    dw_file_namespace = canonical_alias + ":"
    mw_file_namespace_aliases = re.compile("^(%s):" % "|".join([canonical_alias]+aliases), re.IGNORECASE)

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
    # wrap the "magic" marker tag <__mw_nowiki> around <nowiki>, as
    # as mwlib just discards it otherwise and we can't detect it within the parser.
    # We keep the inner <nowiki> so the mwlib parser still skips that content
    content = re.sub(r"<nowiki>.+</nowiki>", lambda e: "<__mw_nowiki>"+e.group(0)+"</__mw_nowiki>", content)

    root = uparser.parseString(title, content) # create parse tree
    return convert(root, False)

def convert_children(node):
    """Walk the children of this parse node and call convert() on each.
    """
    result = ""
    for child in node.children:
        res = convert(child, result.endswith("\n"))
        if type(res) is str:
            res = unicode(res)
        if type(res) is not unicode:
            print("Got invalid response '%s' when processing '%s'" % (res,child))
        result += res
    return result

@visitor.when(Article)
def convert(node, trailing_newline):
    return convert_children(node)

@visitor.when(Paragraph)
def convert(node, trailing_newline):
    return convert_children(node) + "\n"

@visitor.when(Text)
def convert(text, trailing_newline):
    magic_nw_tag = "<__mw_nowiki>"
    if text._text == magic_nw_tag:
        has_trailing_newline = (text.caption[-1] == '\n')
        suffix = ""
        if has_trailing_newline:
            text.caption = text.caption[:-1]
            suffix = "\n"
        return "<nowiki>" + text.caption[len(magic_nw_tag):-1-len(magic_nw_tag)] + "</nowiki>" + suffix
    else:
        return text.caption

@visitor.when(Section)
def convert(section, trailing_newline):
    result = ""
    if section.tagname == "p":
        pass
    elif section.tagname == "@section":
        level = section.level
        heading = convert(section.children.pop(0), trailing_newline)
        #highest level dokuwiki is six ='s, ->_7_-1
        heading_boundary = "="*(7-level)
        result = "\n%s %s %s\n" % (heading_boundary, heading, heading_boundary)
    else:
        print("Unknown tagname %s" % section.tagname)

    return result + convert_children(section)

@visitor.when(Style)
def convert(style, trailing_newline):
    formatter = {
        ";" :  ("**", r"**\\"),     # definition (essentially boldface)
        "''" : ("//", "//"),        # italics
        "'''" :("**", "**"),        # boldface
        ":"   : ("", ""),           # other end of a definition???
        "sub" : ("<sub>","</sub>"),
        "sup" : ("<sup>","</sup>"),
        "big" : ("**", "**"),        # <big> not in dokuwiki so use bold
        }.get(style.caption, None)
    if formatter is None:
        print("WARNING: Ignoring unknown formatter %s" % style.caption)
        formatter = ("","")
    return formatter[0] + convert_children(style) + formatter[1]

@visitor.when(NamedURL)
def convert(url, trailing_newline):
    text = convert_children(url).strip(" ")
    url = url.caption
    if len(text):
        return "[[%s|%s]]" % (url, text)
    else:
        return "%s" % (url)

@visitor.when(URL)
def convert(url, trailing_newline):
    print(' ... converting URL %s'%url.caption)
    return url.caption

@visitor.when(ImageLink)
def convert(link, trailing_newline):
    print(' ... converting %s'%link.target)
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
    target = ":".join(convert_internal_link(tg) for tg in target.split(":"))
    return "{{%s%s%s%s}}" % (prealign, target, suffix, postalign)

@visitor.when(ArticleLink)
def convert(link, trailing_newline):
    print(' ... converting %s'%link.target)
    text = convert_children(link).strip(" ")
    pagename = convert_internal_link(link.target)
    if len(text):
        return "[[%s|%s]]" % (pagename, text)
    else:
        return "[[%s]]" % pagename

@visitor.when(CategoryLink)
def convert(link, trailing_newline):
    print(' ... converting %s'%link.target)
    # Category functionality can be implemented with plugin:tag, but not used here
    return ""

@visitor.when(NamespaceLink)
def convert(link, trailing_newline):
    print(' ... converting %s'%link.target)
    target = re.sub(r'^:','',link.target)
    if is_file_namespace(target): # is a link to a file or image
        target = canonicalise_file_namespace(target)
        #non-detected file link has a caption: sparate it
        if re.match(r'\|',target):
            target,caption=target.split('|')
        else:
            caption = convert_children(link).strip()
        filename = convert_internal_link(re.sub(r'.*[:/]','',target))
        target = ":".join(convert_internal_link(tg) for tg in target.split(":"))
        print('     ... is a file link to %s'%filename)
        if len(caption) > 0:
            return "{{%s|%s}}" % (target, caption)
        else:
            return "{{%s}}" % (target)
    else:
        print("WARNING: Ignoring namespace link to " + link.target)
        return convert_children(link)


@visitor.when(ItemList)
def convert(itemlist, trailing_newline):
    def apply_itemlist_properties(node):
        # ItemLists are used for depth/style tracking - applies those attributes to all its children
        for child in node.children:
            try:
                child.list_style = "* " if itemlist.tagname == "ul" else "- "
                child.list_depth += 1
            except AttributeError:
                child.list_depth = 1
            apply_itemlist_properties(child)
    apply_itemlist_properties(itemlist)
    return convert_children(itemlist)

@visitor.when(Item)
def convert(item, trailing_newline):
    item_content = convert_children(item)
    return "  "*item.list_depth + item.list_style + item_content

@visitor.when(Table)
def convert(table, trailing_newline):
    # we ignore the actual Table tags, instead convert each Row & Cell individually
    return convert_children(table)

@visitor.when(Cell)
def convert(cell, trailing_newline):
    marker = "^" if cell.tagname == "th" else "|"
    result = "%s %s" % (marker, convert_children(cell).replace('\n','').strip())
    return result

@visitor.when(Row)
def convert(row, trailing_newline):
    return convert_children(row) + " |\n"

@visitor.when(PreFormatted)
def convert(pre, trailing_newline):
    try:
        in_list = item.list_depth > 0
    except:
        in_list = False
    if trailing_newline and not in_list: # in its own paragraph, use a two space indent
        return "  " + convert_children(pre).replace("\n","\n  ").strip(" ")
    else: # inline in a list or a paragraph body, use <code> tags
        return "<code>" + convert_children(pre) + "</code>"

@visitor.when(TagNode)
def convert(tag, trailing_newline):
    # dict maps mediawiki tag name to tuple of starting, ending dokuwiki tag
    simple_tagitems = {
        "tt" : ("''", "''"),
        "ref" : ("((","))"), # references converted to footnotes
        "code" : ("<code>","</code>"),
    }
    if tag.tagname in simple_tagitems:
        pre,post = simple_tagitems[tag.tagname]
        return pre + convert_children(tag) + post
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

    return convert_children(tag)

# catchall for Node, which is the parent class of everything above
@visitor.when(Node)
def convert(node, trailing_newline):
    if node.__class__ != Node:
        print("WARNING: Unsupported node type: %s" % (node.__class__))
    return convert_children(node)


def convert_internal_link(mw_target):
    """
    Convert an internal Mediawiki link, with or without an anchor # in the middle.

    Same as converting a plain pagename, only we want to preserve any #s in the target text.
    """
    parts = mw_target.split("#")
    return "#".join([dokuwiki.make_dokuwiki_pagename(part) for part in parts])
