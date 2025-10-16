from cheshirecat_python_sdk.endpoints.base import AbstractEndpoint

class HealthCheckEndpoint(AbstractEndpoint):
    def home(self):
        """
        This endpoint is used to check if the server is running.
        :return: dict, the status of the server.
        """
        response = self.get_http_session().get("/")
        response.raise_for_status()

        return response.json()
