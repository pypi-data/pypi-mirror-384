# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: date report.

To run this, first establish the `edrn-labcas-tunnels` on the JPL host,
since this'll make 8984 open to edrn-labcas on that host. Then run the
`jpl-tunnels` on the high speed development host, and that'll establish
the tunnels to the JPL host (MacBook Pro).

This script then assumes Solr is at https://localhost:8984/ (with a self-
signed certificate). You can override this, of course.

This will write a CSV file with each collection and the known dates.
'''

from .argparse import add_standard_argparse_options
from .const import PROTOCOL_RDF_SOURCE
from .rdf import read_rdf
from urllib.parse import urlparse
import argparse, sys, rdflib, pysolr, csv, logging

_logger = logging.getLogger(__name__)


# RDF type for protocol objects
_protocol_type = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')

# RDF predicate for the start date
_start_date = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#startDate')

# RDF predicate for the estimated finish date
_estimated_finish_date = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#estimatedFinishDate')

# RDF predicate for the finish date
_finish_date = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#finishDate')


def _dmcc_id(subject: rdflib.URIRef) -> str:
    '''Convert an RDF subject URI (specifically a URL in this case) into a DMCC protocol ID.
    I.E, convert `http://edrn.nci.nih.gov/data/protocols/237` → `237`
    '''
    return urlparse(subject).path.split('/')[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_argparse_options(parser)
    parser.add_argument(
        '-p', '--protocols', metavar='URL', default=PROTOCOL_RDF_SOURCE,
        help='Where to find RDF for protocols (default %(default)s)'
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format='%(levelname)s %(message)s')
    solr, statements, protocols = pysolr.Solr(args.solr + 'collections', verify=False), read_rdf(args.protocols), {}

    # First, gather up the title and the start, estimated finish, and finish dates of all protocols
    for subject_uri, predicates in statements.items():
        kind = predicates.get(rdflib.RDF.type, [None])[0]
        if kind != _protocol_type: continue
        start = predicates.get(_start_date, ['«unknown»'])[0]
        estimated_finish = predicates.get(_estimated_finish_date, ['«unknown»'])[0]
        finish = predicates.get(_finish_date, ['«unknown»'])[0]
        title = predicates.get(rdflib.DCTERMS.title, ['«unknown title»'])[0]
        protocols[_dmcc_id(subject_uri)] = (title, start, estimated_finish, finish)

    # Now gather up the EDRN collections
    results = solr.search(
        q='Consortium:EDRN', rows=999999,
        fl=['Date', 'ProtocolId', 'DateDatasetFrozen', 'DateProductFrozen', 'CollectionId']
    )

    # Go through the resuts and write each row
    writer = csv.writer(sys.stdout)
    writer.writerow([
        'Collection ID', 'LabCAS Date', 'LabCAS Date Dataset Frozen', 'LabCAS Date Product Frozen',
        'Protocol ID', 'Protocol Title', 'Protocol Start', 'Estimated Protocol Finish', 'Protocol Finish'
    ])
    for result in results:
        collection_id = result['CollectionId'][0]
        protocol_id = result.get('ProtocolId')
        if protocol_id is None:
            _logger.warning('Collection %s does not have a protocol ID; skipping', collection_id)
            continue
        protocol_id = protocol_id[0]
        pdetails = protocols.get(protocol_id)
        if not pdetails:
            _logger.warning('Collection %s refers to unknown protocol ID %s; skipping', collection_id, protocol_id)
            continue

        row = [
            collection_id,
            result.get('Date', ['«unknown»'])[0],
            result.get('DateDatasetFrozen', ['«unknown»'])[0],
            result.get('DateProductFrozen', ['«unknown»'])[0],
            protocol_id,
            pdetails[0],
            pdetails[1],
            pdetails[2],
            pdetails[3]
        ]
        writer.writerow(row)

    sys.stdout.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
