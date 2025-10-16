# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: fix patient IDs in "Lung Team Project 2" `.dcm` files for 

This queries Solr for all files matching a given query and replaces the DICOM patient ID
header with the event ID as dictated by Solr.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, pydicom, os.path


_logger = logging.getLogger(__name__)
__doc__ = 'Replace patient IDs in DICOM files with event IDs'


def _replace_patient_IDs(solr: pysolr.Solr, query: str, dryrun: bool):
    count = 0
    for doc in find_documents(solr, query, ['id', 'RealFileLocation', 'name', 'eventID']):
        doc_id, event_id = doc['id'], doc.get('eventID', [None])[0]
        dn, fn = doc.get('RealFileLocation', [None])[0], doc.get('name', [None])[0]
        count += 1
        if event_id is None:
            _logger.warning('No "eventID" for %s; skipping', event_id)
            continue
        if dn is None:
            _logger.warning('No "RealFileLocation" for %s; skipping', doc_id)
            continue
        if fn is None:
            _logger.warning('No "name" for %s; skipping', doc_id)
            continue
        actual_file = os.path.join(dn, fn)
        if not os.path.exists(actual_file):
            _logger.warning('Solr doc %s, file %s, does not exist; skipping', doc_id, actual_file)
            continue
        elif os.path.isdir(actual_file):
            _logger.warning('Solr doc %s, file %s, is actually a directory; skipping', doc_id, actual_file)
        else:
            try:
                dcm = pydicom.dcmread(actual_file)
                if dryrun:
                    _logger.info('DRY RUN NOT PATCHING %s', actual_file)
                else:
                    if dcm.PatientID != event_id:
                        _logger.info('PATCHING %s with event ID %s', actual_file, event_id)
                        dcm.PatientID = event_id
                        dcm.save_as(actual_file)
            except Exception as ex:
                _logger.warning('Exception %s reading/writing %s for Solr doc %s; skipping', ex, actual_file, doc_id)
                continue
        if count % 1000 == 0:
            _logger.info('Processed %d Solr entries so far', count)

    _logger.info('Total Solr entries retrieved: %d', count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    parser.add_argument('query', help='Solr query to select files to update')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    solr = pysolr.Solr(solr_url + 'files', always_commit=True, verify=False)

    _replace_patient_IDs(solr, args.query, args.dryrun)
    sys.exit(0)

    # Example of overwriting a field in a DICOM file:
    #
    # fn = '1097_ser005img074_CTThoraxHigh_Lung.dcm'
    # try:
    #     dataset = pydicom.dcmread(fn)
    #     print('Before: Patient ID = ', dataset.PatientID)
    #     dataset.PatientID = args.query
    #     dataset.save_as(fn)
    # except Exception as ex:
    #     breakpoint()
    #     _logger.exception(ex)


if __name__ == '__main__':
    main()
