#!/usr/bin/env python
"""
Migrate user accounts from a Mediawiki installation to a Dokuwiki installation.

Unlike yamdwe.py which can use the Mediawiki API, yamdwe_users.py requires
a database connection to migrate user accounts.

Assumes MySQL, sorry Postgres fans.

Requirements:
Python 2.7, MySQLdb

On Debian/Ubuntu:
sudo apt-get install python-mysqldb

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import argparse, sys, os.path, collections, getpass, MySQLdb
import names
from pprint import pprint

def main():
    args = arguments.parse_args()

    userfile = os.path.join(args.dokuwiki, "conf", "users.auth.php")

    if not os.path.exists(userfile):
        print("Error: users.auth doesn't exist at %s" % userfile)
        if os.path.exists(userfile + ".dist"):
            print("users.auth.dist exists. This suggests you haven't yet run install.php to create a superuser (recommended.")
        sys.exit(1)

    commentblock, dw_users = get_dokuwiki_users(userfile)
    print("Found %d existing dokuwiki users..." % len(dw_users))

    if not args.no_password:
        print("Enter MySQL password for user %s:" % args.user)
        pw = getpass.getpass()
    else:
        pw = None

    mw_users = get_mediawiki_users(args.host, args.user, pw, args.db, args.prefix)

    for mw_username in mw_users.keys():
        if mw_username in dw_users:
            print("%s already exists in users.auth. Updating attributes..." % mw_username)
            dw_users[mw_username]["name"] = mw_users[mw_username]["name"]
            dw_users[mw_username]["email"] = mw_users[mw_username]["email"]
            dw_users[mw_username]["pwhash"] = mw_users[mw_username]["pwhash"]
        else:
            print("Adding new user %s..." % mw_users[mw_username]["login"])
            dw_users[mw_username] = mw_users[mw_username]

    print("Writing %d users back to dokuwiki users.auth.php..." % len(dw_users))
    write_dokuwiki_users(userfile, commentblock, dw_users)
    print("Done.")


def get_dokuwiki_users(userfile):
    """ Parse the dokuwiki users.auth file and return block of comment text, dict of user info structures """
    users = collections.OrderedDict()
    comments = ""
    with open(userfile, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                comments += line
            elif ":" in line:
                login,pwhash,name,email,groups = re.split(r'(?<![^\\]\\)\:', line.strip(),5)
                users[login] = {
                    "login" : login,
                    "pwhash" : pwhash,
                    "name" : name,
                    "email" : email,
                    "groups" : groups,
                    }
    return comments, users

def write_dokuwiki_users(userfile, comments, users):
    """ Write out a new users.auth file with the given users, and comments. """
    with open(userfile, "w") as f:
        f.write(comments.encode("utf-8"))
        for user in users.values():
            line = u"%(login)s:%(pwhash)s:%(name)s:%(email)s:%(groups)s\n" % user
            f.write(line.encode("utf-8"))

def get_mediawiki_users(host, user, password, dbname, tableprefix):
    print(host,user,password,dbname,tableprefix)
    db = MySQLdb.connect(passwd=password, user=user, host=host, db=dbname,
                         use_unicode=True, charset="utf8")
    c = db.cursor()
    c.execute("SELECT user_name,user_real_name,user_email,user_password FROM %suser" % tableprefix)
    users = {}

    def _escape(field):
        return unicode(field, "utf-8").replace(":", r"\:")

    for row in c.fetchall():
        login = names.clean_user(unicode(row[0], "utf-8"))
        users[login] = {
            "login" : login,
            "pwhash" : _escape(row[3]),
            "name" : _escape(row[1]),
            "email" : _escape(row[2]),
            "groups" : "user",
            }
    return users

# Parser for command line arguments
arguments = argparse.ArgumentParser(description='Migrate user accounts from a Mediawiki installation to an equivalent Dokuwiki installation..')
arguments.add_argument('--host', metavar='MEDIAWIKI_DBHOST', help="Database server for the Mediawki database (default localhost.)", default="localhost")
arguments.add_argument('-u', '--user', metavar='MEDIAWIKI_USER', help="Database user for the Mediawiki database (default root.)", default="root")
arguments.add_argument('--no-password', help="Do not use a password for MySQL auth (default is to prompt for a password.)", action="store_true")
arguments.add_argument('--db', metavar='MEDIAWIKI_DBNAME', help="Database name for the Mediawiki database (default mediawiki.)", default="mediawiki")
arguments.add_argument('--prefix', metavar='TABLE_PREFIX', help="Mediawiki table prefix, optionally set in the $wgDBPrefix variable in LocalSettings.php.", default="")
arguments.add_argument('dokuwiki', metavar='DOKUWIKI_ROOT', help="Root path to an existing dokuwiki installation")

if __name__ == "__main__":
    main()
