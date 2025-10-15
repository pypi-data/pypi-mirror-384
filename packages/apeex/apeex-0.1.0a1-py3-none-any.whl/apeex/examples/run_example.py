# apeex/examples/run_example.py
from apeex.container import Container
from apeex.examples.sample_bundle import SampleBundle

# Create container
container = Container()

# Build bundle (registers services)
bundle = SampleBundle()
container.build_bundle(bundle)

# Retrieve services
logger = container.get("Logger")
logger.log("Hello from Logger!")

# Autowiring UserService (should use singleton or factory)
user_service = container.get("UserService")
user_service.create_user("alice")

# Autowiring directly via class (autowire resolves dependencies automatically)
from apeex.examples.services import UserService
user_service2 = container.autowire(UserService)
assert user_service2 is container.get("UserService")  # singleton
