# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: fix the misspelled "mass spectrometry" in the LabCAS cores.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging


_logger = logging.getLogger(__name__)

__doc__ = 'Fix the misspelled "mass spectrometry" in the LabCAS cores.'


def _replace_values(solr: pysolr.Solr, dryrun: bool):
    count, replaced = 0, 0
    for match in find_documents(solr, 'DataCategory:Mass Spectometry', None):
        current = set(match.get('DataCategory'))
        if 'Mass Spectometry' in current:
            current.remove('Mass Spectometry')
            current.add('Mass Spectrometry')
            match['DataCategory'] = list(current)

            if dryrun:
                _logger.info('Dry run: would be replacing document %s with new %s', match['id'], 'DataCategory')
            else:
                _logger.debug('Replacing document %s', match['id'])
                if '_version_' in match:
                    del match['_version_']
                solr.add([match])
            replaced += 1

        count += 1
        if count % 100 == 0:
            _logger.info('Processed %d documents', count)

    _logger.info('Done! After %d documents I replaced the Data Category in %d of them', count, replaced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make any changes but show them instead"
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'
    for core_name in ['collections', 'datasets', 'files']:
        _logger.info('Processing %s', core_name)
        solr = pysolr.Solr(solr_url + core_name, always_commit=True, verify=False)
        _replace_values(solr, args.dryrun)
    sys.exit(0)


if __name__ == '__main__':
    main()
