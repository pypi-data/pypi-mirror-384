# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: delete an entire collection.

It'll also delete all datasets and files under that collection.
'''

from .argparse import add_standard_argparse_options
import argparse, sys, pysolr, logging

_logger = logging.getLogger(__name__)


def _delete_files(collectionid: str, dryrun: bool, solr: pysolr.Solr):
    q = f'CollectionId:{collectionid}'
    if dryrun:
        logging.info('Dry run; would be calling delete on files with q=%s', q)
    else:
        logging.info('Deleting files matching q=%s', q)
        solr.delete(q=q)


def _delete_datasets(collectionid: str, dryrun: bool, solr: pysolr.Solr):
    q = f'CollectionId:{collectionid}'
    if dryrun:
        logging.info('Dry run; would be calling delete on datasets with q=%s', q)
    else:
        logging.info('Deleting datasets matching q=%s', q)
        solr.delete(q=q)


def _delete_collection(collectionid: str, dryrun: bool, c: pysolr.Solr, d: pysolr.Solr, f: pysolr.Solr):
    _delete_files(collectionid, dryrun, f)
    _delete_datasets(collectionid, dryrun, d)
    if dryrun:
        logging.info('Dry run; would be calling delete on collections with id=«%s»', collectionid)
    else:
        logging.info('Deleting collection «%s»', collectionid)
        c.delete(id=collectionid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument(
        '-c', '--confirm', action='store_true', help="Confirmed: don't ask for confirmation; hope you made backups"
    )
    parser.add_argument('collectionid', help='ID of the collection to delete (the id field)')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = args.solr if args.solr.endswith('/') else args.solr + '/'
    c = pysolr.Solr(solr + 'collections', always_commit=True, verify=False)
    d = pysolr.Solr(solr + 'datasets', always_commit=True, verify=False)
    f = pysolr.Solr(solr + 'files', always_commit=True, verify=False)

    if not args.dryrun:
        if not args.confirm:
            confirmation = input('This is a highly destructive action and hope you have backups! Proceed? ')
            if confirmation.lower() != 'yes':
                logging.warning('Aborted because user did not confirm')
                sys.exit(-1)

    _delete_collection(args.collectionid, args.dryrun, c, d, f)

    sys.exit(0)


if __name__ == '__main__':
    main()
