# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: generate various reports.'''


from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, csv, requests, os.path, re, collections, pydicom

_logger = logging.getLogger(__name__)
_event_id_re = re.compile(r'/([0-9]{7})/')


class Report:
    def execute(self, args: argparse.Namespace):
        raise NotImplementedError('🤪 Subclasses must implement this method')


class EventCorrelationReport(Report):
    def execute(self, args: argparse.Namespace):
        '''Correlate event IDs in Solr with those in the given CSV file.'''

        # Gather all the event IDs in the CSV file
        suzanna_event_ids = dict()
        with open(args.csv, 'r', newline='') as io:
            reader = csv.reader(io)
            for row in reader:
                if row[0] == 'STUDY_PARTICIPANT_ID': continue  # skip header
                # For Prostate_MRI `pmri.csv`:
                # ppt_id, event_id, site_id = row
                # For Lung_Team_Project_2 `ltp2.csv`:
                ppt_id, event_id = row
                site_id = ppt_id[0:3]
                suzanna_event_ids[event_id] = (site_id, ppt_id)

        # Gather all the event IDs for Prostate_MRI in Solr
        blindings, solr, files = dict(), pysolr.Solr(args.solr + 'files', verify=False), 0
        # for doc in find_documents(solr, 'CollectionId:Prostate_MRI', ['eventID', 'BlindedSiteID']):
        for doc in find_documents(solr, 'CollectionId:Lung_Team_Project_2', ['eventID', 'BlindedSiteID']):
            files += 1
            if files % 1000 == 0: _logger.info('Read through %d files', files)
            event_id = doc.get('eventID', [None])[0]
            if not event_id: continue  # skipping those without event IDs
            site_id = doc.get('BlindedSiteID', [None])[0]
            if not site_id: continue  # skip those without blinded site IDs
            blindings[event_id] = site_id

        only_in_suzanna = set(suzanna_event_ids.keys()) - set(blindings.keys())
        only_in_solr = set(blindings.keys()) - set(suzanna_event_ids.keys())

        writer = csv.writer(sys.stdout)
        writer.writerow(['Event ID', 'Only in Suzanna Site ID', 'Participant ID'])
        for e in only_in_suzanna:
            writer.writerow([e, suzanna_event_ids[e][0], suzanna_event_ids[e][1]])
        for e in only_in_solr:
            raise ValueError('should not happen')
            # writer.writerow([e, f'Only in Solr for site {blindings[e]}', '«unknown»'])


class PatientIDsReport(Report):
    def execute(self, args: argparse.Namespace):
        if args.folder is None:
            raise ValueError('🤷‍♂️ Folder is required for patientids report')
        event_ids = collections.defaultdict(set)
        for dirpath, _, filenames in os.walk(args.folder):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                possible_event_id = _event_id_re.search(file_path)
                if possible_event_id is not None:
                    event_id = possible_event_id.group(1)
                    try:
                        dcm = pydicom.dcmread(file_path)
                        event_ids[event_id].add(dcm.PatientID)
                        print(f'🔬 For event ID {event_id} found patient ID {dcm.PatientID} in {file_path}')
                    except Exception as ex:
                        _logger.warning('🤷‍♂️ Error reading as DICOM file %s: %r', file_path, ex)
                        continue
                else:
                    _logger.warning('🏟️ No event ID matched in file path %s; skipping', file_path)
                    continue

        writer = csv.writer(sys.stdout)
        writer.writerow(['Event ID', 'Patient IDs'])
        for event_id, patient_ids in event_ids.items():
            writer.writerow([event_id, '|'.join(patient_ids)])


class AvailabilityReport(Report):
    def _get_file_path(self, doc: dict) -> str:
        '''This reproduces the logic in `DownloadServiceImpl.java` in the LabCAS backend.'''

        # LabCAS Solr is so weird; `FileLocation` and `FileName` are strings, but
        # `name` is an array of strings.
        file_directory = doc.get('FileLocation', None)
        if file_directory is None: return None
        file_name, name = doc.get('FileName', None), doc.get('name', [None])[0]
        if name is not None and len(name) > 0:
            return os.path.join(file_directory, name)
        elif file_name is not None and len(file_name) > 0:
            return os.path.join(file_directory, file_name)
        else:
            return None

    def execute(self, args: argparse.Namespace):
        with open('missing.csv', 'w', newline='') as io:
            writer = csv.writer(io)
            writer.writerow(['LabCAS ID', 'File Path'])
            solr = pysolr.Solr(args.solr + 'files', verify=False)
            for doc in find_documents(solr, '*:*', ['FileLocation', 'FileName', 'name', 'id']):
                labcas_id, file_path = doc.get('id', None), self._get_file_path(doc)
                if labcas_id is None:
                    _logger.warning('No ID field for %r', doc)
                    continue
                if not file_path:
                    _logger.warning('No file path for %s', id)
                    continue
                if not os.path.isfile(file_path):
                    writer.writerow([labcas_id, file_path])


class EventIDReport(Report):
    def execute(self, args: argparse.Namespace):
        # Make a dict that maps from blinded site ID to a set of event IDs
        _collections_with_event_IDs = [
            'Lung_Team_Project_2',
            'Prostate_MRI'
        ]
        blindings, solr, files = dict(), pysolr.Solr(args.solr + 'files', verify=False), 0
        for collection in _collections_with_event_IDs:
            for doc in find_documents(solr, f'CollectionId:{collection}', ['eventID', 'BlindedSiteID']):
                files += 1
                if files % 1000 == 0: _logger.info('Processed %d files', files)
                event_id = doc.get('eventID', [None])[0]
                if not event_id: continue  # skipping those without event IDs
                blind = doc.get('BlindedSiteID', [None])[0]
                if not blind: continue  # same without blinding
                events_collection_pairs = blindings.get(blind, set())
                pair = (event_id, collection)
                events_collection_pairs.add(pair)
                blindings[blind] = events_collection_pairs

        writer = csv.writer(sys.stdout)
        writer.writerow(['Blinded Site ID', 'Collection ID', 'Event ID'])
        for blinded_site_id, events in blindings.items():
            for events_collection_pairs in events:
                writer.writerow([blinded_site_id, events_collection_pairs[1], events_collection_pairs[0]])

class PrivacyReport(Report):
    def execute(self, args: argparse.Namespace):
        _privacy_fields = [
            'dicom_EthnicGroup',
            'dicom_Occupation',
            'dicom_PatientAddress',
            'dicom_PatientBirthDate',
            'dicom_PatientBirthName',
            'dicom_PatientID',
            'dicom_PatientMotherBirthName',
            'dicom_PatientName',
            'dicom_PatientReligiousPreference',
            'dicom_PatientSex',
            'dicom_PatientTelephoneNumbers',
            'labcas.dicom:BirthDate',
            'labcas.dicom:ID',
            'labcas.dicom:Name',
            'labcas.dicom:PatientAddress',
            'labcas.dicom:Sex',
        ]
        _max_markdown = 15
        solr = pysolr.Solr(args.solr + 'files', verify=False)  # noqa
        with open('privacy.csv', 'w', newline='') as csvio, open('privacy.md', 'w') as mdio:
            writer = csv.writer(csvio)
            writer.writerow(('Field', 'Count', 'Value'))
            for field_name in _privacy_fields:
                # Trying the "Luke" handler for now; see
                # https://solr.apache.org/guide/8_7/luke-request-handler.html
                luke_url = f'{args.solr}files/admin/luke?numTerms=999999&wt=json&fl={field_name}'
                results = requests.get(luke_url, verify=False)
                try:
                    counts = results.json()['fields'][field_name]['topTerms']
                except KeyError:
                    continue

                # This gives different results:
                # results = solr.search(q='*:*', rows=0, facet='true', **{
                #     'facet.field': field_name,
                #     'facet.sort': 'count',
                #     'facet.limit': -1
                # })
                # counts = results.facets['facet_fields'][field_name]

                for v, c in zip(counts[0::2], counts[1::2]):
                    writer.writerow((field_name, c, v))
                counts = [f'`{v}`: {c}' for v, c in zip(counts[0::2], counts[1::2])]
                if len(counts) == 0:
                    print(f'- {field_name}: none', file=mdio)
                elif len(counts) > _max_markdown:
                    print(f'- {field_name}: {", ".join(counts[:_max_markdown])} …', file=mdio)
                else:
                    print(f'- {field_name}: {", ".join(counts)}', file=mdio)


# Register the reports by name
_reports = {
    'events': EventIDReport,
    'privacy': PrivacyReport,
    'eventcor': EventCorrelationReport,
    'availability': AvailabilityReport,
    'patientids': PatientIDsReport,
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('--csv', help="Suzanna's CSV file of event IDs in column 2 for eventcor report")
    parser.add_argument('--core', help='What Solr core to use (collections, datasets, files, etc.) for the field report')
    parser.add_argument('report', choices=_reports.keys(), help='What kind of report to make')
    parser.add_argument('folder', nargs='?', help='Folder to process for patientids report')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    report = _reports.get(args.report)
    if not report:
        raise ValueError(f'Unknown report: {args.report}')
    report().execute(args)
    sys.exit(0)


if __name__ == '__main__':
    main()
