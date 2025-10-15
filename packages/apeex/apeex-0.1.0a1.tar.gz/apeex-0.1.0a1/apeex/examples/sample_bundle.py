# apeex/examples/sample_bundle.py
from apeex.container.container import Container
from apeex.examples.services import Logger, UserService

class SampleBundle:
    """Example bundle demonstrating container integration."""
    def build(self, container: Container):
        # Direct service registration
        container.set("Logger", Logger())

        # Service registration via factory (lazy instantiation)
        container.set_factory("UserService", lambda c: UserService(c.get("Logger")))
