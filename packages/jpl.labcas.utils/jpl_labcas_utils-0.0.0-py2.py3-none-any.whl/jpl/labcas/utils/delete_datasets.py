# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: delete dataset.

To run this, first establish the `edrn-labcas-tunnels` on the JPL host,
since this'll make 8984 open to edrn-labcas on that host. Then run the
`jpl-tunnels` on the high speed development host, and that'll establish
the tunnels to the JPL host (MacBook Pro).

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will go through documents and delete datasets by given IDs.
While doing so it outputs a CSV file of all files that will need to
be removed from disk. The columns of this file are dataset ID,
file ID, and file path. The CSV goes to stdout.

It'll also delete all files under that dataset.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, csv

_logger = logging.getLogger(__name__)

_disk, _s3 = '/labcas-data', 's3://edrn-labcas/archive'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('datasetid', nargs='+', help='IDs of the datasets to delete (the id field)')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = args.solr if args.solr.endswith('/') else args.solr + '/'
    datasets_solr = pysolr.Solr(solr + 'datasets', always_commit=True, verify=False)
    files_solr = pysolr.Solr(solr + 'files', always_commit=True, verify=False)

    _logger.debug('Opening CSV writer')
    writer = csv.writer(sys.stdout)
    writer.writerow([
        'Dataset ID', 'File ID', 'LabCAS Prepublished File Location', 'LabCAS Published File Location', 'S3 Location'
    ])
    for given_dataset_id in args.datasetid:
        _logger.info('Processing given dataset ID %s', given_dataset_id)

        for dataset in find_documents(datasets_solr, f'id:{given_dataset_id}*', ['id']):
            dataset_id = dataset['id']

            _logger.info('Finding files for dataset "%s"', dataset_id)
            file_ids = []
            for file in find_documents(files_solr, f'DatasetId:"{dataset_id}"', ['id', 'FileLocation', 'FileName']):
                pre, post = f'{_disk}/{file["id"]}', f'{file["FileLocation"]}/{file["FileName"]}'
                s3 = f'{_s3}/{file["id"]}'
                writer.writerow([dataset_id, file['id'], pre, post, s3])
                file_ids.append(file['id'])

            _logger.info('Done finding files for %s, found %d; dry run=%r', dataset_id, len(file_ids), args.dryrun)
            if file_ids:
                _logger.info("Deleting (%r) from Solr: %r", not args.dryrun, ','.join(file_ids))
                if not args.dryrun:
                    files_solr.delete(id=file_ids)
                _logger.info("Deleting (%r) from Solr: %s", not args.dryrun, dataset_id)

            _logger.info('Now to delete (%r) the dataset %s', not args.dryrun, dataset_id)
            if not args.dryrun:
                datasets_solr.delete(id=dataset_id)

    sys.exit(0)


if __name__ == '__main__':
    main()
