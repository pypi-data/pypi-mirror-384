# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: S3 report.

This produces a CSV as outlined in `jpl-labcas/jpl.labcas.utils#1`.
'''

from . import VERSION
from .argparse import add_logging_argparse_options
from enum import Enum
from urllib.parse import urlparse
import argparse, logging, boto3, os, os.path, csv, sys

_logger = logging.getLogger(__name__)


class _ObjectType(Enum):
    FILE = 0
    FOLDER = 1


class _Folder:
    '''A "folder" in S3, tracking the number of files it contains and its child folders.'''

    def __init__(self, path):
        '''Initialize a "folder" giving its `path`.'''
        self.path = path
        self.files = 0
        self.children = []

    def average_num_child_files(self):
        '''Tell the average number of files in immediate children.

        This can return a number or None if the folder has no children folders.
        '''
        num_children = len(self.children)
        return None if num_children == 0 else sum([i.files for i in self.children]) / num_children

    def __repr__(self):
        return f'_Folder(path={self.path},files={self.files},children={self.children})'


def _extract_bucket_path(s3_url: str) -> tuple[str, str]:
    '''Given an S3 URL, return the name of the bucket and the path of the folder within
    the bucket.

    For example, `s3://blah/foo/bar` would give `('blah', 'foo/bar')`.
    '''
    parsed = urlparse(s3_url)
    return parsed.netloc, parsed.path.lstrip('/')


def _generate_s3_contents(s3, bucket, base_path):
    '''Generate the contents of everthing in `base_path` in the S3 `bucket`.

    This handles pagination.
    '''
    continuation_token = None
    while True:
        request_params = {'Bucket': bucket, 'Prefix': base_path}
        if continuation_token:
            request_params['ContinuationToken'] = continuation_token
        response = s3.list_objects_v2(**request_params)
        if 'Contents' in response:
            for obj in response['Contents']:
                path = obj['Key']
                if obj['Size'] == 0 and path.endswith('/'):
                    yield _ObjectType.FOLDER, path
                else:
                    yield _ObjectType.FILE, path
        if response.get('IsTruncated'):
            continuation_token = response['NextContinuationToken']
        else:
            break


def _parent(kind, path):
    '''For the `kind` of object at `path` give the path to its parent.

    The parent is always a folder so will always end with a `/`.
    '''
    if kind == _ObjectType.FOLDER:
        return os.path.dirname(path[0:-1]) + '/'
    else:
        return os.path.dirname(path) + '/'


def _generate_report(s3, s3_url):
    '''Using the given `s3` client, generate a report for the contents of `s3_url`.

    The report is written to the standard output as a CSV file with 4 columns
    as specified in EDRN/jpl.labcas.utils#1.
    '''
    bucket, root_path = _extract_bucket_path(s3_url)
    root, folders, count = None, {}, 0
    for kind, path in _generate_s3_contents(s3, bucket, root_path):
        _logger.debug('Kind = %s, path = %s', kind, path)
        parent_path = _parent(kind, path)
        if kind == _ObjectType.FOLDER:
            folder = _Folder(path)
            folders[path] = folder
            if path == root_path:
                assert root is None
                root = folder
            else:
                folders[parent_path].children.append(folder)
        else:  # must be FILE
            folders[parent_path].files += 1
        count += 1
        if count % 1000 == 0: _logger.info('Processed %d entries so far', count)

    writer = csv.writer(sys.stdout)
    writer.writerow(('folder path', '# files', '# sub-folders', 'avg # of files in sub-folders'))
    for folder in folders.values():
        avg = folder.average_num_child_files()
        avg = f'{avg:.2f}' if avg else ''
        writer.writerow((folder.path, folder.files, len(folder.children), avg))
    sys.stdout.flush()


def main():
    '''Entrypoint.'''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--profile', help='AWS profile to use, optional; set AWS_PROFILE environment variable if needed')
    parser.add_argument('s3url', help='URL to report on in the form s3://BUCKET/FOLDER/FOLDER/…')
    add_logging_argparse_options(parser)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    profile = args.profile if args.profile else os.getenv('AWS_PROFILE')
    session = boto3.Session(profile_name=profile)  # Assume AWS_PROFILE is set
    s3_client = session.client('s3')
    _generate_report(s3_client, args.s3url)


if __name__ == '__main__':
    main()
