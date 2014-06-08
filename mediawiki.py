from pprint import pprint

def get_all_pages(mw):
    pages = []
    query = {'action' : 'query', 'list' : 'allpages'}
    try:
        while True:
            result = mw.call(query)
            pages += [page for page in result['query']['allpages']]
            query.update(result['query-continue']['allpages']) # set apfrom for next query
    except KeyError:
        return pages;


def get_revisions(mw, page):
    pageid = page['pageid']
    query = { 'action' : 'query',
              'prop' : 'revisions',
              'pageids' : pageid,
              'rvprop' : 'timestamp|user|comment|content',
              'rvlimit' : '5',
             }
    revisions = []
    try:
        while True:
            result = mw.call(query)
            revisions += result['query']['pages'][str(pageid)]['revisions']
            query.update(result['query-continue']['revisions']) # set apfrom for nex
    except KeyError:
        return revisions
