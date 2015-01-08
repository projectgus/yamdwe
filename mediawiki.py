"""
Methods for importing mediawiki pages, images via the simplemediawki
wrapper to the MediaWiki API.

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import simplemediawiki
import re
from pprint import pprint

class Importer(object):
    def __init__(self, api_url, http_user=None, http_pass="", wiki_user=None, wiki_pass=""):
        self.mw = simplemediawiki.MediaWiki(api_url,http_user=http_user,http_password=http_pass)
        # login if necessary
        if wiki_user is not None:
            print("Logging in as %s..." % wiki_user)
            if not self.mw.login(wiki_user, wiki_pass):
                raise RuntimeError("Mediawiki login failed. Wrong credentials?")

        # version check
        try:
            generator = "".join(self._query({'meta' : 'siteinfo'}, ['general', 'generator']))
            version = [ int(x) for x in re.search(r'[0-9.]+', generator).group(0).split(".") ] # list of [ 1, 19, 1 ] or similar
            if version[0] == 1 and version[1] < 13:
                raise RuntimeError("Mediawiki version is too old. Yamdwe requires 1.13 or newer. This install is %s" % generator)
            print("%s meets version requirements." % generator)
        except IndexError:
            raise RuntimeError("Failed to read Mediawiki siteinfo/generator. Is version older than 1.8? Yamdwe requires 1.13 or greater.")

    def get_all_pages(self):
        """
        Slurp all pages down from the mediawiki instance, together with all revisions including content.
        WARNING: Hits API hard, don't do this without knowledge/permission of wiki operator!!
        """
        query = {'list' : 'allpages'}
        print("Getting list of pages...")
        pages = self._query(query, [ 'allpages' ])
        
        print("Query page revisions...")
        for page in pages:
            page["revisions"] = self._get_revisions(page)
        return pages

    def _get_revisions(self, page):
        pageid = page['pageid']
        query = { 'prop' : 'revisions',
                  'pageids' : pageid,
                  'rvprop' : 'timestamp|user|comment|content',
                  'rvlimit' : '5',
                  }
        revisions = self._query(query, [ 'pages', str(pageid), 'revisions' ])
        return revisions

    def get_all_images(self):
        """
        Slurp all images down from the mediawiki instance, latest revision of each image, only.

        WARNING: Hits API hard, don't do this without knowledge/permission of wiki operator!!
        """
        query = {'list' : 'allimages'}
        return self._query(query, [ 'allimages' ])

    def get_all_users(self):
        """
        Slurp down all usernames from the mediawiki instance.
        """
        query = {'list' : 'allusers'}
        return self._query(query, [ 'allusers' ])

    def _query(self, args, path_to_result):
        """
        Make a Mediawiki API query that results a list of results,
        handle the possibility of making a paginated query using query-continue
        """
        query = { 'action' : 'query' }
        query.update(args)
        result = []
        continuations = 0
        while True:
            response = self.mw.call(query)

            # fish around in the response for our actual data (location depends on query)
            try:
                inner = response['query']
                for key in path_to_result:
                    inner = inner[key]
            except KeyError:
                raise RuntimeError("Mediawiki query '%s' returned unexpected response '%s' after %d continuations" % (args, response, continuations))
            result += inner

            # if there's a continuation, find the new arguments and follow them
            try:
                query.update(response['query-continue'][path_to_result[-1]])
                continuations += 1
            except KeyError:
                return result

    def get_all_namespaces(self):
        """
        Return a list of dictionaries, each containing the keys 
        'subpages' (non-empty=may contain subpages),'*' (Name), 
        'id' (numeric), 'canonical' (canonical name)
        """
        query = { 'action' : 'query', 'meta' : 'siteinfo', 'siprop' : 'namespaces|namespacealiases' }
        result = self.mw.call(query)['query']
        namespaces = result['namespaces'].values()
        return namespaces

    def get_file_namespaces(self):
        """
        Return a tuple. First entry is the name used by default for the file namespace (which dokuwiki will also use.)
        Second entry is a list of all aliases used for that namespace, and aliases used for the 'media' namespace.
        """
        query = { 'action' : 'query', 'meta' : 'siteinfo', 'siprop' : 'namespaces|namespacealiases' }
        result = self.mw.call(query)['query']
        namespaces = result['namespaces'].values()
        aliases = result.get('namespacealiases', {})
        file_namespace = {'*' : 'Files', 'canonical' : 'File'}
        media_namespace = {'*' : 'Media', 'canonical' : 'Media'}
        # search for the File namespace
        for namespace in namespaces:
            if namespace.get('canonical', None) == 'File':
                file_namespace = namespace
            elif namespace.get('canonical', None) == 'Media':
                media_namespace = namespace
        # alias list starts with the file & media namespace canonical values, and the media "real" value
        aliases_result = [ file_namespace['canonical'], media_namespace['canonical'], media_namespace['*'] ]
        # look for any aliases by searching the file namespace id, add to the list
        ids = [ file_namespace.get('id', None), media_namespace.get('id', None) ]
        for alias in aliases:
            if alias['id'] in ids:
                aliases_result.append(alias['*'])
        return file_namespace['*'], aliases_result

    def get_main_pagetitle(self):
        """
        Return the title of the main Mediawiki page
        """
        query = { 'action' : 'query', 'meta' : 'siteinfo', 'siprop' : 'general' }
        result = self.mw.call(query)['query']
        return result['general'].get("mainpage", "Main")




