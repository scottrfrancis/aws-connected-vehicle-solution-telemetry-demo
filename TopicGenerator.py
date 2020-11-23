# TopicGenerator
#
#   Creates topic name for a message from configured template and message content
# Implemented as factory patter to allow to variable strategies 
#

from abc import ABC, abstractmethod

class TopicGenerator(ABC):
    def __init__(self, topic_template) -> None:
        self.template = topic_template

    @abstractmethod
    def make_topicname(self, **kwargs):
        raise NotImplementedError("MessagePayload must be subclassed with an implementation of #prepare_message")

class SimpleFormattedTopic(TopicGenerator):
    def make_topicname(self, **kwargs):
        # TODO: strip or encode args to be topic-safe
        topic_name = self.template.format(**kwargs)
        return topic_name
