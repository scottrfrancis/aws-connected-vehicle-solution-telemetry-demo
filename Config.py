# Global configuration dict object for the app
#
#   can be used as state as well
#

# these are the defaults, they can be overwritten
state = {
    'file': 's3://connected-vehicle-datasource/100.csv',
    'topic_base': "dt/cvra",
    'at_end': 'repeat',
    'local_dir': '/tmp'
}
