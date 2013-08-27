# work around modules with the same name
from __future__ import absolute_import

from cache_toolbar import panels
import logging
import datetime

DEBUG = False
logger = logging.getLogger(__name__)

CF_METHODS = (
    'get',
    'multi_get',
    'xget',
    'get_count',
    'multiget_count',
    'get_range',
    'get_indexed_slices',
    'insert',
    'batch_insert',
    'add',
    'remove',
    'remove_counter',
    'truncate'
)

def generate_method(cls, cls_name, method_name):
    def method(*args, **kwargs):
        stacktrace = panels.tidy_stacktrace(
            panels.traceback.extract_stack())

        call = {
            'function': '%s.%s()' % (cls_name, method_name),
            'args': "(%r) %r" % (panels.repr_value(args), panels.repr_value(kwargs)),
            'stacktrace': stacktrace,
        }

        ret = None
        try:
            # the clock starts now
            call['start'] = datetime.datetime.now()
            ret = getattr(cls, method_name)(*args, **kwargs)
        finally:
            # the clock stops now
            call['stop'] = datetime.datetime.now()
            d = call['stop'] - call['start']
            call['duration'] = d.seconds * 1e3 + d.microseconds * 1e-3

            call['hit'] = 1
            
        call['ret'] = panels.repr_value(ret)

        panels._get_calls().append(call)
        return ret    
    return method

try:
    import pycassa.columnfamily

    class TrackedColumnFamily(pycassa.columnfamily.ColumnFamily):
        def __init__(self, *args, **kwargs):
            # patch methods
            for method in CF_METHODS:
                setattr(self, method, generate_method(super(TrackedColumnFamily, self), 'ColumnFamily', method))

            return super(TrackedColumnFamily, self).__init__(*args, **kwargs)
    

    original_columnfamily = None
    # NOTE issubclass is true if both are the same class
    if not issubclass(pycassa.columnfamily.ColumnFamily, TrackedColumnFamily):
        logger.debug('installing pycassa.columnfamily.ColumnFamily with tracking')
        original_columnfamily = pycassa.columnfamily.ColumnFamily
        pycassa.columnfamily.ColumnFamily = TrackedColumnFamily

except:
    if DEBUG:
        logger.exception('unable to install pycassa.columnfamily.ColumnFamily with tracking')
    else:
        logger.debug('unable to install pycassa.columnfamily.ColumnFamily with tracking')


class CassandraPanel(panels.BasePanel):
    pass

