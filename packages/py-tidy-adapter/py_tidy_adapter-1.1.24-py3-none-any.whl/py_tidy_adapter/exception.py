class TidyException(Exception):
    def __init__(self, service_response):
        Exception.__init__(self)
        self.service_response = service_response

    def __str__(self):
        return self.service_response if isinstance(self.service_response, str) else self.service_response.message
