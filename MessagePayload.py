# MessagePayload
#
#   Takes dict of keys/vals and makes a formatted payload message.
# Implemented as factory pattern that allows for variations in message formatting.
#

from abc import ABC, abstractmethod

class MessagePayload(ABC):
    # pass array of keys to remove from message BEFORE or AFTER formatting
    # allows for subclasses to use data and then remove it
    #
    #   Typically, the caller will only supply preDropKeys if any and 
    # subclasses would set the postDropKeys as needed.
    #
    def __init__(self, d, preDropKeys = [], postDropKeys = []) -> None:
        self.payload = {}
        self.preDropKeys = preDropKeys
        self.preDropKeys.append('')
        self.postDropKeys = postDropKeys
        self._prepare_message(d)

    def _prepare_message(self, d):
        [ d.pop(k) for k in (set(self.preDropKeys) & set(d.keys())) ]
        self.make_message(d)
        [ self.payload.pop(k) for k in (set(self.postDropKeys) & set(self.payload.keys())) ]
    
    def message(self, formatter=None):
        return self.payload if formatter == None else formatter(self.payload)

    @abstractmethod
    def make_message(self, d):
        raise NotImplementedError("MessagePayload must be subclassed with an implementation of #prepare_message")

# SimpleLabelled Strategy just returns the dict
#   the dict is assumed to be structured with 'key': value
# so no changes.
class SimpleLabelledPayload(MessagePayload):
    def make_message(self, d):
        self.payload = d.copy()

# DynamicLabelledPayload takes apart the dict and builds the payload
#   the dict is of the format 'name': metric, 'value': reading
# and will be reformatted to 'metric': reading
#
class DynamicLabelledPayload(MessagePayload):
    # set keepKeys to any key-vals to preserve in message
    def __init__(self, metricKey='status', readingKey='value', keepKeys=['timestamp']) -> None:
        self.metricKey = metricKey
        self.readingKey = readingKey
        self.keepKeys = keepKeys

    def make_message(self, d):
        try:
            for k in self.keepKeys:
                self.payload[k] = d[k]
            self.payload[d[self.metricKey]] = d[self.readingKey]
        except Exception as e:
            print("key or value didn't exist")