'''🛠️ JPL LabCAS Utilities: fix event IDs in a the files core.

This will take an alias.json file and find in Solr's `files` core all
matching documents and will set the `labcasName` to have the proper underscore
with event ID as well as add the `eventID` field.

The alias.json file should already exist and is given as an command-line
argument.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, os.path, json, re


_logger = logging.getLogger(__name__)
__doc__ = 'Fix the event IDs in the files core'
_event_id_re = re.compile(r'_([0-9]+)\.[Dd][Cc][Mm]$')


def _update(solr: pysolr.Solr, doc: dict, aliased_path: str, aliased_file_name: str, new_event_id: str):
    _logger.info('✍️ Updating %s with path %s, file name %s, and event ID %s', doc['id'], aliased_path, aliased_file_name, new_event_id)
    update = {
        'id': doc['id'],
        'labcasId': {'set': [aliased_path]},
        'FileId': {'set': [aliased_path]},
        'labcasName': {'set': [aliased_file_name]},
        'FileName': {'set': [aliased_file_name]},
        'eventID': {'set': [new_event_id]},
    }
    solr.add(update, commit=True)


def _fix_event_ids(solr: pysolr.Solr, collection: str, aliases: str, dryrun: bool = True):
    with open(aliases, 'r') as io:
        aliases = json.load(io)
    for doc in find_documents(solr, f'CollectionId:{collection}', ['id', 'labcasName', 'eventID']):
        _logger.debug('🔎 CONSIDERING %s', doc['id'])
        identifier, labcas_name, event_id = doc['id'], doc.get('labcasName', [''])[0], doc.get('eventID', [''])[0]
        if identifier not in aliases:
            _logger.info('🤐 Skipping %s because it is not in the alias.json file', identifier)
            continue
        if '_' in labcas_name and event_id is not None and event_id != '':
            _logger.info('🎉 Skipping %s because it already has a proper labcas_name %s and event ID %s', identifier, labcas_name, event_id)
            continue
        
        # Special case: the alias might just be a filename + extension, in which case still don't have to do anything
        aliased_path = aliases[identifier]
        aliased_file_name = os.path.basename(aliased_path)
        event_id_matches = _event_id_re.search(aliased_file_name)
        if event_id_matches is None:
            _logger.info('❓ Skipping %s because it does not have an event ID in the aliased file name', identifier)
            continue
        new_event_id = event_id_matches.group(1)
        if dryrun:
            _logger.info(
                '🙂‍↔️ Not updating %s with path %s, file name %s, or event ID %s since this is a dry run',
                identifier, aliased_path, aliased_file_name, new_event_id
            )
        else:
            _update(solr, doc, aliased_path, aliased_file_name, new_event_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make changes, show them instead"
    )
    parser.add_argument('collection', help='ID of the collection to fix')
    parser.add_argument('aliases', help='The alias.json file to use')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + 'files', always_commit=True, verify=False)
    _fix_event_ids(solr, args.collection, args.aliases, args.dryrun)

    sys.exit(0)


if __name__ == '__main__':
    main()
