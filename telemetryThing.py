#!/usr/bin/env python3
from collections.abc import Iterable
from datetime import datetime
from FileReader import FileReader
from GreengrassAwareConnection import *
import MessagePayload
from Observer import *
import TopicGenerator

import argparse
from datetime import datetime
import json
import logging
import time
import sys
import boto3
import hashlib
import ssl

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
parser.add_argument("-p", "--profile", action="store", dest="profile", default=None, help="AWS CLI profile")

args = parser.parse_args()
host = args.host
rootCA = args.rootCAPath
cert = args.certificatePath
key = args.privateKeyPath
thingName = args.thingName
profile = args.profile

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

tripSrc = FileReader(local_dir=state.get('local_dir', "."), record_separator=state.get('record_separator', ','), quote_records=state.get('quote_records', False))

def checkActiveCertificate(cert):
    try:
        #open the cert and read to a byte array
        f = open(cert, "r") 
        #covert PEM to DER to hash to SHA 256 string
        myder_cert = ssl.PEM_cert_to_DER_cert(f.read())
        #AWS IOT uses SHA-256 hash of the device certificate in binary DER to generate the certificateID, use the hashlib below to perform that operation
        certId = hashlib.sha256(myder_cert).hexdigest()     
        #pass in the profile name to use this from your own AWS CLI, rather than temp credentials through C9
        if profile is not None: boto3.setup_default_session(profile_name = profile)
        client = boto3.client('iot')
        #get certificate status from the account using the certId             
        certStatus = client.describe_certificate(certificateId=certId)["certificateDescription"]["status"]
        print("certstatus: %s" % certStatus)
        if certStatus == 'INACTIVE':return False 
        return True
    except Exception as e:
         logger.error(f'{str(type(e))} Error')

rootCA = args.rootCAPath
cert = args.certificatePath
key = args.privateKeyPath
thingName = args.thingName
profile = args.profile

class DeltaProcessor(Observer):
    def update(self, updateList):
        global state_dirty

        [ state.update(u) for u in updateList ]
        state_dirty = True

try:
    deltas = ObservableDeepArray()

    certValid = checkActiveCertificate(cert)
    print("certValid: %s" % certValid)
    if not certValid:
        print("Invalid discovery request detected!")
        print("The certificate needs to be activated before attempting to connect")
        print("Stopping...")
        exit()

    iotConnection = GreengrassAwareConnection(host, rootCA, cert, key, thingName, deltas)
    
    time.sleep(10)

    deltaProcessor = DeltaProcessor()
    deltas.addObserver(deltaProcessor)
except Exception as e:
    logger.error(f'{str(type(e))} Error')

def getTopicGenerator():
    topic_strategy = getattr(TopicGenerator, state.get('topic_strategy', 'SimpleFormattedTopic'))
    return topic_strategy(state.get('topic_name', 'dt/cvra/{deviceid}/cardata'))

def makePayload(telemetry):
    payload_strategy = getattr(MessagePayload, state.get('payload_strategy', 'SimpleLabelledPayload'))
    return payload_strategy(telemetry, {
        'preDropKeys':state.get('ignore_columns'),
        'metricKey': state.get('measure_column'),
        'readingKey': state.get('value_column'),
        'time_col_name': state.get('time_col_name')
    }).message(json.dumps)

def getTimestampMS(telemetry):
    time_col_name = state.get('time_col_name', 'Timestamp(ms)')
    time_scale = float(state.get('time_scale', 1000.0))
    timestamp = telemetry.get(time_col_name, DEFAULT_SAMPLE_DURATION_MS)
    time_format = state.get('timestamp_format')
    timestamp_offset = state.get('timestamp_offset', 0.0)
    # convert to milliseconds
    if time_format == None:
        timestamp_ms = (float(timestamp) + timestamp_offset)/time_scale*1000
    else:
        timestamp_ms = datetime.strptime(timestamp, time_format).timestamp()*1000
    
    return int(timestamp_ms)



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
            time.sleep(600) # wait 10 min for queued messages to clear
            sys.exit()
        return 30       # wait 30 seconds between runs

    deviceid = state.get('deviceid', thingName)
    timestamp_ms = getTimestampMS(telemetry)

    payload = makePayload(telemetry)
    topic = getTopicGenerator().make_topicname(deviceid=deviceid, timestamp_ms=timestamp_ms)

    message_count += 1
    logger.info(f"{message_count} - {topic}:{payload}")

    sleep = [0, 1]
    while not iotConnection.publishMessageOnTopic(payload, topic, qos=1):
        logger.info("waiting to clear block")
        # fibonacci backoff on wait
        sleep.append(sum(sleep))
        timeout = sleep.pop(0)
        if timeout > 300:
            logger.warn("timeout escalated to 30 sec -- re-connecting")

            iotConnection.disconnect()
            time.sleep(10)
            iotConnection.connect()

            sleep = [0, 1]
        time.sleep(timeout/10.0)

    # return the timestamp of the leg
    return timestamp_ms/1000.0

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
