"""
Simple name munging functions used by both yamdwe.py and yamdwe_users.py

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.
"""
import re, os.path, unicodedata, urllib

def clean_id(name):
    """
    Return a 'clean' dokuwiki-compliant name. Based on the cleanID() PHP function in inc/pageutils.php

    Ignores both slashes and colons as valid namespace choices (to convert slashes to colons,
    call make_dokuwiki_pagename)
    """
    # decode URL-ecoded characters
    name=urllib.unquote(name)

    main,ext = os.path.splitext(name)

    # remove accents
    try:
        decomposed = unicodedata.normalize("NFKD", main)
        no_accent = ''.join(c for c in decomposed if ord(c)<0x7f)
    except TypeError:
        no_accent = main # name was plaintext to begin with

    # recombine without any other characters
#    result = (re.sub(r'[^\w/:]+', '_', no_accent) + ext).lower()
    result = (re.sub(r'[^\w]+', '_', no_accent) + ext).lower()
    while "__" in result:
        result = result.replace("__", "_") # this is a hack, unsure why regex doesn't catch it
    # remove heading and trailing underscores
    result=re.sub('^_|_$', '', result)
    return result

def clean_user(name):
    """
    Return a 'clean' dokuwiki-authplain-compliant username.
    Based on the cleanUser() PHP function in lib/plugins/authplain/auth.php
    """
    return clean_id(name).replace(":","_")

