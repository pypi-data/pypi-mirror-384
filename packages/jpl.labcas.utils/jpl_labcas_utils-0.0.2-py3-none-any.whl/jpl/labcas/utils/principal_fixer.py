'''🛠️ JPL LabCAS Utilities: fix OwnerPrincipal in a collection.

This will take an existing document and replace a list field with a new
items as given on the command line.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, os.path, configparser


_logger = logging.getLogger(__name__)
__doc__ = 'Fix the OwnerPrincipal field in a LabCAS collection and its datasets and files'
_max_updates = 100


def _read_owner_principals(cfgfile: str, section: str) -> list[str]:
    '''Read the `cfgfile` and look in the `section` for `OwnerPrincipal` and return
    a list of each one found.
    '''
    if not os.path.isfile(cfgfile):
        raise ValueError(f"Expected {cfgfile} to be a file that exists but it doesn't")
    cp = configparser.ConfigParser()
    cp.read(cfgfile)
    if not cp.has_section(section):
        raise ValueError(f'Expected {cfgfile} to have {section} but it only has {cp.sections()}')
    try:
        principals = cp.get(section, 'OwnerPrincipal')
        return principals.split('|')
    except configparser.NoOptionError:
        _logger.warning('⚠️ %s config file %s has no OwnerPrincipal, assuming none', section, cfgfile)
        return []


def _apply_updates(solr: pysolr.Solr, updates: list, dryrun: bool = True):
    if dryrun:
        _logger.info('🌵 DRY RUN: not calling update on %d updates', len(updates))
    else:
        _logger.debug('😎 HOT RUN: applying updates %r', updates)
        solr.add(updates)


def _set_owner_principals(solr_url: str, core: str, query: str, principals: list[str], dryrun: bool):
    solr_url = f'{solr_url}{core}'
    solr = pysolr.Solr(solr_url, always_commit=True, verify=False)
    updates = []
    for doc in find_documents(solr, query, ['id']):
        updates.append({'id': doc['id'], 'OwnerPrincipal': {'set': principals}})
        if len(updates) >= _max_updates:
            _apply_updates(solr, updates, dryrun)
            updates = []
    if len(updates) > 0:
        _apply_updates(solr, updates, dryrun)


def _fix_owner_principals_for_collection_dir(solr_url: str, collection_dir: str, dryrun: bool = True):
    collection_name = os.path.basename(collection_dir)
    _logger.info(
        '🧑‍🔧 Fixing OwnerPrincipal for collection %s in Solr at %s; dryrun=%d',
        collection_name, solr_url, dryrun
    )

    # First update the collection
    collection_cfg = os.path.abspath(os.path.join(collection_dir, f'{collection_name}.cfg'))
    collection_principals = _read_owner_principals(collection_cfg, 'Collection')
    if len(collection_principals) == 0:
        _logger.info('No OwnerPrincipals at Collection level, so not making any changes to collection')
    else:
        _logger.info(
            'At the Collection %s level, setting owners to %r', collection_name, collection_principals 
        )
        _set_owner_principals(
            solr_url, 'collections', f'id:{collection_name}', collection_principals, dryrun
        )

    # Now find each subdirectory and update the datasets and files. Note this assumes
    # there are no nested dataset directories, which is the case as of 2025-02-07 in
    # EDRN-metadata.
    for dirpath, dirnames, filenames in os.walk(collection_dir):
        for fn in filenames:
            if fn.endswith('.cfg'):
                cfg = os.path.abspath(os.path.join(dirpath, fn))
                if cfg == collection_cfg: continue
                dataset_name = os.path.basename(dirpath)
                dataset_principals = _read_owner_principals(cfg, 'Dataset')
                query = f'id:{collection_name}/{dataset_name}*'
                _logger.info(
                    'At the Dataset %s level, setting owners to %r', dataset_name, dataset_principals
                )
                _set_owner_principals(solr_url, 'datasets', query, dataset_principals, dryrun)
                _logger.info(
                    'For Files under %s, setting owners to %r', dataset_name, dataset_principals
                )
                _set_owner_principals(solr_url, 'files', query, dataset_principals, dryrun)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-r', '--dryrun', action='store_true', help="Dry run; don't make changes, show them instead"
    )
    parser.add_argument('dir', help='Path to directory with collection `.cfg` file and dataset subidrs')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    collection_dir = args.dir if not args.dir.endswith('/') else args.dir[:-1]
    solr_url = args.solr if args.solr.endswith('/') else args.solr + '/'

    if not os.path.isdir(collection_dir):
        raise ValueError(f'Expecting {collection_dir} to be a directory')
    _fix_owner_principals_for_collection_dir(solr_url, collection_dir, args.dryrun)

    sys.exit(0)


if __name__ == '__main__':
    main()
