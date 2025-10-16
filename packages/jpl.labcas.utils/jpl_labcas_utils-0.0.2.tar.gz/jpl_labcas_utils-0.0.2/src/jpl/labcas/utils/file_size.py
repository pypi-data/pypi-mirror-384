# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: report total size in bytes of all files.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        'query', help='Query to select files to report on; default "%(default)s"',
        default='Consortium:EDRN'
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = pysolr.Solr(args.solr + 'files', always_commit=True, verify=False)

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
