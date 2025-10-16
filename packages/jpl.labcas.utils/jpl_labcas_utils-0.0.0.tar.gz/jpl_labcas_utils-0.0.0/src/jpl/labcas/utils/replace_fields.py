# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: replace a field in multiple documents.

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will take an existing document and replace a list field with a new
items as given on the command line.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging


_logger = logging.getLogger(__name__)

__doc__ = 'Replace a field with new values in multiple documents'


def _show_identifiers(solr: pysolr.Solr, query: str):
    for match in find_documents(solr, query, ['id']):
        print(match['id'])


def _replace_values(solr: pysolr.Solr, query: str, field: str, values: list[str], dryrun: bool):
    count, replaced, proposed = 0, 0, set(values)
    for match in find_documents(solr, query, None):
        current = match.get(field, set())
        if current == proposed:
            _logger.debug('Doc %s already has expected values, skipping', match['id'])
            continue

        # Solr treats keys as case insensitive so when we try to change the case of a field
        # (such as ProtocolID → ProtocolId) it doesn't actually do anything, so let's delete
        # any fields without regard to case
        for key in match.keys():
            if key.lower() == field.lower():
                del match[key]
                break

        _logger.debug('Replacing attribute %s of doc %s with values  %r', field, match['id'], values)
        match[field] = values
        del match['_version_']

        if dryrun:
            _logger.info('Dry run: would be replacing document %s with new %s', match['id'], field)
            replaced += 1
        else:
            _logger.debug('Replacing document %s', match['id'])
            solr.add([match])
            replaced += 1

        count += 1
        if count % 100 == 0:
            _logger.info('Processed %d documents', count)

    _logger.info('Done! After %d documents I replaced %s in %d of them', count, field, replaced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-i', '--id', action='store_true',
        help='Select IDs only rather than make any changes; all command-line arguments must still be given'
    )
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    parser.add_argument('query', help='Query to select documents to update')
    parser.add_argument('field', help='List field whose values to replace')
    parser.add_argument('value', nargs='+', help='New values')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = pysolr.Solr(args.solr + args.core, always_commit=True, verify=False)

    if args.id:
        _show_identifiers(solr, args.query)
    else:
        _replace_values(solr, args.query, args.field, args.value, args.dryrun)

    sys.exit(0)


if __name__ == '__main__':
    main()
