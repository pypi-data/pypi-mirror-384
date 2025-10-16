# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: generate annual report which provides

- Number of collections
- Number of datasets
- Number of files
- Total size of files in bytes, kilobytes, megabytes, gigabytes, terabytes

for both EDRN and MCL and since a given date.

Note: this doesn't work.
'''

from . import VERSION
from .const import DEFAULT_SOLR_URL
from .argparse import add_logging_argparse_options
from .solr import find_documents
from datetime import date
import argparse, sys, pysolr, logging


_logger = logging.getLogger(__name__)
_mcl_solr_url = 'https://localhost:8985/solr/'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    add_logging_argparse_options(parser)
    parser.add_argument(
        '-e', '--edrn', metavar='EDRN', default=DEFAULT_SOLR_URL, help='EDRN Solr URL (default %(default)s)'
    )
    parser.add_argument(
        '-m', '--mcl', metavar='MCL', default=_mcl_solr_url, help='MCL Solr URL (default %(default)s)'
    )
    parser.add_argument('DATE', help='Date to report on (YYYY-MM-DD)')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')

    edrn_url = args.edrn if args.edrn.endswith('/') else args.edrn + '/'
    mcl_url = args.mcl if args.mcl.endswith('/') else args.mcl + '/'
    since = date.fromisoformat(args.DATE)
    for label, url in (('EDRN', edrn_url), ('MCL', mcl_url)):
        report_collections(label, url, since)
        report_datasets(label, url, since)
        report_files(label, url, since)

    sys.exit(0)


def report_collections(url, since):

    edrn_solr = pysolr.Solr(edrn_url + 'files', always_commit=True, verify=False)
    mcl_solr = pysolr.Solr(mcl_url + 'files', always_commit=True, verify=False)

    since = date.fromisoformat(args.DATE)
    edrn_collections = find_collections(edrn_solr, since)
    mcl_collections = find_collections(mcl_solr, since)

    edrn_datasets = find_datasets(edrn_solr, since)
    mcl_datasets = find_datasets(mcl_solr, since)

    edrn_files = find_files(edrn_solr, since)
    mcl_files = find_files(mcl_solr, since)


    total, count = 0, 0
    for match in find_documents(solr, args.query, ['id', 'FileSize']):
        count += 1
        ident, size_str = match.get('id', '«unknown»'), match.get('FileSize', None)
        if size_str is None:
            _logger.warning('File «%s» has no FileSize; ignoring', ident)
            continue
        total += int(size_str)
        if count % 1000 == 0:
            _logger.info('Processed %d files, size so far is %d GB', count, total/1024/1024/1024)

    print(f'Number of files: {count}')

    kilobytes = int(total / 1024)
    megabytes = int(total / 1024 / 1024)
    gigabytes = int(total / 1024 / 1024 / 1024)
    terabytes = int(total / 1024 / 1024 / 1024 / 1024)
    print(
        f'Total size: {total} bytes ({kilobytes} KB, {megabytes} MB, {gigabytes} GB,'
        f' {terabytes} TB)'
    )
    sys.exit(0)


if __name__ == '__main__':
    main()
