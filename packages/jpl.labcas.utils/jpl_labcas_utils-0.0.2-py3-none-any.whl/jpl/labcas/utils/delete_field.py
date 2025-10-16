# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: delete field.

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will go through documents and delete a named field.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    parser.add_argument('field', help='Field to delete')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = pysolr.Solr(args.solr + args.core, always_commit=True, verify=False)

    query_field, count = args.field.replace(':', '\\:'), 0
    for result in find_documents(solr, f'{query_field}:*', None):
        del result[args.field]
        del result['_version_']
        solr.add([result])
        count += 1
        if count % 100 == 0:
            _logger.info('Completed %d documents', count)
    sys.exit(0)


if __name__ == '__main__':
    main()
