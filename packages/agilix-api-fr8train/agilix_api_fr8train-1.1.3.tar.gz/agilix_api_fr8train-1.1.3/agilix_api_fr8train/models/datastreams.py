class DataStreamConnectorDefinition:
    title: str
    enabled: bool

    def __init__(self, title: str, enabled: bool):
        self.title = title
        self.enabled = enabled


class HttpsStreamConnectorDefinition(DataStreamConnectorDefinition):
    stream_name: str
    timeout_seconds: int
    retries: int
    endpoints: str
    http_method: str

    def __init__(
        self,
        stream_name: str,
        endpoints: str,
        title: str = None,
        enabled: bool = True,
        timeout_seconds: int = 2,
        retries: int = 2,
        http_method: str = "POST",
    ):
        super().__init__(title, enabled)
        self.stream_name = stream_name
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.endpoints = endpoints
        self.http_method = http_method

    def __iter__(self):
        if self.title:
            yield "title", self.title
        else:
            yield "title", self.stream_name
        yield "enabled", self.enabled
        yield "streamName", self.stream_name
        yield "timeoutSeconds", self.timeout_seconds
        yield "retries", self.retries
        yield "endpoints", self.endpoints
        yield "httpMethod", self.http_method


class SetDataStreamConfigurationDefinition:
    domain_id: int
    https: list[HttpsStreamConnectorDefinition]

    def __init__(
        self, domain_id: int, https: list[HttpsStreamConnectorDefinition] = []
    ):
        self.domain_id = domain_id
        self.https = https

    def __iter__(self):
        yield "cmd", "setdatastreamconfiguration"
        yield "domainid", self.domain_id
        # IT'S FINE IF HTTPS IS EMPTY, THAT'S WHAT DELETES THE NODE
        yield "https", list(map(lambda x: dict(x), self.https))
