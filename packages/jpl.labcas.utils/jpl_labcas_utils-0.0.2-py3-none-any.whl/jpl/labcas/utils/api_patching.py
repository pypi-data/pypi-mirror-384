# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: patch DICOM files and Solr metadata based on info from the
DMCC API.

This … not sure how this'll work
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
from .dmcc_api import dmcc_authenticate, get_image_events
from .const import DEFAULT_TOKEN_ID, DEFAULT_PROTOCOL
import argparse, sys, pysolr, logging, pydicom, os.path, os, getpass


_logger = logging.getLogger(__name__)
__doc__ = 'Add data from DMCC to DICOM files and Solr'


def _patch(doc: dict, event, solr, dryrun: bool):
    '''Patch the DICOM file and metadata in `solr` described by `doc` with the info in `event`.'''

    # `doc` is the search result from Solr and has `id` (single value), `RealFileLocation` (list of single
    # value), and `name` (list of single value).
    #
    # `event` is from the DMCC and has fields `participantId`, `siteId`, `imageEventIdentifier`, `visitTypeText`,
    # `imageTypeText`, and `protocolId`
    #
    # Assemble the DICOM filename from `RealFileLocation` and `name`.
    #
    # This is TBD!
    breakpoint()


def _patch_files_and_metadata(events: list, solr: pysolr.Solr, dryrun: bool):
    '''Patch all files and Solr metadata by using `solr` and the information in `events`.'''

    # In DMCC it's `imageEventIdentifier`, but in Solr it's `eventID`
    for event in events:
        event_id = event['imageEventIdentifier']
        found_doc = False
        for doc in find_documents(solr, f'eventID:{event_id}', ['id', 'RealFileLocation', 'name']):
            found_doc = True
            _patch(doc, event, solr, dryrun)
        if not found_doc:
            _logger.info('No documents in Solr match DMCC event ID %s', event_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('-i', '--id', default=DEFAULT_TOKEN_ID, help='Client ID; default %(default)s')
    parser.add_argument(
        '-w', '--secret', help='Client secret; will use CLIENT_SECRET env var if not given, or will prompt for it'
    )
    parser.add_argument('-p', '--protocol', default=str(DEFAULT_PROTOCOL), help='Protocol ID, defaults to %(default)s')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + 'files', always_commit=True, verify=False)
    secret = args.secret
    if not secret:
        secret = os.getenv('CLIENT_SECRET')
        if not secret:
            secret = getpass.getpass('Client secret: ')
    protocol = int(args.protocol)
    token = dmcc_authenticate(args.id, secret)
    events = get_image_events(protocol, token)
    _patch_files_and_metadata(events, solr, args.dryrun)

    sys.exit(0)


if __name__ == '__main__':
    main()
