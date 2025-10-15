from apeex.bundles.demo_bundle.services.hello_services import HelloService
from apeex.http.route import Route

class HelloController:
    """Example controller using HelloService."""

    def __init__(self, service: HelloService):
        self.service = service

    @Route(path="/hello/{name}", methods=["GET"])
    def greet(self, name: str) -> str:
        print(name)
        return "просто те"
