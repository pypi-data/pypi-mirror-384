# encoding: utf-8

'''Populate the BBD and DCIS collections in Solr with with the fields from the CSV files.

Typical invocation: `rm -f nohup.out; nohup .venv/bin/populate-bbd-dcis bbd.csv bbd &`
'''

import logging, argparse, csv, os, pysolr

from .argparse import add_standard_argparse_options

_logger = logging.getLogger(__name__)


_shortcut_to_collection_id = {
    'bbd': 'BBD_Pathology_Slide_Images',
    'dcis': 'DCIS_Pathology_Slide_Images',
}
_shortcut_to_field_name = {
    'bbd': 'New BBD ID',
    'dcis': 'New DCIS ID',
}

def _populate_solr(spreadsheet: str, solr: pysolr.Solr, collection_shortcut: str, dryrun: bool):
    cid = _shortcut_to_collection_id[collection_shortcut]
    field_name = _shortcut_to_field_name[collection_shortcut]

    _logger.debug(
        '🧑‍🧑‍🧒‍🧒 Populating Solr at %s with "%s" for collection "%s", field "%s", dryrun=%r',
        solr.url, spreadsheet, cid, field_name, dryrun
    )

    with open(spreadsheet, 'r') as io:
        reader = csv.reader(io)
        for row in reader:
            # Skip the header and the weird row with SECTION NOT AVAILABLE in it
            if row[8] == 'RefSetGroup' or row[0] == 'SECTION NOT AVAILABLE': continue
            fn = row[4]  # Does HK want any other fields?
            query = f'CollectionId:"{cid}" AND (FileName:{fn}.svs OR FileName:{fn}.scn)'
            results = solr.search(query, fl=['id'], start=0, rows=9999)
            if len(results) == 0:
                _logger.warning('⚠️ No results for %s', query)
                continue
            for doc in results:
                _logger.info('✍️ Updating %s with "%s"', doc['id'], fn)
                update = {'id': doc['id'], field_name: {'set': [fn]}}
                if dryrun:
                    _logger.info(
                        '🌵 Dry run; would have updated %s field %s set to "%s"',
                        doc['id'], field_name, fn
                    )
                else:
                    solr.add(update, commit=True)
                    _logger.info(
                        '✅ Updated %s field %s set to "%s"', doc['id'],
                        field_name, fn
                    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('spreadsheet', help='The CSV file with the fields to use to populate.')
    parser.add_argument(
        'collection_shortcut', help='What collection to update', choices=['bbd', 'dcis']
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + 'files', always_commit=True, verify=False)
    _populate_solr(args.spreadsheet, solr, args.collection_shortcut, args.dryrun)


if __name__ == '__main__':
    main()
