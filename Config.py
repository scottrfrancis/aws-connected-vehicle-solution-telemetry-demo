# Global configuration dict object for the app
#
#   can be used as state as well
#
import datetime

# these are the defaults, they can be overwritten
state = {
    # file to read -- 'file://', 's3://' also supported
    'file': 'file:///OBDII_Capture.csv',
    'record_separator': ';',
    'quote_records': True,

    #
    # Timestamp handling
    #
    'time_col_name': 'SECONDS',                     # column name to use for time        
    #'timestamp_format': '%Y-%m-%d %H:%M:%S.%f',    # set to parse the time, otherwise, numeric is assumed
    'timestamp_offset': float((datetime.date.today() - datetime.timedelta(days=1)).strftime('%s')),                # if set, added to the timestamp values
    'time_scale': 1.0,                              # units/second -- e.g. 1000.0 means stamps in milliseconds

    # Select a Strategy from MessagePayload.py to define how to format a payload from the record
    'payload_strategy': 'UntimedDynamicLabelledPayload',
    # Different stragegies may need different configs,
    # these two define the column of the metric and the value
    'measure_column':  'PID',
    'value_column': 'VALUE',
    'ignore_columns': ['UNITS'],

    # Topic to publish messages, different payload_strategies may need different templates using local vars
    'topic_name': "vt/cvra/{deviceid}/cardata/{timestamp_ms}",

    # throttle of messages per second
    'message_publish_rate': 10.0,

    # what to do at the end of the file... 'stop' or 'repeat'
    'at_end': 'stop',
}
