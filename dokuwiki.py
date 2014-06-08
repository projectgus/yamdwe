import os, os.path, gzip, shutil, re, requests
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
        self._aggregate_changes(self.meta, "_dokuwiki.changes")

    def write_images(self, images):
        """
        Given 'images' as a list of mediawiki image metadata API entries,
        download and write out dokuwiki images. Does not bring over revisions.

        Images are all written to the file: namespace, to match mediawiki.
        """
        filedir = os.path.join(self.data, "media", "file")
        ensure_directory_exists(filedir)
        filemeta = os.path.join(self.data, "media_meta", "file")
        ensure_directory_exists(filemeta)
        for image in images:
            # download the image from the Mediawiki server
            print("Downloading %s..." % image['name'])
            r = requests.get(image['url'])
            # write the actual image out to the data/file directory
            name = clean_id(image['name'], False)
            imagepath = os.path.join(filedir, name)
            with open(imagepath, "wb") as f:
                f.write(r.content)
            # set modification time appropriately
            timestamp = get_timestamp(image)
            os.utime(imagepath, times=(timestamp,timestamp))
            # write a .changes file out to the media_meta/file directory
            changepath = os.path.join(filemeta, "%s.changes" % name)
            with open(changepath, "w") as f:
                fields = (str(timestamp), "::1", "C", "file:%s"%name, "", "created")
                f.write("\t".join(fields) + "\r\n")
        # aggregate all the new changes to the media_meta/_media.changes file
        self._aggregate_changes(os.path.join(self.data, "media_meta"), "_media.changes")

    def _convert_page(self, page):
        """ Convert the supplied mediawiki page to a Dokuwiki page """
        print("Converting %d revisions of page '%s'..." %
              (len(page["revisions"]), page['title']))
        # Sanitise the mediawiki pagename to something matching the dokuwiki pagename convention
        full_title = make_dokuwiki_pagename(page['title'])

        # Mediawiki pagenames can contain /s, convert these to dokuwiki / paths on the filesystem (becoming : namespaces in dokuwiki)
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
            timestamp = get_timestamp(revision)
            # path to the .changes metafile
            changespath = os.path.join(metadir, "%s.changes"%pagename)
            # for current revision, create 'pages' .txt
            if is_current:
                txtpath = os.path.join(pagedir, "%s.txt"%pagename)
                with open(txtpath, "w") as f:
                    f.write(content)
                os.utime(txtpath, times=(timestamp,timestamp))
            # create gzipped attic revision
            atticname = "%s.%s.txt.gz" % (pagename, timestamp)
            atticpath = os.path.join(atticdir, atticname)
            with gzip.open(atticpath, "wb") as f:
                f.write(content.encode())
            os.utime(atticpath, times=(timestamp,timestamp))
            # append entry to page's 'changes' metadata index
            with open(changespath, "w" if is_first else "a") as f:
                changes_title = full_title.replace("/", ":")
                fields = (str(timestamp), "::1", "C" if is_first else "E", changes_title, revision["user"])
                print("\t".join(fields), file=f)


    def _aggregate_changes(self, metadir, aggregate):
        """
        Rebuild the wiki-wide changelong from meta/ to meta/_dokuwiki.changes or
        from media_meta to media_meta/_media.changes

        This is a Pythonified version of https://www.dokuwiki.org/tips:Recreate_Wiki_Change_Log
        """
        lines = []
        for root, dirs, files in os.walk(metadir):
            for changesfile in files:
                if changesfile == aggregate or not changesfile.endswith(".changes"):
                    continue
                with open(os.path.join(root,changesfile), "r") as f:
                    lines += f.readlines()
        lines = sorted(lines, key=lambda r: int(r.split("\t")[0]))
        with open(os.path.join(metadir, aggregate), "w") as f:
            f.writelines(lines)

    def fixup_permissions(self):
        """ Fix permissions under the data directory

        This means applying the data directory's permissions and ownership to all underlying parts.

        If this fails due to insufficient privileges then it just prints a warning and continues on.
        """
        stat = os.stat(self.data)
        try:
            for root, dirs, files in os.walk(self.data):
                for name in files:
                    path = os.path.join(root, name)
                    os.chmod(path, stat.st_mode & 0o666)
                    os.chown(path, stat.st_uid, stat.st_gid)
                for name in dirs:
                    path = os.path.join(root, name)
                    os.chmod(path, stat.st_mode)
                    os.chown(path, stat.st_uid, stat.st_gid)

        except OSError:
            print("WARNING: Failed to set permissions under the data directory (not owned by process?) May need to be manually fixed.")




def clean_id(name, keep_slashes):
    """
    Return a 'clean' dokuwiki-compliant name. Based on the cleanID() PHP function in inc/pageutils.php
    """
    main,ext = os.path.splitext(name)
    if keep_slashes:
        regex = r'[^\w/]+'
    else:
        regex = r'\W+'
    result = (re.sub(regex, '_', main) + ext).lower()
    while "__" in result:
        result = result.replace("__", "_") # this is a hack, unsure why regex doesn't catch it
    return result

def get_timestamp(node):
    """
    Return a dokuwiki-Comaptible Unix int timestamp for a mediawiki API page/image/revision
    """
    return int(simplemediawiki.MediaWiki.parse_date(node['timestamp']).timestamp())

def ensure_directory_exists(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def make_dokuwiki_pagename(mediawiki_name):
    """
    Convert a canonical mediawiki pagename to a dokuwiki pagename
    """
    result = mediawiki_name.replace(" ","_")
    return clean_id(camel_to_underscore(result), True)

def camel_to_underscore(camelcase):
    """
    Convert a camelcased string to underscore_delimited (tweaked from this StackOverflow answer)
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
    """
    s1 = re.sub('(^_)([A-Z][a-z]+)', r'\1_\2', camelcase)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()    
