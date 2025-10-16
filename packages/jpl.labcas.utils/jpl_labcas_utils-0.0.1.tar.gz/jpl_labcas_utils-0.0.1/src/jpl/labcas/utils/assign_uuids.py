# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: assign UUIDs.

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will go through documents and, if there isn't a UUID element, will
assign one.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, uuid

_logger = logging.getLogger(__name__)

_disk, _s3 = '/labcas-data', 's3://edrn-labcas/archive'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = f'{args.solr}{args.core}' if args.solr.endswith('/') else f'{args.solr}/{args.core}'
    _logger.debug('Solr URL is %s', solr_url)
    solr = pysolr.Solr(solr_url, always_commit=True, verify=False)

    count = 0
    for doc in find_documents(solr, '*:*', None):
        existing_id = doc.get('uuid', None)
        if not existing_id:
            new_id = uuid.uuid4().urn  # Fully random UUID
            _logger.debug('Doc %s lacks UUID, assigning %s', doc['id'], new_id)
            doc['uuid'] = new_id
            del doc['_version_']
            count += 1
            if args.dryrun:
                _logger.info('Dry run: would be updating doc %s', doc['id'])
            else:
                solr.add(doc)
            if count % 1000 == 0:
                _logger.info(f'Processed {"(not really, dry run)" if args.dryrun else ""} %d so far', count)
        else:
            _logger.debug('Doc %s already has UUID %s', doc['id'], existing_id)

    sys.exit(0)


if __name__ == '__main__':
    main()
