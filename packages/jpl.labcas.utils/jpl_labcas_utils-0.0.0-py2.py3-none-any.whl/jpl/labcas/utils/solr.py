# encoding: utf-8

'''🛠️ JPL LabCAS Utilities: Solr.

Various conveniences to Apache Solr.
'''

import pysolr, logging
from typing import Generator

_logger = logging.getLogger(__name__)
_rows = 10000


def find_documents(solr: pysolr.Solr, query: str, fields: list[str]) -> Generator[dict, None, None]:
    start = 0
    while True:
        if fields:
            results = solr.search(q=query, start=start, rows=_rows, fl=','.join(fields))
        else:
            results = solr.search(q=query, start=start, rows=_rows)
        num_results = len(results)
        if num_results == 0:
            _logger.debug('At start %d with rows %d got zero results for %s', start, _rows, query)
            return
        start += num_results
        for result in results:
            yield result
