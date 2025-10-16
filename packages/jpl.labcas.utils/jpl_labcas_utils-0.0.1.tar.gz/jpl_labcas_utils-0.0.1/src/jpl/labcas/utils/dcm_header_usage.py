# encoding: utf-8

'''Show usage of DICOM headers in Lung_Team_Project_2 and Prostate_MRI collections.

See https://github.com/jpl-labcas/jpl.labcas.utils/issues/2 for more details.
'''

from . import VERSION
from .argparse import add_logging_argparse_options
from pydicom.errors import InvalidDicomError, BytesLengthException
from pydicom.sequence import Sequence
from pydicom.tag import Tag
from pydicom import datadict
from typing import Generator, Dict, Any
import argparse, logging, sys, os, time, humanize, pydicom, tempfile, gdown, csv, collections, re, multiprocessing, random


_logger = multiprocessing.log_to_stderr()
_default_spreadsheet_id = '1Q56vKzK0nB4UAkfLJnBOy6C-7wtHccvZkWYGQHTMpBw'
_site_re = re.compile(r'(Images_Site_[A-Za-z0-9]+|LTP2-Site6)')


class ScannedTag:
    '''Tag for a scanned DICOM file.'''
    def __init__(self, tag: Tag):
        self.tag = tag
        self.in_file = self.in_spreadsheet = False

    def __hash__(self):
        return hash(self.tag)
    
    def __eq__(self, other):
        return self.tag == other.tag

    def __lt__(self, other):
        return self.tag < other.tag

    def __str__(self):
        return f'{self.tag} in file: {self.in_file}, in spreadsheet: {self.in_spreadsheet}'

    def __repr__(self):
        return f'<{self.__class__.__name__}(tag={self.tag},in_file={self.in_file},in_spreadsheet={self.in_spreadsheet})>'


def _load_hk_spreadsheet(spreadsheet_id: str) -> Generator[list[str], None, None]:
    '''Load the HK spreadsheet with the given ID.'''
    fd, fn = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        gdown.download(id=spreadsheet_id, output=fn, format='csv')
        with open(fn, 'r') as io:
            reader = csv.reader(io)
            for row in reader: yield row
    finally:
        os.unlink(fn)


def _tag_from_string(tag_string: str) -> tuple[Tag, str]:
    '''Parse the tag string like "(0010,0020)" into a pydicom Tag; strip out HK's "clever" annotations.

    Returns the pydicom Tag and the cleaned tag string.
    
    >>> _tag_from_string('(0010,0020)')
    Tag(0x0010, 0x0020), '(0010,0020)'
    >>> _tag_from_string('(0010,0020) [private]')
    Tag(0x0010, 0x0020), '(0010,0020)'

    This may raise a ValueError if the tag string is invalid.
    '''
    tag_string = tag_string.replace('[private]', '').strip().strip('()')
    group, element = tag_string.split(',')
    return Tag(int(group, 16), int(element, 16)), tag_string


def _load_prescribed_tags(spreadsheet_id: str) -> dict:
    '''Load the prescribed tags from the Google Sheet with the given ID.'''
    tags, line_num = set(), 0
    for row in _load_hk_spreadsheet(spreadsheet_id):
        line_num += 1
        # Skip header row and annotation rows (i.e., rows with no tag) and HK's spreadsheet-wide grouping rows
        if row[0] == 'Set' or row[2] == '' or row[2] == '??': continue
        # Parse the tag string like "(0010,0020)" into a pydicom Tag; strip out HK's "clever" annotations
        try:
            dicom_tag, _ = _tag_from_string(row[2])
            tags.add(dicom_tag)
        except ValueError as e:
            _logger.error('❌ Ignoring invalid tag "%s" in row %d', row[2], line_num)
    return tags


def _top_level_data_elements(ds: pydicom.Dataset) -> Generator[pydicom.DataElement, None, None]:
    '''Yields only the top-level data elements in the given DICOM dataset wihtout recursing into subsequences.'''
    try:
        for elem in ds: yield elem
    except BytesLengthException:
        # There are bad tags in the good (and bad) DICOM files too, so skip 'em
        pass


def _record_value(tag: Tag, file_path: str, value: object, values: dict):
    '''Record the value in the values dictionary.'''

    # Transform it into something readable by HK
    if isinstance(value, bytes):
        value = '«binary data»'
    elif isinstance(value, Sequence):
        value = '«Sequence data»'
    else:  # It's a MultiValue, UID, PersonName, DSfloat, IS, list, float, int … or a str
        value = str(value)

    # Figure out which "site" it belongs to
    matches = _site_re.search(file_path)
    site = matches.group(1) if matches else '«unknown site»'

    # Record it
    sites = values.get(tag, dict())

    # HK thinks using the most prevalent value is "misleading" (🤔) so just gather sets of values
    # so we can pick one at random—no I don't get it either.
    # counter = sites.get(site, collections.Counter())
    # counter[value] += 1
    seen_values = sites.get(site, set())
    seen_values.add(value)
    sites[site] = seen_values
    values[tag] = sites


def _scan_file(file_path: str) -> tuple:
    '''Scan the DICOM header of the file at `file_path` and return results.'''
    # Remove excessive logging - only log errors
    try:
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
    except InvalidDicomError as e:
        # There are many non-DICOM files so just ignore these; no need to even log them
        return set(), {}

    tags, values = set(), {}
    
    for elem in _top_level_data_elements(ds):
        # Create a new object with updated state
        new_tag = ScannedTag(elem.tag)
        new_tag.in_file = True
        tags.add(elem.tag)
        _record_value(elem.tag, file_path, elem.value, values)
    
    return tags, values


def _find_all_files(folder: str):
    '''Find all the DICOM files in `folder`.'''
    for root, _, files in os.walk(folder):
        for fn in files:
            yield os.path.join(root, fn)


def _serial_scan(folder: str) -> tuple:
    '''Scan the DICOM headers of the files in `folder` serially.'''
    all_tags, all_values = set(), {}
    
    for file_path in _find_all_files(folder):
        tags, values = _scan_file(file_path)
        all_tags.update(tags)
        # Merge values dictionaries
        for tag, sites_dict in values.items():
            if tag not in all_values:
                all_values[tag] = {}
            for site, values in sites_dict.items():
                if site not in all_values[tag]:
                    all_values[tag][site] = set()
                all_values[tag][site].update(values)
    
    return all_tags, all_values


def _report_tag_appearance(tags: dict, values: dict):
    '''Report DICOM tag appearance in the files and spreadsheet to a CSV file.'''

    header = ['Tag', 'Name', 'In File', 'In Spreadsheet']

    with open('tag-appearance-report.csv', 'w') as io:
        writer = csv.writer(io)
        writer.writerow(header)
        for tag in sorted(tags.values(), key=lambda t: t.tag):
            row = [
                tag.tag, datadict.keyword_for_tag(tag.tag),
                '✓' if tag.in_file else '', '✓' if tag.in_spreadsheet else ''
            ]
            writer.writerow(row)


def _generate_hk_spreadsheet(tags: dict, values: dict, spreadsheet_id: str):
    '''Generate the HK spreadsheet with the given ID.'''

    sites = sorted(list(set([key for d in values.values() for key in d.keys()])))
    header = False
    with open('hk-spreadsheet-with-randomly-chosen-values.csv', 'w') as io:
        writer = csv.writer(io)
        for row in _load_hk_spreadsheet(spreadsheet_id):
            if not header and row[0] == 'Set':
                header = True
                header_row = row + [f'Randomly chosen value from DCM files in "{site}"' for site in sites]
                writer.writerow(header_row)
            elif row[2] == '':
                # This is one of HK's "clever" annotation rows, so just output it verbatim but add blanks for the
                # randonly chosen value columns for each site
                row_values = row + [''] * len(sites)
                writer.writerow(row_values)
            else:
                # This is a row with a tag, so we need to find the corresponding tag in the tags dictionary
                row_values = row
                try:
                    tag_obj, cleaned_tag_string = _tag_from_string(row[2])
                    possible_values_per_site = values.get(tag_obj, {})
                    for site in sites:
                        if site not in possible_values_per_site:
                            row_values += [f'🫙 No values found for tag "{cleaned_tag_string}" in DICOM file for site "{site}"']
                        else:
                            # Note that this could pick an empty string, but that's what HK wants I guess 🤪
                            row_values += [random.choice(list(possible_values_per_site[site]))]
                except ValueError as e:
                    row_values += [f'❌ Tag "{row[2]}" is an invalid DICOM tag ID'] * len(sites)
                writer.writerow(row_values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    add_logging_argparse_options(parser)
    parser.add_argument(
        '--spreadsheet', default=_default_spreadsheet_id,
        help='ID of the Google Sheet to use; default "%(default)s"'
    )
    parser.add_argument('folders', nargs='+', help='Folders containing DICOM files to scan')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')

    # Map from a pydicom.tag.Tag to a ScannedTag object; and set of prescribed tags from the Google sheet
    prescribed_tags = _load_prescribed_tags(args.spreadsheet)

    _logger.info('🏁 Scanning %d folders: %s', len(args.folders), ', '.join(args.folders))
    time0 = time.monotonic()
    
    # Just use serial processing - it's faster and more reliable for I/O-bound tasks
    _logger.info('🔧 Using serial processing (multiprocessing disabled due to Cursor stupidity issues)')
    
    # Process all folders and combine results
    all_tags_set = set()
    all_values = {}
    
    for folder in args.folders:
        _logger.info('📁 Processing folder: %s', folder)
        tags_set, values = _serial_scan(folder)
        all_tags_set.update(tags_set)
        
        # Merge values dictionaries
        for tag, sites_dict in values.items():
            if tag not in all_values:
                all_values[tag] = {}
            for site, possible_values in sites_dict.items():
                if site not in all_values[tag]:
                    all_values[tag][site] = set()
                all_values[tag][site].update(possible_values)

    # Convert tags_set to tags dict with ScannedTag objects
    tags = {}
    for tag in all_tags_set:
        scanned_tag = ScannedTag(tag)
        scanned_tag.in_file = True
        tags[tag] = scanned_tag

    # Finally, mark all the tags in the spreadsheet and add any missing found in the spreadsheet but not in files
    for tag in prescribed_tags:
        existing_tag = tags.get(tag)
        if existing_tag is None:
            # Create new tag with in_spreadsheet=True
            new_tag = ScannedTag(tag)
            new_tag.in_spreadsheet = True
            tags[tag] = new_tag
        else:
            # Update existing tag
            existing_tag.in_spreadsheet = True

    _logger.info('🏁 Scanning took %s', humanize.naturaldelta(time.monotonic() - time0))
    _generate_hk_spreadsheet(tags, all_values, args.spreadsheet)
    _report_tag_appearance(tags, all_values)

    sys.exit(0)


if __name__ == '__main__':
    main()
