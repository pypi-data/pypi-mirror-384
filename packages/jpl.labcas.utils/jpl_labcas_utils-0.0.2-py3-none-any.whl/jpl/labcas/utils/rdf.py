# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: RDF handling.'''


import rdflib, logging

_logger = logging.getLogger(__name__)


def read_rdf(source: str) -> dict:
    '''Read the RDF at the given URL `source` and return a dictionary.

    The dictionary keys are RDF subject URIs. The values are dictionaries. Those dictionary's keys
    are predicate URIs, and the values are lists of objects.
    '''
    _logger.debug('Parsing RDF from %s', source)
    graph, statements = rdflib.Graph(), {}
    graph.parse(source)
    for statement, predicate, obj in graph:
        predicates = statements.get(statement, {})
        objs = predicates.get(predicate, [])
        objs.append(obj)
        predicates[predicate] = objs
        statements[statement] = predicates
    _logger.debug('Parsed %d statements', len(statements))
    return statements
