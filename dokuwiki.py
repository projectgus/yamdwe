import os, os.path, gzip, shutil
import wikicontent
import simplemediawiki


def write_dokuwiki(rootpath, pages):
    prepare_rootpath(rootpath)
    for page in pages:
        convert_page(rootpath, page)
    fixup_permissions(rootpath)

def prepare_rootpath(rootpath):
    """ Ensure the rootpath looks like a DokuWiki install, back up any existing meta, attic & pages directories """
    if not os.path.isdir(rootpath):
        raise RuntimeError("Dokuwiki root path '%s' does not point to a directory" % rootpath)
    data = os.path.join(rootpath, "data")
    if not os.path.isdir(data):
        raise RuntimeError("Dokuwiki root path '%s' does not contain a data directory" % rootpath)
    meta = os.path.join(data, "meta")
    attic = os.path.join(data, "attic")
    pages = os.path.join(data, "pages")
    for existing in [ meta, attic, pages]:
        if os.path.isdir(existing):
            print("Moving existing directory '%s' out of the way to '%s.old'..." % (existing, os.path.basename(existing)))
            olddir = existing+".old"
            if os.path.isdir(olddir)
                shutil.rmtree(olddir)
            os.rename(existing, olddir)
        os.mkdir(existing, 0o770)

def convert_page(rootpath, page):
    """ Convert the supplied mediawiki page to a Dokuwiki page """
    print("Converting %d revisions of page '%s'..." %
          (len(page["revisions"]), page['title']))
    subdir, pagename = os.path.split(page['title'].replace(" ","_").lower())
    pagedir = os.path.join(rootpath, "data", "pages", subdir)
    metadir = os.path.join(rootpath, "data", "meta", subdir)
    atticdir = os.path.join(rootpath, "data", "attic", subdir)
    if not os.path.isdir(pagedir):
        os.makedirs(pagedir)
    if not os.path.isdir(metadir):
        os.makedirs(metadir)
    if not os.path.isdir(atticdir):
        os.makedirs(atticdir)
    revisions = list(reversed(page["revisions"])) # oldest first
    for revision in revisions:
        content = wikicontent.convert_pagecontent(revision["*"])
        if revision == revisions[-1]: # current revision page, create 'pages' .txt
            with open(os.path.join(pagedir, "%s.txt"%pagename), "w") as f:
                    f.write(content)
        # create gzipped attic revision
        timestamp = int(simplemediawiki.MediaWiki.parse_date(revision['timestamp']).timestamp())
        with gzip.open(os.path.join(atticdir,
                                    "%s.%d.txt.gz" % (pagename, timestamp)),
                       "wb") as f:
            f.write(content.encode())
        # create entry in 'changes' metadata index
        with open(os.path.join(metadir, "%s.changes"%pagename), "a") as f:
            f.write("%d\t0.0.0.0\t%s\t%s\t%s\n"
                    % (timestamp,
                       "C" if revision == revisions[0] else "E",
                       pagename,
                       revision["user"]))


def fixup_permissions(rootpath):
    """ Fix permissions under the specified data directory

    This means applying the data directory's permissions and ownership to all underlying parts
    """
    
