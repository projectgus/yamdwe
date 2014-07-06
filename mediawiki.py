"""
Methods for importing mediawiki pages, images via the simplemediawki
wrapper to the MediaWiki API.

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import simplemediawiki
from pprint import pprint

class Importer(object):
    def __init__(self, api_url):
        self.mw = simplemediawiki.MediaWiki(api_url)

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
        while True:
            response = self.mw.call(query)
            # fish around in the response for our actual data (location depends on query)
            inner = response['query']
            for key in path_to_result:
                inner = inner[key]
            result += inner
            try:
                # if there's a continuation, its arguments are hiding here
                query.update(response['query-continue'][path_to_result[-1]])
            except KeyError:
                return result



