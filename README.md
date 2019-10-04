# Yet Another Mediawiki to DokuWiki Exporter

Yamdwe is made up of two Python programs to export an existing
Mediawiki install to a Dokuwiki install.

[![Build Status](https://travis-ci.org/projectgus/yamdwe.svg?branch=master)](https://travis-ci.org/projectgus/yamdwe)

**yamde needs a new maintainer** - I've gotten busy with other responsibilities and I'm not giving yamdwe the attention it deserves. It's mostly mature software, the only issue is occasionally content in some wikis that doesn't convert properly. Yamdwe has automated tests and continuous integration so it's not too painful to add bugfixes, the usual slow point is investigating behaviour of mediawiki installs that aren't publically available. If you're interested in helping out then please get in touch, or just browse the [Issues](https://github.com/projectgus/yamdwe/issues) list and maybe send some PRs! Any active maintainer will be gladly credited and/or I'll transfer the repo to you if you'd like that. *-- Angus*

# Features

* Exports and recreates full revision history of all pages, including author information for correct attribution.
* Exports images and maintains modification dates (but not past revisions of an image.)
* Can optionally export user accounts to the default dokuiwiki "basicauth" format (see below.)
* Parses MediaWiki syntax using the [mwlib library](http://mwlib.readthedocs.org/en/latest/index.html) (as used by Wikipedia), so can convert most pages very cleanly - minimal manual cleanup.
* Syntax support includes: tables, image embeds, code blocks.
* Uses the MediaWiki API to export pages and images, so a MediaWiki install can be exported remotely and without admin privileges (NB: Yamdwe does hit the API quite hard, so please do not export other people's wikis for fun. Or, at minimum, please read their Terms of Service first and comply by them.)
* Supports logging in to Mediawiki to export, and also HTTP Basic Auth.

# Compatible Versions

* Dokuwiki 2014-09-29a "Hrun", but should work on any recent version. Exporting users only works on 2014-09-29a or newer (see below).
* MediaWiki 1.13 or newer (ie any recent version, 1.13 is from *2008*!)

Yamdwe has now been used successfully on many wikis of various sizes. If you've used it on a particularly large or unusual wiki, please let me know!

# Requirements

* Python 2.7 or newer (Python 3 not supported by all dependencies at time of writing.)
* [requests module](http://docs.python-requests.org/en/latest/)
* [simplemediawiki module](http://pythonhosted.org/simplemediawiki/)
* [mwlib module](http://mwlib.readthedocs.org/en/latest/index.html)

## If exporting users is required

* [Python MySQLDb](http://sourceforge.net/projects/mysql-python/)

# Using yamdwe

## Installation "the Python way"

Note: It's strongly recommended to use a [virtualenv](https://virtualenv.pypa.io/en/latest/) environment to keep yamdwe's libraries isolated from the rest of your system. yamdwe has over 20 package dependencies including some very specific versions to support mwlib. Good introductory posts about virtualenv can be found [here](http://davedash.com/tutorial/virtualenv/) and [also here](http://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/). You may want to check out [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/), which provides handy shortcuts for common virtualenv operations.

Once the virtualenv is made and activated:

    pip install -r requirements.txt

If exporting users is also required, install MySQL-python:

    pip install MySQL-python=1.2.5

## Alternative Installation for Debian/Ubuntu Linux

Installing everything via pip as shown above means compiling some
common packages from source. Here's an alternative set of commands to
set up a virtualenv on Debian/Ubuntu, but with some common packages
installed into the main system:

    sudo apt-get install python-mysqldb python-pip python-lxml python-requests python-dev python-virtualenv
    virtualenv --system-site-packages -p python2.7 env
	source env/bin/activate
	pip install simplemediawiki==1.2.0b2
	pip install -i http://pypi.pediapress.com/simple/ mwlib

(Once done working with yamdwe, run `deactivate` to leave the virtualenv, `source env/bin/activate` again to re-enter it).

If the installation of mwlib fails install the packages recommended for mwlib https://mwlib.readthedocs.io/en/latest/installation.html#ubuntu-install

	sudo apt-get install -y gcc g++ make python python-dev python-virtualenv   \
 	 libjpeg-dev libz-dev libfreetype6-dev liblcms-dev                   \
 	 libxml2-dev libxslt-dev                                             \
 	 ocaml-nox git-core                                                  \
 	 python-imaging python-lxml                                          \
  	 texlive-latex-recommended ploticus dvipng imagemagick               \
 	 pdftk

## Set up Dokuwiki

If you're creating a new DokuWiki then set up your
[DokuWiki](http://dokuwiki.org) installation and perform the initial
installation steps (name the wiki, set up an admin user, etc.) You can
also use yamdwe with an existing wiki, but any existing content with
the same name will be overwritten.

## Exporting pages & images

To start an export, you will need the URL of the mediawiki API (usually http://mywiki/wiki/api.php or similar) and the local path to the Dokuwiki installation.

    yamdwe.py MEDIAWIKI_API_URL DOKUWIKI_ROOT_PATH

If you need to log in to to your Mediawiki install (either with a Mediawiki username and if you are in a domain with the domain-name, or via HTTP Basic Auth) then run `yamdwe.py -h` to view the command line options for authentication.

Domain functionality is added through the "develop" branch of this [simplemediawiki fork](https://github.com/BlackLotus/python-simplemediawiki/tree/develop) and can be used through.

    yamdwe.py --wiki_domain WIKI_DOMAIN MEDIAWIKI_API_URL DOKUWIKI_ROOT_PATH

If installation goes well it should print the names of pages and images as it is exporting, and finally print "Done". This process can be slow, and can load up the Mediawiki server for large wikis.

Yamdwe may warn you at the end that it is unable to set [correct permissions for the Dokuwiki data directories and files](https://www.dokuwiki.org/install:permissions) - regardless, you should check and correct these manually.

Inevitably some content will not import cleanly, so a manual check/edit/cleanup pass is almost certainly necessary.

## Dokuwiki Plugin Features

Yamdwe supports some features in Mediawiki that aren't supported by a base Dokuwiki installaton. To display these elements Dokuwiki plugins are required:

* `<blockquote>` tags in Mediawiki can use the [blockquote plugin](https://www.dokuwiki.org/plugin:blockquote) in Dokuwiki.
* `<math>` tags in Mediawiki can use the [MathJax plugin](https://www.dokuwiki.org/plugin:mathjax) (or similar) in Dokuwiki.

You only need the plugins for any features that you are using in your Mediawiki and want to keep using as-is.

## Exporting users

This step is optional, but it's nice as it matches the user names in the imported revision history with actual users in dokuwiki.

For this step you need MySQL-python installed and access to the MySQL database backing the mediawiki install, and local access to the dokuwiki root directory.

An example usage looks like this:

    ./yamdwe_users.py -u mediawiki --prefix wiki_ /srv/www/dokuwiki/

Run yamdwe_users.py with "-h" to see all options:

Any settings you're unsure about (like `--prefix` for table prefix)
can be found in the LocalSettings.php file of your Mediawiki
installation.

yamdwe_users exports mediawiki password hashes to a dokuwiki "basicauth" text file. These imported passwords require Dokuwiki version 2014-09-29 "Hrun" or newer. On older Dokuwiki installs the password file format is not compatible and it will break user auth. The best thing to do is to update to 2014-09-29 or newer before running `yamdwe_users.py`.

## Post Import Steps

* After the export please check for [correct permissions](https://www.dokuwiki.org/install:permissions) on
  the dokuwiki `data/conf/users.auth.php` file and other data/conf files.

* The search index needs to be manually rebuilt with the contents of the new pages. The [searchindex plugin](https://www.dokuwiki.org/plugin:searchindex) can do this.

## Common Manual Cleanup Items

* Page naming and namespaces will probably need some rearranging/renaming to seem "natural" in Dokuwiki. The [move Plugin](https://www.dokuwiki.org/plugin:move) makes this straightforward.

* Some uncommon URL schemes, such as `file://`, are not detected by Dokuwiki as links unless you [add a scheme.local.conf file as described here](https://www.dokuwiki.org/urlschemes)


# Known Issues

Please check the [Issues list on github](https://github.com/projectgus/yamdwe/issues) to see what's going on.

If you do find a bug or have trouble exporting a wiki then please open an issue there and I (or other yamdwe users) can try and help you out.

## Submitting Good Bug Reports

If the bug is with some Mediawiki markup that doesn't provide the expected Dokuwiki markup, for a good bug report please include:

* Excerpt of the Mediawiki markup causing the problem.
* Desired Dokuwiki markup output.
* Actual (problematic) Dokuwiki output from yamdwe.

## Better Bug Reports?

Want to put a huge smile on my face and get a massive karma dose by
submitting an even better bug report? Are you comfortable using git &
github?

* Fork the yamdwe repository on github.
* Add a test case directory under tests/ and place the problematic Mediawiki markup into a file `mediawiki.txt`, and the desired correct Dokuwiki output into `dokuwiki.txt`.
* Run `wikicontent_tests.py` to verify that the incorrect output you expected is printed as part of the test failure.
* Add a commmit which adds the new test case directory.
* Submit a Pull Request for the test failure. Use the Pull Request description field to explain the problem.

## Best Bug Reports?

If you want to outclass even that bug report, your commit could also add a fix for the conversion problem in yamdwe, so all tests pass including the new one you added! *A+++ would accept Pull Request again!*

Don't worry if you don't want to perform any extra steps though, any (polite) bug report is always welcome!
