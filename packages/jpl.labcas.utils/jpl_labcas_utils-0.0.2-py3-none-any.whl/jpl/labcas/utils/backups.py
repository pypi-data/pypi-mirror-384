# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: backup Solr metadata for LabCAS.

This just runs the backup endpoint on the three LabCAS cores, `collections`, `datasets`, and `files`.

By default it'll run on the default Solr (https://localhost:8984/solr/) but you can use `--solr` to
override that; for example, if you've tunneled `labcas-dev`'s Solr onto port 8987, you can specify
`--solr https://localhost:8987/solr/`.
'''

from .argparse import add_standard_argparse_options
import argparse, sys, logging, requests


_logger = logging.getLogger(__name__)


def _backup(url: str, core: str):
    _logger.info('Backing up core «%s» on %s', core, url)
    endpoint = f'{url}{core}/replication'
    _logger.debug('Replication endpoint is %s', endpoint)
    response = requests.get(
        endpoint, params={'command': 'backup', 'wt': 'json'}, headers={'Accept': 'application/json'}, verify=False
    )
    response.raise_for_status()
    result = response.json()
    _logger.info('Backup status: %s', result.get('status'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    url = args.solr if args.solr.endswith('/') else args.solr + '/'
    for core in ('collections', 'datasets', 'files'):
        _backup(url, core)
    sys.exit(0)


if __name__ == '__main__':
    main()
