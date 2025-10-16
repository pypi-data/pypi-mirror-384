# encoding: utf-8

'''Make numerous symlinks separated into validation and discovery folders for BBD
and DCIS images.

1. Run this before publishing to get the symlinks in the right place so publishing
can actually publish them.
2. Then, run the publication pipeline.
3. Then, run bbd_dcis_population to add the fields to Solr from the Excel files.

Typical invocation:

cd /usr/local/labcas/Documents/Clients/JPL/Cancer/LabCAS/Development/jpl.labcas.utils
git pull
.venv/bin/pip install --editable .
.venv/bin/restructure-bbd-dcis bbd.csv /labcas-data/labcas-backend/archive/edrn/BBD_Pathology_Slide_Images
'''

import logging, argparse, csv, os, glob

from .argparse import add_logging_argparse_options

_logger = logging.getLogger(__name__)


def _unlink(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _found(filename: str, source_dir: str) -> str | None:
    '''Return the first matching partial `filename` found in `source_dir`.
    
    If no match is found, return `None`.
    '''
    for dirpath, _, filenames in os.walk(source_dir):
        if 'Source' in dirpath:
            _logger.debug('Skipping directory %s', dirpath)
            continue
        pattern = os.path.join(dirpath, f"{filename}.*")
        matches = glob.glob(pattern)
        if matches:
            _logger.debug('🔍 Found %r in %s', matches, dirpath)
            return matches[0]
    return None


def _make_symlinks(spreadsheet: str, target_dir: str, dryrun: bool):
    with open(spreadsheet, 'r') as io:
        reader = csv.reader(io)
        for row in reader:
            # Skip the header and the weird row with SECTION NOT AVAILABLE in it
            if row[8] == 'RefSetGroup' or row[0] == 'SECTION NOT AVAILABLE': continue
            f = _found(row[4], target_dir)
            if f is None:
                _logger.info('🤷 No match found for %s', row[4])
                continue
            is_discovery = row[8] == 'Discovery'
            destination = os.path.join(
                target_dir, 'Discovery' if is_discovery else 'Validation', os.path.basename(f)
            )
            f, destination = os.path.abspath(f), os.path.abspath(destination)
            if dryrun:
                _logger.info('🌵 Dry run; would have symlinked %s to %s', f, destination)
            else:
                _logger.info('🔗 Symlinking %s to %s', f, destination)
                _unlink(destination)
                os.symlink(f, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_logging_argparse_options(parser)
    parser.add_argument('spreadsheet', type=str, help='The BBD or DCIS spreadsheet to process')
    parser.add_argument('target_dir', type=str, help='Where to find and also make symlinks')
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    os.makedirs(os.path.join(args.target_dir, 'Validation'), exist_ok=True)
    os.makedirs(os.path.join(args.target_dir, 'Discovery'), exist_ok=True)
    _logger.info('🔍 Processing spreadsheet: %s', args.spreadsheet)
    _make_symlinks(args.spreadsheet, args.target_dir, args.dryrun)


if __name__ == '__main__':
    main()
