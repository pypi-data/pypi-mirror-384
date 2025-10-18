###### Parsers, Formats, Utils
import logging

###### Blue
from blue.agent import Agent


##########################
### Agent.UserAgent
#
class UserAgent(Agent):
    """A simple agent that represents a user in the system."""

    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = "USER"
        super().__init__(**kwargs)

    ####### inputs / outputs
    def _initialize_inputs(self):
        pass

    def _initialize_outputs(self):
        """Initialize outputs for the user agent."""
        self.add_output("DEFAULT", description="user output")

    def _initialize(self, properties=None):
        """ Initialize the UserAgent with default properties, setting it as non-instructable."""
        super()._initialize(properties=properties)

        # user is not instructable
        self.properties['instructable'] = False
