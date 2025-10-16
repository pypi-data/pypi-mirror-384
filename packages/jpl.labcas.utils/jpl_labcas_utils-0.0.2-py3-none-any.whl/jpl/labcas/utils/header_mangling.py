# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: mangle DICOM headers and do other things.

To run: .venv/bin/mangle-headers BLINDED_PairID.to.Event.Identifier.with.BlindedID.csv data

See EDRN/EDRN-metadata#151 for the details.
'''

from . import VERSION
from .argparse import add_logging_argparse_options
from pathlib import Path
from .dcm_splitter import extract_bval
from pydicom.tag import Tag
from multiprocessing import Process, Queue, JoinableQueue
import argparse, sys, logging, pydicom, csv, re, time, humanize

_event_id_re = re.compile(r'/([0-9]{7})/')
_tag_to_delete = Tag((0x0400, 0x0561))  # "OriginalAttributesSequence", Adrian doesn't like it


_logger = logging.getLogger(__name__)
__doc__ = 'Mangle DICOM headers amongst other things'


def find_all_files(directory: str):
    '''Yield the full path to each file in `directory` and its subdirectories.'''
    root_path = Path(directory)
    for file_path in root_path.rglob("*"):
        if file_path.is_file():
            yield str(file_path)


def _load_event_ids(spreadsheet: str) -> dict:
    '''Load the event IDs to pair IDs plus visit code from the given spreadsheet.'''
    event_ids = {}
    with open(spreadsheet, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if 'Image Event Identifier' in row[0]: continue
            event_ids[row[0]] = (row[1], row[2])
    return event_ids


def _mangle(event_ids: dict, file_path: str):
    '''Mangle the DICOM headers of the file file_path using information in event_ids.'''
    try:
        _logger.debug('🔬 Reading DICOM file %s', file_path)
        dcm = pydicom.dcmread(file_path)
        possible_event_id = _event_id_re.search(file_path)
        if possible_event_id is not None:
            event_id = possible_event_id.group(1)
        else:
            _logger.warning('🏟️ No event ID matched in file path %s; skipping', file_path)
            return
        blinded_shuffled_pair_id, visit_code = event_ids.get(event_id, (None, None))
        if blinded_shuffled_pair_id is None:
            _logger.warning('🦯 HEATHER: No event ID %s found in CSV for file %s; skipping it', event_id, file_path)
            return
        _logger.info(
            '🦧 Mangling DCM file %s with pair ID %s, event ID %s, and visit code %s',
            file_path, blinded_shuffled_pair_id, event_id, visit_code
        )

        # Mangle these headers
        dcm.PatientID = blinded_shuffled_pair_id
        dcm.StudyID = event_id
        dcm.ClinicalTrialTimePointID = visit_code
        dcm.InstitutionName = 'Anonymous'
        dcm.PatientName = blinded_shuffled_pair_id

        # Extract the b-value and save it
        bval, _ = extract_bval(dcm)
        _logger.debug('Got b-value %f', bval)
        if bval is not None:
            dcm.DiffusionBValue = bval

        # Delete the tag Adrian doesn't like
        if _tag_to_delete in dcm:
            del dcm[_tag_to_delete]

        # Save the mangled DICOM file
        _logger.debug('💾 Saving mangled DICOM file %s', file_path)
        dcm.save_as(file_path)
    except Exception as ex:
        _logger.error('🤷 Error mangling %s: %r; maybe not a DICOM file?', file_path, ex)


def _file_producer(queue: Queue, folder: str, concurrency: int):
    '''Produce the files to mangle.'''
    for file_path in find_all_files(folder):
        _logger.debug('🏭 Producer putting file %s', file_path)
        queue.put(file_path)
    _logger.debug('🔚 Producer putting Nones to end the consumers')
    for _ in range(concurrency): queue.put(None)


def _file_consumer(queue: Queue, event_ids: dict):
    '''Consume the files to mangle.'''
    while True:
        file_path = queue.get()
        if file_path is None:
            _logger.debug('🔚 Consumer got None; signaling task done')
            queue.task_done()
            break
        _logger.debug('🍽️ Consumer got file %s; mangling', file_path)
        _mangle(event_ids, file_path)
        queue.task_done()


def _mangle_parallel(event_ids: dict, folder: str, concurrency: int):
    '''Mangle the DICOM headers of the files in `folder` in parallel.'''
    queue = JoinableQueue()
    _logger.debug('🏁 Starting producer')
    producer = Process(target=_file_producer, args=(queue, folder, concurrency))
    producer.start()
    _logger.debug('🏁 Starting %d consumers', concurrency)
    consumers = [Process(target=_file_consumer, args=(queue, event_ids)) for _ in range(concurrency)]
    for c in consumers: c.start()
    _logger.debug('🔚 Joining producer')
    producer.join()
    _logger.debug('🔚 Joining consumers')
    queue.join()
    for c in consumers: c.join()


def _mangle_serial(event_ids: dict, folder: str):
    '''Mangle the DICOM headers of the files in `folder` in serial.'''
    for file_path in find_all_files(folder):
        _mangle(event_ids, file_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument(
        '--concurrency', type=int, default=10,
        help='Number of concurrent processes to use; default is %(default)d'
    )
    add_logging_argparse_options(parser)
    parser.add_argument('spreadsheet', help='CSV file')
    parser.add_argument('folder', help='Folder containing DICOM files to mangle')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    event_ids = _load_event_ids(args.spreadsheet)

    time0 = time.monotonic()
    if args.concurrency > 1:
        _mangle_parallel(event_ids, args.folder, args.concurrency)
    elif args.concurrency == 1:
        _mangle_serial(event_ids, args.folder)
    else:
        raise ValueError(f'❌ Invalid concurrency: {args.concurrency}; must be 1 or greater')
    _logger.info('🏁 Mangling took %s', humanize.naturaldelta(time.monotonic() - time0))
    sys.exit(0)


if __name__ == '__main__':
    main()
