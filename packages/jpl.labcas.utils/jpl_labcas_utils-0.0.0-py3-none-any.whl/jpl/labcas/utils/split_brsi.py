# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: split BRSI files. BRSI stands for "Breast Reference Set
Images".

This will open and extract a GZIP'd tar file and will split the contents based
on an Excel spreadsheet (exported to CSV).

The splitting is done per:
https://github.com/EDRN/EDRN-metadata/issues/97#issuecomment-2045737597
'''

from .argparse import add_logging_argparse_options
import argparse, sys, csv, logging, dataclasses, os, tarfile


_logger = logging.getLogger(__name__)


__doc__ = 'Split BRSI archives into training and validation directories'


@dataclasses.dataclass(order=True, frozen=True)
class BRSIFile:
    '''Overkill.

    All we needed was a mapping from jpl_id to a boolean. Oh well.
    '''
    jpl_id: str = dataclasses.field(hash=True)
    training: bool = dataclasses.field(hash=False, repr=True)


def _read_spreadsheet(spreadsheet_input):
    '''Read the `spreadsheet_input` and return a mapping of `jpl_id` → `BRSIFile`.'''
    classifications = {}
    try:
        reader = csv.reader(spreadsheet_input)
        for row in reader:
            if row[0] == 'Ppt ID': continue
            training, validation, jpl_id = row[5].strip(), row[6].strip(), row[9].strip()
            training, validation = training == 'Yes', validation == 'Yes'
            if not training and not validation:
                _logger.info('File %s in the spreadsheet is neither training nor validation so ignoring', jpl_id)
            classifications[jpl_id] = BRSIFile(jpl_id, training)
    finally:
        spreadsheet_input.close()
    return classifications


def _jpl_id(filepath: str) -> str:
    '''Get the "JPL ID" out of the given `filepath`.'''
    return filepath.split('/')[-1][0:6]


def _find_files(tar: tarfile):
    '''Yield only file entries in the given `tar`.'''
    for tarinfo in tar:
        if tarinfo.isfile(): yield tarinfo


def _classify_files(tf_gen, classifications: dict):
    '''Classify the given `TarInfo`s according to the `classifications` and if found, yield the `tf`
    and whether it's training or not.

    This annotates each `TarInfo` with a boolean (`True` = training, `False` = validation).
    '''
    for tf in tf_gen:
        classification = classifications.get(_jpl_id(tf.name))
        if classification:
            yield tf, classification.training
        else:
            _logger.info('Tar file %s not found in spreadsheeet, ignoring', tf.name)


def _filter_training_files(annotated_tf_gen, training):
    '''Yield only those annotated `TarInfo`s that match the boolean `training`.'''
    for tf, was_training in annotated_tf_gen:
        if was_training == training:
            yield tf


def _sort_files(classifications: dict, archive: argparse.FileType, training: str, validation: str):
    '''Extract files from the given `archive` and sort them into `training` and `validation`
    directories based on the `classifications`.
    '''
    with tarfile.open(mode='r', fileobj=archive) as tar:
        tar.extractall(
            path=training,
            members=_filter_training_files(_classify_files(_find_files(tar), classifications), training=True)
        )
        tar.extractall(
            path=validation,
            members=_filter_training_files(_classify_files(_find_files(tar), classifications), training=False)
        )


def main():
    '''Do it.'''
    parser = argparse.ArgumentParser(description=__doc__)
    add_logging_argparse_options(parser)
    parser.add_argument('csv', type=argparse.FileType('r'), help='Spreadsheet')
    parser.add_argument('archive', type=argparse.FileType('rb'), help="GZIP'd archive file")
    parser.add_argument('target', help='Target directory')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    os.makedirs(args.target, exist_ok=True)
    training, validation = os.path.join(args.target, 'training'), os.path.join(args.target, 'validation')
    os.makedirs(training, exist_ok=True)
    os.makedirs(validation, exist_ok=True)
    classifications = _read_spreadsheet(args.csv)
    _sort_files(classifications, args.archive, training, validation)
    sys.exit(0)


if __name__ == '__main__':
    main()
