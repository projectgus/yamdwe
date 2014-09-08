

# Yet Another Mediawiki to DokuWiki Exporter

Yamdwe is made up of two Python programs to export an existing
Mediawiki install to a Dokuwiki install.

# Features

* Exports and recreates full revision history of all pages, including author information for correct attribution.
* Exports images and maintains modification dates (but not past revisions of an image.)
* Can optionally export user accounts to the default dokuiwiki "basicauth" format (see below.)
* Parses MediaWiki syntax using the [mwlib library](http://mwlib.readthedocs.org/en/latest/index.html) (as used by Wikipedia), so can convert most pages very cleanly - minimal manual cleanup.
* Syntax support includes: tables, image embeds, code blocks.
* Uses the MediaWiki API to export pages and images, so a MediaWiki install can be exported remotely and without admin privileges (NB: Yamdwe does hit the API quite hard, so please do not export other people's wikis for fun. Or, at minimum, please read their Terms of Service first and comply by them.)

# Tested with

* Dokuwiki 2014-05-05 "Ponder Stibbons" (should work on any recent version, see below for notes about user passwords.)
* MediaWiki 1.19.1 (should work on 1.13 or newer.)
* A smallish wiki.

# Not-So-Features

This is one of those projects you hammer out once for a given task (in this case migrating the Melbourne Hackerspace's small wiki installation) and then invariably neglect. It'll hopefully work for you, and I've tried to write it in a sensible way so if you know some Python you can probably hack on it without cursing my name too much, but I probably won't be maintaining it. :(.

If you are interested in maintaining this project on any kind of
basis then please let me know and I will gladly hand it over.

If you do find glaring bugs then please do take the time to [open
an Issue](https://github.com/projectgus/yamdwe/issues) here on github.

# Requirements

* Python 2.7 or newer (Python 3 not supported by all dependencies at time of writing.)
* [requests module](http://docs.python-requests.org/en/latest/)
* [simplemediawiki module](http://pythonhosted.org/simplemediawiki/)
* [mwlib module](http://mwlib.readthedocs.org/en/latest/index.html)

## If exporting users is required

* [Python MySQLDb](http://sourceforge.net/projects/mysql-python/)

# Using yamdwe

## Installing dependencies

### 1. Basic dependencies

For Debian/Ubuntu Linux:

    sudo apt-get install python python-mysqldb python-pip python-lxml python-requests python-dev

### 2. Virtualenv (optional)

I suggest installing the remaining Python dependencies inside a
[virtualenv](https://virtualenv.pypa.io/en/latest/), as mwlib in
particular has a lot of specific dependencies.

Some of the mwlib dependencies may be available as system Python
packages, but they may have older/incompatible versions. Sandboxing
these packages into a "virtualenv" avoids these version conflicts.

Virtualenv & virtualenvwrapper for Debian/Ubuntu:

    sudo apt-get install python-virtualenv virtualenvwrapper
    source /etc/bash_completion
    mkvirtualenv --system-site-packages yamdwe

(Next time you log in the [virtualenvwrapper aliases](http://virtualenvwrapper.readthedocs.org/en/latest/command_ref.html) will be
automatically added to your environment, and you can use `workon yamdwe` to
enable the yamdwe virtualenv.)

### 3. Pip dependencies

Make sure to run these inside the virtualenv (ie run `workon yamdwe`
first), if you're using a virtulaenv.

    pip install http://pypi.python.org/packages/source/s/simplemediawiki/simplemediawiki-1.2.0b2.tar.gz
    pip install -i http://pypi.pediapress.com/simple/ mwlib

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

yamdwe_users exports mediawiki password hashes to a dokuwiki "basicauth" text file. These imported passwords won't work with the current stable Dokuwiki version (2014-05-05 "Ponder Stibbons".) However they will work with the current development version, or if you patch with [this commit](https://github.com/splitbrain/dokuwiki/commit/42aeaf8323271f65bb906e11c6126d3a2d060a3f).

## Post Import Steps

* After the export please check for [correct permissions](https://www.dokuwiki.org/install:permissions) on
  the dokuwiki `data/conf/users.auth.php` file and other data/conf files.

* The search index needs to be manually rebuilt with the contents of the new pages. The [searchindex plugin](https://www.dokuwiki.org/plugin:searchindex) can do this.
