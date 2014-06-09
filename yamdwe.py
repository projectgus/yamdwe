#!/usr/bin/env python

"""

Debian/Ubuntu install
sudo apt-get install python-pip

(Probably actually want a virtualenv for these steps)

pip install http://pypi.python.org/packages/source/s/simplemediawiki/simplemediawiki-1.2.0b2.tar.gz
pip install -i http://pypi.pediapress.com/simple/ mwlib

"""
from __future__ import print_function, unicode_literals, absolute_import, division
import argparse, sys
from pprint import pprint
import mediawiki, dokuwiki


def main():
    args = arguments.parse_args()
    importer = mediawiki.Importer(args.mediawiki)
    exporter = dokuwiki.Exporter(args.dokuwiki)

    # Convert all pages and page revisions
    pages = importer.get_all_pages()
    print("Found %d pages to export..." % len(pages))
    exporter.write_pages(pages)

    # Bring over images
    images = importer.get_all_images()
    print("Found %d images to export..." % len(images))
    exporter.write_images(images)

    # fix permissions on data directory if possible
    exporter.fixup_permissions()


# Parser for command line arguments
arguments = argparse.ArgumentParser(description='Convert a Mediawiki installation to a brand new Dokuwiki installation.')
#arguments.add_argument('-y', '--yes',help="Don't pause for confirmation before exporting", action="store_true")
arguments.add_argument('mediawiki', metavar='MEDIAWIKI_API_URL', help="URL of mediawiki's api.php file (something like http://mysite/wiki/api.php)")
arguments.add_argument('dokuwiki', metavar='DOKUWIKI_ROOT', help="Root path to an empty (erasable) dokuwiki installation")

if __name__ == "__main__":
    main()
