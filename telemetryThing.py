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

FileURI = 's3://connected-vehicle-datasource/100.csv'
tripSrc = FileReader(FileURI)
def updateFileSource(fileURI):
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
    # if FileURI != tripSrc.getFileURI():
    #     del tripSrc
    #     tripSrc = FileReader(FileURI)

    # update state to shadow
    state['file'] = tripSrc.getFileURI()
    iotConnection.updateShadow(state)

    # send telemetry
    telemetry = tripSrc.getSample()
    print(json.dumps(telemetry))
    # iotConnection.publishTopic()

    # return the length of the leg
    return float(telemetry.get('Timestamp(ms)', DEFAULT_SAMPLE_DURATION_MS))/1000.0

timeout = 5
def run():
    while True:
        timeout = do_something()
        time.sleep(timeout)         
        
if __name__ == "__main__":
    run()
