# Global configuration dict object for the app
#
#   can be used as state as well
#

# these are the defaults, they can be overwritten
state = {
    'time_col_name': 'timestamp',
    'timestamp_format': '%Y-%m-%d %H:%M:%S.%f',
    'time_scale': 1.0,

    # 'file': 's3://amzl-data/1FTRS4XM0KKB08742-AMAZON_NA_EV_PILOT.bE-locations.csv',

    'topic_name': "vt/cvra/{deviceid}/cardata/{timestamp_ms}",

    'file': 's3://amzl-data/1FTRS4XM0KKB08742-AMAZON_NA_EV_PILOT.bE-statuses.csv',
    'payload_strategy': 'UntimedDynamicLabelledPayload',

    'message_publish_rate': 10.0,
    'measure_column':  'status',
    'value_column': 'value',
    'at_end': 'stop',
    'local_dir': '/tmp'
}
