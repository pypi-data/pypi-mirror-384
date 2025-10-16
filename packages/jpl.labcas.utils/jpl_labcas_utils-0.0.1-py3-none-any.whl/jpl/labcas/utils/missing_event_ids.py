'''🛠️ JPL LabCAS Utilities: report missing event IDs.

Given event IDs, report which are missing in LabCAS Solr.

Typical usage: .venv/bin/missing-event-ids 1635113 9353978 xxxyyzz
Or: awk -F, '{print $1}' BLINDED_PairID.to.Event.Identifier.with.BlindedID.csv | xargs .venv/bin/missing-event-ids > missing-event-ids.txt

This writes to stdout the event IDs that are not found in the files core in Solr.

Supports https://github.com/EDRN/EDRN-metadata/issues/151#issuecomment-3215362878 (this comment specifically under "Add new verification).
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, os.path, json, re


_logger = logging.getLogger(__name__)
__doc__ = 'Report missing event IDs'


def _report_missing_event_ids(solr: pysolr.Solr, event_ids: list[str]):
    for event_id in event_ids:
        _logger.info('🔍 Checking for event ID %s', event_id)
        query = f'eventID:{event_id}'
        results = solr.search(query, rows=0)
        if results.hits == 0:
            print(event_id)
        else:
            _logger.info('🔍 %d results found for event ID %s', results.hits, event_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('event_ids', nargs='+', help='The event IDs to check')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + 'files', always_commit=True, verify=False)
    event_ids = sorted(list(set(args.event_ids)))
    _report_missing_event_ids(solr, event_ids)
    sys.exit(0)


if __name__ == '__main__':
    main()
