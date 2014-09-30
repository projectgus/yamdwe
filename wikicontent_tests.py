#!/usr/bin/env python
"""Test suite for mediawiki->dokuwiki conversions.

Goes through every subdirectory of the tests/ directory. Each subdirectory contains:

* mediawiki.txt -> snippet of Mediawiki syntax to be converted.
* dokuwiki.txt -> correct Dokuwiki output to be expected.
* notes.txt -> (optional) file describing what's special about this test.

Converts mediawiki.txt and compares output to dokuwiki.txt, prints an
error (and contents of notes.txt) if the output does not match.

Copyright (C) 2014 Angus Gratton
Licensed under New BSD License as described in the file LICENSE.

"""
from __future__ import print_function, unicode_literals, absolute_import, division
import sys, os, codecs, inspect, traceback
from pprint import pprint
import wikicontent, yamdwe

DELIMITER="*"*40

def run_test(testdir):
    """
    Run the test contained in the directory 'testdir'

    Return True on success
    """
    print("Running %s..." % testdir)
    mw = _readfile(testdir, "mediawiki.txt")
    dw = _readfile(testdir, "dokuwiki.txt")
    notes = _readfile(testdir, "notes.txt")

    if len(mw) == 0:
        print("WARNING: No mediawiki input!!!")

    try:
        converted = wikicontent.convert_pagecontent("(test)", mw)
        if converted == dw:
            return True
    except:
        print("CONVERSION ERROR")
        traceback.print_exc()
        print(DELIMITER)
        if len(notes):
            print("Test notes:")
            print(notes)
        return False

    print("OUTPUT MISMATCH")
    if len(notes):
        print("Test notes:")
        print(notes)
    print(DELIMITER)
    print("Input Mediawiki:")
    print(mw)
    print(DELIMITER)
    print("Expected Output:")
    print(DELIMITER)
    print(dw)
    print(DELIMITER)
    print("Actual Output:")
    print(converted)
    print(DELIMITER)
    return False

def run_all_tests():
    """
    Run all tests. Return True on success.
    """
    successes = 0
    testsrun = 0
    execdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    testsdir = os.path.join(execdir, "tests")
    for test in os.listdir(testsdir):
        path = os.path.join(testsdir, test)
        if os.path.isdir(path):
            testsrun += 1
            if run_test(path):
                successes += 1
    print("--- %d/%d TESTS PASSED ---" % (successes, testsrun))
    return successes == testsrun

def _readfile(dirpath, filename):
    """
    Read a complete file and return content as a unicode string, or
    empty string if file not found
    """
    try:
        with codecs.open(os.path.join(dirpath, filename), "r", "utf-8") as f:
            return f.read()
    except IOError:
        return u""

if __name__ == "__main__":
    yamdwe.enable_unicode_output()
    if run_all_tests():
        sys.exit(0)
    else:
        sys.exit(1)
