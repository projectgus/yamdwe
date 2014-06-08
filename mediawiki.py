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
        pages = self._query(query, [ 'allpages' ])
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
        Slurp all images down from the mediawiki instance, latest revision only

        WARNING: Hits API hard, don't do this without knowledge/permission of wiki operator!!
        """
        query = {'list' : 'allimages'}
        return self._query(query, [ 'allimages' ])

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



