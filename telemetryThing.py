#!/usr/bin/python3
from collections.abc import Iterable
from datetime import datetime
from FileReader import FileReader
from GreengrassAwareConnection import *
# from MessagePayload import *
import MessagePayload
from Observer import *

import argparse
from datetime import datetime
import json
import logging
import time
import sys

#  singleton config/state/globals
from Config import state

# Configure logging
logger = logging.getLogger("TelemetryThing.core")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Read in command-line parameters
parser = argparse.ArgumentParser()

parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")

args = parser.parse_args()
host = args.host
rootCA = args.rootCAPath
cert = args.certificatePath
key = args.privateKeyPath
thingName = args.thingName


# State variables
def_state = {
    'deviceid': thingName,
    'file': 's3://connected-vehicle-datasource/100.csv',
    'time_col_name': 'Timestamp(ms)',
    'time_scale':1000.0
}
for k in set(def_state.keys()) - set(state.keys()):
    state[k] = def_state[k]
state_dirty = True


tripSrc = FileReader()

class DeltaProcessor(Observer):
    def update(self, updateList):
        global state_dirty

        [ state.update(u) for u in updateList ]
        state_dirty = True

try:
    deltas = ObservableDeepArray()
    iotConnection = GreengrassAwareConnection(host, rootCA, cert, key, thingName, deltas)

    time.sleep(10)

    deltaProcessor = DeltaProcessor()
    deltas.addObserver(deltaProcessor)
except Exception as e:
    logger.error(f'{str(type(e))} Error')


DEFAULT_SAMPLE_DURATION_MS = 1000
message_count = 0
def do_something():
    # send current state to shadow
    global state_dirty, message_count
    if state_dirty:
        tripSrc.useFileURI(state['file'])

        iotConnection.updateShadow(state)
        state_dirty = False

    # assemble telemetry
    telemetry = tripSrc.getSample()
    # print(json.dumps(telemetry) + "\n")

    if len(telemetry) == 0:
        if state.get('at_end') == 'stop':
            logger.info("end of file reached")
            time.sleep(600)
            sys.exit()
        return 30       # wait 30 seconds between runs

    # extract 'process' properties
    deviceid = state.get('deviceid', thingName)
    time_col_name = state.get('time_col_name', 'Timestamp(ms)')
    time_scale = float(state.get('time_scale', 1000.0))
    timestamp = telemetry.get(time_col_name, DEFAULT_SAMPLE_DURATION_MS)
    format = state.get('timestamp_format')
    # convert to seconds
    if format == None:
        timestamp = float(timestamp)/time_scale
    else:
        t = datetime.strptime(timestamp, format)
        # telemetry.pop(time_col_name)
        # telemetry['the_time'] = timestamp #t.isoformat()

        timestamp = t.timestamp()

        # ${time_to_epoch(timestamp, "yyyy-MM-dd HH:mm:ss.SSS")}

    topic = state['topic_name'].format(deviceid=deviceid)

    # telemetry['time'] = telemetry.pop(time_col_name)

    payload_strategy = getattr(MessagePayload, state.get('file_strategy', 'SimpleLabelledPayload'))
    payload = payload_strategy(telemetry, {'preDropKeys':['DayNum', 'VehId', 'Trip']}).message()

    try:
        measure_column_name = state['measure_column']
        value_column_name = state['value_column']

        topic = state['topic_name'].format(deviceid=deviceid, status=payload[measure_column_name])
        payload.pop(measure_column_name)
    except exception as e:
        pass

    message_count += 1
    # if message_count > 1000:
    #     sys.exit()
    logger.info(f"{message_count} - {payload}")

    sleep0 = 0
    sleep1 = 1
    while not iotConnection.publishMessageOnTopic(payload, topic, qos=1):
        logger.info("waiting to clear block")
        # fibonacci backoff on wait
        sleep = sleep0 + sleep1
        sleep0 = sleep1
        sleep1 = sleep
        if sleep > 300:
            logger.warn("timeout escalated to 30 sec -- re-connecting")

            iotConnection.disconnect()
            time.sleep(10)
            iotConnection.connect()

            sleep0 = 0
            sleep1 = 1

        time.sleep(sleep/10.0)

    # return the timestamp of the leg
    return timestamp

timeout = 5
def run():
    rate = state.get('message_publish_rate')

    last_time = do_something()
    sleep_time = 0.05 if rate == None else 1.0/rate
    while True:
        time.sleep(sleep_time)

        cur_time = do_something()

        if rate == None:
            sleep_time = cur_time - last_time if timeout >= last_time else 0
            last_time = cur_time

if __name__ == "__main__":
    run()
