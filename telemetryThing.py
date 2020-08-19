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


class DeltaProcessor(Observer):
    def __init__(self, stateDict):
        super().__init__()
        self.state = stateDict
        
    def update(self, updateList):
        print("updating deltas with " + updateList)
        [ self.state.update(u) for u in updateList ]
        print("state now " + self.state)




try:
    deltas = ObservableDeepArray()
    iotConnection = GreengrassAwareConnection(host, rootCA, cert, key, thingName, deltas)
    
    time.sleep(10)
    iotConnection.deleteShadow()
        
    thingState = ObservableDict()
    deltaProcessor = DeltaProcessor(thingState)
    deltas.addObserver(deltaProcessor)   

    thingState.append({})

except Exception as e:
    logger.error(f'{str(type(e))} Error')


def do_something():
    iotConnection.updateShadow(thingState.getDict())
    

timeout = 20
def run():
    while True:
        time.sleep(timeout)         # crude approach to timing adjustment
        do_something()

if __name__ == "__main__":
    run()
