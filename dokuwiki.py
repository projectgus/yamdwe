import os, os.path, gzip, shutil, re
import wikicontent
import simplemediawiki

class Exporter(object):
    def __init__(self, rootpath):

        # verify the dokuwiki rootpath exists
        self.root = rootpath
        if not os.path.isdir(rootpath):
            raise RuntimeError("Dokuwiki root path '%s' does not point to a directory" % rootpath)

        # check a 'data' directory exists, establish pathes for each subdirectory
        self.data = os.path.join(rootpath, "data")
        if not os.path.isdir(self.data):
            raise RuntimeError("Dokuwiki root path '%s' does not contain a data directory" % rootpath)

        # create meta, attic, pages subdirs if they don't exist (OK to have deleted them before the import)
        self.meta = os.path.join(self.data, "meta")
        self.attic = os.path.join(self.data, "attic")
        self.pages = os.path.join(self.data, "pages")
        for subdir in [ self.meta, self.attic, self.pages]:
            ensure_directory_exists(subdir)

    def write_pages(self, pages):
        """
        Given 'pages' as a list of mediawiki pages with revisions attached, export them to dokuwiki pages
        """
        for page in pages:
            self._convert_page(page)
        self._write_wikichanges()
        self._fixup_permissions()

    def _convert_page(self, page):
        """ Convert the supplied mediawiki page to a Dokuwiki page """
        print("Converting %d revisions of page '%s'..." %
              (len(page["revisions"]), page['title']))
        # Sanitise the mediawiki pagename to something resemblign a dokuwiki pagename convention
        full_title = make_dokuwiki_pagename(page['title'])

        # Mediawiki pagenames can contain /s, convert these to dokuwiki / paths on the filesystem
        subdir, pagename = os.path.split(full_title)
        pagedir = os.path.join(self.pages, subdir)
        metadir = os.path.join(self.meta, subdir)
        atticdir = os.path.join(self.attic, subdir)
        for d in pagedir, metadir, atticdir:
            ensure_directory_exists(d)

        # Walk through the list of revisions
        revisions = list(reversed(page["revisions"])) # order as oldest first
        for revision in revisions:
            is_current = (revision == revisions[-1])
            is_first = (revision == revisions[0])
            content = wikicontent.convert_pagecontent(revision["*"])
            # path to the .changes metafile
            changespath = os.path.join(metadir, "%s.changes"%pagename)
            # for current revision, create 'pages' .txt
            if is_current:
                with open(os.path.join(pagedir, "%s.txt"%pagename), "w") as f:
                    f.write(content)
            # create gzipped attic revision
            timestamp = int(simplemediawiki.MediaWiki.parse_date(revision['timestamp']).timestamp())
            atticname = "%s.%d.txt.gz" % (pagename, timestamp)
            atticpath = os.path.join(atticdir, atticname)
            with gzip.open(atticpath, "wb") as f:
                f.write(content.encode())
            # append entry to page's 'changes' metadata index
            with open(changespath, "w" if is_first else "a") as f:
                fields = (str(timestamp), "0.0.0.0", "C" if is_first else "E", full_title, revision["user"])
                print("\t".join(fields), file=f)


    def _write_wikichanges(self):
        """
        Rebuild the wiki-wide changelong meta/_dokuwiki.changes

        This is a Pythonified version of https://www.dokuwiki.org/tips:Recreate_Wiki_Change_Log
        """
        lines = []
        for changesfile in os.listdir(self.meta):
            if changesfile == "_dokuwiki.changes" or not changesfile.endswith(".changes"):
                continue
            with open(os.path.join(self.meta,changesfile), "r") as f:
                lines += f.readlines()
        lines = sorted(lines, key=lambda r: int(r.split("\t")[0]))
        with open(os.path.join(self.meta, "_dokuwiki.changes"), "w") as f:
            f.writelines(lines)

    def _fixup_permissions(self):
        """ Fix permissions under the data directory

        This means applying the data directory's permissions and ownership to all underlying parts.

        If this fails due to insufficient privileges then it just prints a warning and continues on.
        """
        stat = os.stat(self.data)
        try:
            for root, dirs, files in os.walk(self.data):
                for name in files + dirs:
                    path = os.path.join(root, name)
                    os.chmod(path, stat.st_mode)
                    os.chown(path, stat.st_uid, stat.st_gid)
        except OSError:
            print("WARNING: Failed to set permissions under the data directory (not owned by process?) May need to be manually fixed.")



def ensure_directory_exists(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def make_dokuwiki_pagename(mediawiki_name):
    """
    Convert a canonical mediawiki pagename to a dokuwiki pagename
    """
    result = mediawiki_name.replace(" ","_")
    return camel_to_underscore(result)

def camel_to_underscore(camelcase):
    """
    Convert a camelcased string to underscore_delimited (tweaked from this StackOverflow answer)
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
    """
    s1 = re.sub('(^_)([A-Z][a-z]+)', r'\1_\2', camelcase)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()    
