#!/usr/bin/python3
from collections.abc import Iterable
from FileReader import FileReader
from GreengrassAwareConnection import *
from Observer import *

import argparse
from datetime import datetime
import json
import logging
import time




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
FileURI = 's3://connected-vehicle-datasource/100.csv'
TelemetryTopicBase = "vt"

tripSrc = FileReader(FileURI)
def updateFileSource(fileURI):
    global FileURI
    FileURI = fileURI

class DeltaProcessor(Observer):      
    def update(self, updateList):
        def do_update(d):
            updaters = { 'file': updateFileSource }
            for k in d:
                try:
                    updaters[k](d[k])
                except Exception as e:
                    pass

        [ do_update(u) for u in updateList ]


try:
    deltas = ObservableDeepArray()
    iotConnection = GreengrassAwareConnection(host, rootCA, cert, key, thingName, deltas)
    
    time.sleep(10)
    iotConnection.deleteShadow()
    time.sleep(10)
        
    deltaProcessor = DeltaProcessor()
    deltas.addObserver(deltaProcessor)   
except Exception as e:
    logger.error(f'{str(type(e))} Error')


state = {}
DEFAULT_SAMPLE_DURATION_MS = 1000
def do_something():
    global FileURI

    # apply updates
    currentURI = tripSrc.getFileURI()
    if FileURI != currentURI:
        tripSrc.useFileURI(FileURI)

    # send current state to shadow
    state['file'] = currentURI
    state['topic_base'] = TelemetryTopicBase
    iotConnection.updateShadow(state)

    # assemble telemetry
    telemetry = tripSrc.getSample()
    print(json.dumps(telemetry) + "\n")

    # extract 'process' properties
    timestamp = float(telemetry.get('Timestamp(ms)', DEFAULT_SAMPLE_DURATION_MS))/1000.0
    vehId = telemetry.get('VehId', 'None')

    # filter extraneous props
    try:
        for k in ['', 'DayNum', 'VehId', 'Trip', 'Timestamp(ms)']:
            telemetry.pop(k)
    except Exception as e:
        pass

    # publish it
    topic = "/".join([TelemetryTopicBase, vehId])
    iotConnection.publishMessageOnTopic(json.dumps(telemetry), topic)

    # return the timestamp of the leg
    return timestamp

timeout = 5
def run():
    last_time = 0
    while True:
        timeout = do_something()

        sleep_time = timeout - last_time if timeout >= last_time else 0
        last_time = timeout
        time.sleep(sleep_time)         
        
if __name__ == "__main__":
    run()
