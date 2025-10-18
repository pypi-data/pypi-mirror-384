###### Parsers, Formats, Utils
import logging
import json
import re
import copy

###### Communication
from websockets.sync.client import connect


###### Blue
from blue.agent import Agent
from blue.utils import string_utils, json_utils
from blue.utils.service_utils import ServiceClient


############################
### Agent.RequestorAgent
#
class RequestorAgent(Agent, ServiceClient):
    """An agent that sends requests to an external service via a WebSocket API.
    The agent collects input data from the input stream, sends it to the specified service URL,
    and writes the response to the output stream.
    """

    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = "REQUESTOR"
        super().__init__(**kwargs)

    def _initialize_properties(self):
        """Initialize default properties for the requestor agent, including service URL and input/output processing configurations."""
        super()._initialize_properties()

        self.properties['service_url'] = "ws://localhost:8001"

        # input / output processing properties
        self.properties['input_json'] = None
        self.properties['input_context'] = None
        self.properties['input_context_field'] = None
        self.properties['input_field'] = 'input'
        self.properties['output_path'] = 'output'

    def default_processor(self, message, input="DEFAULT", properties=None, worker=None):
        """Process messages for the requestor agent, sending input data to an external service via WebSocket and writing the response to the output stream.

        Parameters:
            message: The incoming message to process.
            input: The input stream name. Defaults to "DEFAULT".
            properties: Additional properties for processing.
            worker: The worker handling the processing.

        Returns:
            None or a response message.
        """
        if message.isEOS():
            # get all data received from stream
            stream_data = ""
            if worker:
                stream_data = worker.get_data('stream')

            #### call api to compute
            input_data = stream_data[0]
            self.logger.info(input_data)
            session_data = self.session.get_all_data()
            output = self.execute_api_call(input_data, properties=properties, additional_data=session_data)
            worker.write_data(output)
            worker.write_eos()

        elif message.isBOS():
            # init stream to empty array
            if worker:
                worker.set_data('stream', [])
            pass
        elif message.isData():
            # store data value
            data = message.getData()
            self.logger.info(data)

            if worker:
                worker.append_data('stream', str(data))

        return None
