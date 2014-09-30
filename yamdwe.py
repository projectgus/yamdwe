#!/usr/bin/env python
"""
Export all revisions of all pages, plus all images/meda, from a
Mediawiki install to a Dokuwiki install. Mediawiki install can be
remote (uses API, but check terms of service.) Dokuwiki install is
local.

Requirements:
Python 2.7, mwlib, simplemediawiki, requests

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import argparse, sys, codecs
from pprint import pprint
import mediawiki, dokuwiki, wikicontent

def main():
    # the wikicontent code (that uses visitor module) tends to recurse quite deeply for complex pages
    sys.setrecursionlimit(20000)

    enable_unicode_output()

    args = arguments.parse_args()
    importer = mediawiki.Importer(args.mediawiki)
    exporter = dokuwiki.Exporter(args.dokuwiki)

    # Set the wikicontent's definition of File: and Image: prefixes (varies by language settings)
    canonical_file, aliases = importer.get_file_namespaces()
    wikicontent.set_file_namespaces(canonical_file, aliases)

    # Convert all pages and page revisions
    pages = importer.get_all_pages()
    print("Found %d pages to export..." % len(pages))
    exporter.write_pages(pages)

    # Bring over images
    images = importer.get_all_images()
    print("Found %d images to export..." % len(images))
    exporter.write_images(images, canonical_file)

    # fix permissions on data directory if possible
    exporter.fixup_permissions()

    # touch conf file to invalidate cached pages
    exporter.invalidate_cache()

    print("Done.")

def enable_unicode_output():
    """ We output a lot of Unicode strings, so set Unicode output to console/file if its not already set """
    if sys.stdout.encoding in [ None, "ascii" ]:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

# Parser for command line arguments
arguments = argparse.ArgumentParser(description='Convert a Mediawiki installation to a Dokuwiki installation.')
#arguments.add_argument('-y', '--yes',help="Don't pause for confirmation before exporting", action="store_true")
arguments.add_argument('mediawiki', metavar='MEDIAWIKI_API_URL', help="URL of mediawiki's api.php file (something like http://mysite/wiki/api.php)")
arguments.add_argument('dokuwiki', metavar='DOKUWIKI_ROOT', help="Root path to an existing dokuwiki installation to add the Mediawiki pages to (can be a brand new install.)")

if __name__ == "__main__":
    main()
