# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: substitute the value of a field in multiple documents.

This takes a Solr URL, a core name, a field name, an existing value, and a replacement value.

For example:

    sub-field --url https://localhost:8987/solr/ files OwnerPrincipal cn=Feng cn=Zhang

will replace all occurrences of `cn=Feng` with `cn=Zhang` in the `OwnerPrincipal` field of all documents in the `files` core.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging


_logger = logging.getLogger(__name__)
__doc__ = 'Substitute the value of a field in multiple documents'
_batch_size = 100


def _replace(solr: pysolr.Solr, batch: list[dict], dryrun: bool):
    if dryrun:
        _logger.info('🌵 Dry run: would be replacing %d documents', len(batch))
    else:
        _logger.info('🔄 Replacing %d documents', len(batch))
        solr.add(batch)


def _substitute_values(solr: pysolr.Solr, field: str, old: str, new: str, dryrun: bool):
    count, replaced, batch, query = 0, 0, [], f'{field}:"{old}"'
    for match in find_documents(solr, query, ['OwnerPrincipal', 'id']):
        count += 1
        _logger.debug('Replacing attribute %s of doc %s with value %s', field, match['id'], new)
        doc_id, op = match['id'], match.get(field)
        if op is None:
            _logger.warning('🚨 Document %s has no %s field; skipping', doc_id, field)
            continue
        if isinstance(op, list):
            new_values = [new if i == old else i for i in op]
            batch.append({'id': doc_id, field: {'set': new_values}})
            replaced += 1
        elif isinstance(op, str):
            batch.append({'id': doc_id, field: {'set': new}})
            replaced += 1
        else:
            _logger.warning('🚨 Document %s has an unexpected %s field of type %s; skipping', doc_id, field, type(op))
            continue

        if replaced >= _batch_size:
            _replace(solr, batch, dryrun)
            batch, replaced = [], 0

        if count % 100 == 0:
            _logger.info('Processed %d documents', count)

    if len(batch) > 0:
        _replace(solr, batch, dryrun)

    _logger.info('Done after %d documents', count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    parser.add_argument('field', help='List field whose values to replace')
    parser.add_argument('old', help='Old value to replace')
    parser.add_argument('new', help='New value to replace with')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + args.core, always_commit=True, verify=False)

    _substitute_values(solr, args.field, args.old, args.new, args.dryrun)

    sys.exit(0)


if __name__ == '__main__':
    main()
