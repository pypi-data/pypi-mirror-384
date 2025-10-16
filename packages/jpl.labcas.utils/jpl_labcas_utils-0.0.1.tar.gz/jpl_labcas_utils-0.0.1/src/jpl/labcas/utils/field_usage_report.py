# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: field usage report.

Tells what fields are in use by collections, datasets, and files in
Solr and marks those that appear in collection and dataset `.cfg` files.
'''

from .argparse import add_standard_argparse_options
import argparse, logging, requests, csv, os, glob, configparser

_logger = logging.getLogger(__name__)


def _find_specified_keys(metadata_dir: str, level: str) -> set[str]:
    if level == 'files':
        _logger.info('🙅 The files level does not have any specified keys')
        return set()
    elif level == 'collections':
        pattern = f'{metadata_dir}/*/*.cfg'
    elif level == 'datasets':
        pattern = f'{metadata_dir}/*/*/*.cfg'

    keys = set()
    for cfg_file in glob.glob(pattern):
        try:
            cfg = configparser.ConfigParser()
            cfg.optionxform = str
            _logger.debug('📖 Reading %s at %s level', cfg_file, level)
            cfg.read(cfg_file)
            for section in cfg.sections():
                keys.update(cfg[section].keys())
        except configparser.Error as ex:
            _logger.error(f'🚨 Error reading {cfg_file}; skipping it ({ex})')
    _logger.info('🔑 Found %d specified keys in %s', len(keys), level)
    return keys


def _report_fields_for_core(solr_url: str, core: str, metadata_dir: str):
    specified_keys = _find_specified_keys(metadata_dir, core)
    luke_url = solr_url if solr_url.endswith('/') else solr_url + '/'
    luke_url += f'{core}/admin/luke'
    params = {'numTerms': 0, 'wt': 'json'}
    response = requests.get(luke_url, params=params, verify=False)
    fields = response.json().get('fields', {})
    _logger.info('🌞 Found %d fields in Solr in %s', len(fields), core)
    with open(f'{core}.csv', 'w', newline='') as io:
        writer = csv.writer(io)
        writer.writerow(['Field', 'Count', 'Specified'])
        for field_name, info in sorted(fields.items()):
            doc_count = info.get('docs', 0)
            specified = '✓' if field_name in specified_keys else ''
            writer.writerow([field_name, doc_count, specified])


def _report_fields(solr_url: str, metadata_dir: str):
    for core in ('collections', 'datasets', 'files'):
        _report_fields_for_core(solr_url, core, metadata_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('metadata', help='Location of the metadata directory')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    _report_fields(solr_url, args.metadata)


if __name__ == '__main__':
    main()