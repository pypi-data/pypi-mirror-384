# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: report fields.

To run this, first establish the `edrn-labcas-tunnels` on the JPL host,
since this'll make 8984 open to edrn-labcas on that host. Then run the
`jpl-tunnels` on the high speed development host, and that'll establish
the tunnels to the JPL host (MacBook Pro).

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This reports all requested fields. Note that some fields are search-only
and cannot return values.
'''

from .argparse import add_standard_argparse_options
from .solr import find_documents
import argparse, sys, pysolr, logging, csv

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument('--query', default='*:*', help='Optional constrain query, default %(default)s')
    parser.add_argument('core', help='What Solr core to use (collections, datasets, files, etc.)')
    parser.add_argument('field', nargs='+', help='Fields to include')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr = pysolr.Solr(args.solr + args.core, always_commit=True, verify=False)

    writer = csv.writer(sys.stdout)
    writer.writerow(args.field)

    for match in find_documents(solr, args.query, args.field):
        row = []
        for field in args.field:
            value = match.get(field, None)
            if value is None:
                value = '«unknown»'
            if isinstance(value, list):
                value = ','.join(value)
            row.append(value)
        writer.writerow(row)

    sys.exit(0)


if __name__ == '__main__':
    main()
