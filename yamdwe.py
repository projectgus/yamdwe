#!/usr/bin/env python3

"""

Debian/Ubuntu install
sudo apt-get install python3 python3-pip
sudo pip3 install http://pypi.python.org/packages/source/s/simplemediawiki/simplemediawiki-1.2.0b2.tar.gz

"""

import argparse, sys
from simplemediawiki import MediaWiki
from pprint import pprint
import mediawiki, dokuwiki


def main():
    args = arguments.parse_args()
    mw = MediaWiki(args.mediawiki)
    pages = mediawiki.get_all_pages(mw)[:4]
    print("Found %d pages to export" % len(pages))
    for page in pages:
        page["revisions"] = mediawiki.get_revisions(mw, page)
    dokuwiki.write_dokuwiki(args.dokuwiki, pages)

# Parser for command line arguments
arguments = argparse.ArgumentParser(description='Convert a Mediawiki installation to a brand new Dokuwiki installation.')
#arguments.add_argument('-y', '--yes',help="Don't pause for confirmation before exporting", action="store_true")
arguments.add_argument('mediawiki', metavar='MEDIAWIKI_API_URL', help="URL of mediawiki's api.php file (something like http://mysite/wiki/api.php)")
arguments.add_argument('dokuwiki', metavar='DOKUWIKI_ROOT', help="Root path to an empty (erasable) dokuwiki installation")

if __name__ == "__main__":
    main()
