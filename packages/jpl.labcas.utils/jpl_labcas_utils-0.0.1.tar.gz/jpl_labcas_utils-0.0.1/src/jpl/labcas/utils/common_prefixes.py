# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: common prefixes.

Find common prefixes in FileLocation fields in Solr.
'''

from .argparse import add_standard_argparse_options
import requests, logging, argparse, os.path


_logger = logging.getLogger(__name__)

# Possible query?
# https://localhost:8984/solr/files/select?q=*:*&rows=0&facet=true&facet.field=FileLocation&facet.limit=-1&facet.sort=count

def _print_common_prefixes(url: str):
    url = url + 'files/select'
    _logger.info('Finding common prefixes in %s', url)
    params = {
        'q': '*:*', 'rows': 0, 'wt': 'json',
        'facet': 'true', 'facet.field': 'FileLocation', 'facet.limit': '-1', 'facet.sort': 'count'
    }
    response = requests.get(url, params=params, headers={'Accept': 'application/json'}, verify=False)
    response.raise_for_status()
    result = response.json()
    file_locations = result['facet_counts']['facet_fields']['FileLocation'][::2]
    for f in file_locations:
        print(f)


def main():
    parser = argparse.ArgumentParser(__doc__)
    add_standard_argparse_options(parser)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    url = args.solr if args.solr.endswith('/') else args.solr + '/'
    _print_common_prefixes(url)


if __name__ == '__main__':
    main()