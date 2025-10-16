# encoding: utf-8

'''Find the missing anonymized BBD or DCIS images from a given spreadsheet by traversing
the /labcas-data/amahabal/HandE_Images_from_KUMC directory.

This uses the `E` column of the spreadsheet since apparenty the files are named
after the "New BBD ID" or "New DCIS ID" column (column 4 after zero index).
'''

import logging, argparse, csv, os, glob

from .argparse import add_logging_argparse_options

_logger = logging.getLogger(__name__)


def _found(filename: str, source_dir: str) -> bool:
    for dirpath, _, filenames in os.walk(source_dir):
        pattern = os.path.join(dirpath, f"{filename}.*")
        matches = glob.glob(pattern)
        if matches:
            _logger.debug('🔍 Found %s.* in %s', filename, dirpath)
            return True
    return False


def _find_missing_images(spreadsheet: str, source_dir: str):
    with open(spreadsheet, 'r') as io:
        reader = csv.reader(io)
        for row in reader:
            # Skip the header and the weird row with SECTION NOT AVAILABLE in it
            if row[8] == 'RefSetGroup' or row[0] == 'SECTION NOT AVAILABLE': continue
            if not _found(row[4], source_dir): print(row[4])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_logging_argparse_options(parser)
    parser.add_argument('spreadsheet', type=str, help='The BBD or DCIS spreadsheet to process')
    parser.add_argument('source_dir', type=str, help='Where to find the original DICOM files')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    _logger.info('🔍 Processing spreadsheet: %s', args.spreadsheet)
    _find_missing_images(args.spreadsheet, args.source_dir)


if __name__ == '__main__':
    main()
