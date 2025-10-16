# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: replace field.

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will take an existing document and replace a singly-valued list
field with a new single-value in a singly-valued list.
'''

from .argparse import add_standard_argparse_options
import argparse, sys, pysolr, logging
from typing import Iterable

_logger = logging.getLogger(__name__)


def _first(i: Iterable) -> object:
    iterator = iter(i)
    return next(iterator)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    parser.add_argument('id', help='ID of the document to update')
    parser.add_argument('field', help='List field whose values to replace')
    parser.add_argument('value', help='New single-item list value to replace with')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = pysolr.Solr(args.solr + args.core, always_commit=True, verify=False)

    # Now gather up the EDRN collections
    results = solr.search(q=f'id:{args.id}')
    if results.hits != 1:
        print(f'Unexpected number of hits for «{args.id}»: {results.hits}; aborting')
        sys.exit(-1)

    match = _first(results)
    match[args.field] = [args.value]
    del match['_version_']
    # Curiously, we don't have to delete the doc first … just adding it works to overwrite
    solr.add([match])
    sys.exit(0)


if __name__ == '__main__':
    main()
