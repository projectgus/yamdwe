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
import argparse, sys, codecs, locale, getpass, datetime
from pprint import pprint
import mediawiki, dokuwiki, wikicontent
import inspect

def main():
    # the wikicontent code (that uses visitor module) tends to recurse quite deeply for complex pages
    sys.setrecursionlimit(20000)

    # try not to crash if the output/console has a character we can't encode
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout, "replace")

    args = arguments.parse_args()

    if args.http_pass is not None and args.http_user is None:
        raise RuntimeError("ERROR: Option --http_pass requires --http_user to also be specified")
    if args.wiki_pass is not None and args.wiki_user is None:
        raise RuntimeError("ERROR: Option --wiki_pass requires --wiki_user to also be specified")

    if args.http_user is not None and args.http_pass is None:
        args.http_pass = getpass.getpass("Enter password for HTTP auth (%s):" % args.http_user)
    if args.wiki_user is not None and args.wiki_pass is None:
        args.wiki_pass = getpass.getpass("Enter password for Wiki login (%s):" % args.wiki_user)

    if not args.mediawiki.endswith("api.php"):
        print("WARNING: Mediawiki URL does not end in 'api.php'... This has to be the URL of the Mediawiki API, not just the wiki. If you can't export anything, try adding '/api.php' to the wiki URL.")

    if "domain" in inspect.getargspec(simplemediawiki.MediaWiki.__init__)[0]:
        importer = mediawiki.Importer(args.mediawiki, args.http_user, args.http_pass, args.wiki_user, args.wiki_pass, args.wiki_domain, args.verbose)
    else:
        importer = mediawiki.Importer(args.mediawiki, args.http_user, args.http_pass, args.wiki_user, args.wiki_pass, args.verbose)
    exporter = dokuwiki.Exporter(args.dokuwiki)

    # Set the wikicontent's definition of File: and Image: prefixes (varies by language settings)
    canonical_file, aliases = importer.get_file_namespaces()
    wikicontent.set_file_namespaces(canonical_file, aliases)

    # Read all pages and page revisions
    pages = importer.get_all_pages()
    print("Found %d pages to export..." % len(pages))

    # Add a shameless "exported by yamdwe" note to the front page of the wiki
    mainpage = importer.get_main_pagetitle()

    for page in pages:
        if page["title"] == mainpage:
            latest = dict(page["revisions"][0])
            latest["user"] = "yamdwe"
            now = datetime.datetime.utcnow().replace(microsecond=0)
            latest["timestamp"] = now.isoformat() + "Z"
            latest["comment"] = "Automated note about use of yamdwe Dokuwiki import tool"
            latest["*"] += "\n\n(Automatically exported to Dokuwiki from Mediawiki by [https://github.com/projectgus/yamdwe Yamdwe] on %s.)" % (datetime.date.today().strftime("%x"))
            page["revisions"].insert(0, latest)

    # Export pages to Dokuwiki format
    exporter.write_pages(pages)

    # Bring over images
    images = importer.get_all_images()
    print("Found %d images to export..." % len(images))
    exporter.write_images(images, canonical_file, args.http_user, args.http_pass)

    # fix permissions on data directory if possible
    exporter.fixup_permissions()

    # touch conf file to invalidate cached pages
    exporter.invalidate_cache()

    print("Done.")

# Parser for command line arguments
arguments = argparse.ArgumentParser(description='Convert a Mediawiki installation to a Dokuwiki installation.')
#arguments.add_argument('-y', '--yes',help="Don't pause for confirmation before exporting", action="store_true")
arguments.add_argument('--http_user', help="Username for HTTP basic auth")
arguments.add_argument('--http_pass', help="Password for HTTP basic auth (if --http_user is specified but not --http_pass, yamdwe will prompt for a password)")
arguments.add_argument('--wiki_user', help="Mediawiki login username")
arguments.add_argument('--wiki_pass', help="Mediawiki login password (if --wiki_user is specified but not --wiki_pass, yamdwe will prompt for a password)")
if "domain" in inspect.getargspec(simplemediawiki.MediaWiki.__init__)[0]:
    arguments.add_argument('--wiki_domain', help="Mediawiki login domain (needs a non-standard simplemediawiki library)")
arguments.add_argument('-v', '--verbose',help="Print verbose progress and error messages", action="store_true")
arguments.add_argument('mediawiki', metavar='MEDIAWIKI_API_URL', help="URL of mediawiki's api.php file (something like http://mysite/wiki/api.php)")
arguments.add_argument('dokuwiki', metavar='DOKUWIKI_ROOT', help="Root path to an existing dokuwiki installation to add the Mediawiki pages to (can be a brand new install.)")

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("ERROR: %s" % e)
        sys.exit(3)
