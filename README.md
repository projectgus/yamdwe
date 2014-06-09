# Yet Another Mediawiki to DokuWiki Exporter

Yamdwe is made up of two Python programs to export an existing
Mediawiki install to a Dokuwiki install. It also serves a cautionary
tale about overzealous yak shaving.

# Features

* Exports and recreates full revision history of all pages, including author information for correct attribution.
* Exports images and maintains modification dates (but not past revisions of an image.)
* Can optionally export user accounts.
* Parses MediaWiki syntax using the [mwlib library](http://mwlib.readthedocs.org/en/latest/index.html) (as used by Wikipedia), so can convert most pages quite cleanly.
* Syntax support includes: tables, image embeds, code blocks.
* Uses Mediawiki API for pages and images, so local access to Mediawiki is not required to export it (NB: Yamdwe does hit the API quite hard, so please do not export other people's wikis for fun. Or, at minimum, please read their Terms of Service first.)

# Tested with

* Dokuwiki 2014-05-05 "Ponder Stibbons" (should work on any recent version.)
* MediaWiki 1.19.1 (should work on 1.8 or newer.)
* A smallish wiki.

# Not-So-Features

Is one of those projects you hammer out once for a given task (in this case migrating the Melbourne Hackerspace's small wiki installation) and then neglect. It'll hopefully work for you, and I've tried to write it in a sensible way so if you know some Python you can probably hack on it without cursing my name too much, but I probably won't be maintaining it. :(.

If you are interested in maintaining this project on any kind of
basis then please let me know and I will gladly hand it over.

If you do find glaring bugs then please do still take the time to open
an Issue here on github.

# Requirements

* Python 2.7 or newer
* [requests module](http://docs.python-requests.org/en/latest/)
* [simplemediawiki module](http://pythonhosted.org/simplemediawiki/)
* [mwlib module](http://mwlib.readthedocs.org/en/latest/index.html)

## For exporting Users (only)

* [Python MySQLDb](http://sourceforge.net/projects/mysql-python/)

# Using yamdwe

## Installing dependencies

For Debian/Ubuntu Linux:
    sudo apt-get install python python-mysqldb python-pip

(I suggest installing the following Python dependencies inside a
[virtualenv](https://virtualenv.pypa.io/en/latest/), as mwlib in
particular has a lot of specific dependencies)

    pip install http://pypi.python.org/packages/source/s/simplemediawiki/simplemediawiki-1.2.0b2.tar.gz
    pip install -i http://pypi.pediapress.com/simple/ mwlib
    pip install requests

## Set up Dokuwiki

If you're creating a new DokuWiki then set up your
[DokuWiki](http://dokuwiki.org) installation and perform the initial
installation steps (name the wiki, set up an admin user, etc.) You can
also use yamdwe with an existing wiki, but any existing content with
the same name will be overwritten.

## Exporting pages & images

To start an export, you will need the URL of the mediawiki API (usually http://mywiki/wiki/api.php or similar) and the local path to the Dokuwiki installation.

    yamdwe.py MEDIAWIKI_API_URL DOKUWIKI_ROOT_PATH

If installation goes well it should print the names of pages and images as it is exporting, and finally print "Done". This process can be slow, and can load up the Mediawiki server for large wikis.

Yamdwe may warn you at the end that it is unable to set [correct permissions for the Dokuwiki data directories and files](https://www.dokuwiki.org/install:permissions) - regardless, you should check and correct these manually.

Inevitably some content will not import cleanly, so a manual check/edit/cleanup pass is almost certainly necessary.

## Exporting users

This step is optional, but it's nice as it matches the user names in the imported revision history with actual users in dokuwiki.

For this step you need access to the MySQL database backing the mediawiki install, and local access to the dokuwiki root directory.

An example usage looks like this:

    ./yamdwe_users.py -u mediawiki --prefix wiki_ /srv/www/dokuwiki/

Run yamdwe_users.py with "-h" to see all options:

Any settings you're unsure about (like `--prefix` for table prefix)
can be found in the LocalSettings.php file of your Mediawiki
installation.

yamdwe_users exports mediawiki password hashes to a dokuwiki "basicauth" text file, but at time of writing Dokuwiki can't actually use these and each user will need to reset their password. If [this pull request](https://github.com/splitbrain/dokuwiki/pull/755) is accepted then passwords will "just work" after export.

Please check for
[correct permissions](https://www.dokuwiki.org/install:permissions) on
the dokuwiki `data/conf/users.auth.php` file after the export is
finished.
