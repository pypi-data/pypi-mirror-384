from agilix_api_fr8train.models.generics import ListDefinition
from pendulum import DateTime


class ListUserDefinition(ListDefinition):
    pass


class GetUserActivityDefinition:
    user_id: int
    start_date: DateTime
    end_date: DateTime

    def __init__(
        self,
        user_id: int,
        start_date: DateTime = None,
        end_date: DateTime = None,
    ):
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date

    def __iter__(self):
        yield "userid", self.user_id
        if self.start_date:
            yield "startdate", self.start_date.to_iso8601_string()
        if self.end_date:
            yield "enddate", self.end_date.to_iso8601_string()


class GetDomainActivityDefinition:
    domain_id: int
    start_date: DateTime
    end_date: DateTime
    max_users: int
    select: list[str]

    def __init__(
        self,
        domain_id: int,
        start_date: DateTime = None,
        end_date: DateTime = None,
        max_users: int = 1000,
        select: list[str] = [],
    ):
        self.domain_id = domain_id
        self.start_date = start_date
        self.end_date = end_date
        self.max_users = max_users
        self.select = select

    def __iter__(self):
        yield "domainid", self.domain_id
        if self.start_date:
            yield "startdate", self.start_date.to_iso8601_string()
        if self.end_date:
            yield "enddate", self.end_date.to_iso8601_string()
        yield "maxusers", self.max_users
        if self.select:
            yield "select", ",".join(self.select)


class CreateUserDefinition:
    username: str
    password: str
    firstname: str
    lastname: str
    email: str
    domain_id: int
    reference: str
    role_id: int

    def __init__(
        self,
        username: str,
        password: str,
        firstname: str,
        lastname: str,
        email: str,
        domain_id: int,
        role_id: int,
        reference: str = "",
    ):
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.domain_id = domain_id
        self.reference = reference
        self.role_id = role_id

    def __iter__(self):
        yield "username", self.username
        yield "password", self.password
        yield "firstname", self.firstname
        yield "lastname", self.lastname
        yield "email", self.email
        yield "domainid", self.domain_id
        yield "reference", self.reference
        yield "roleid", self.role_id


class UpdateUserDefinition:
    user_id: int
    domain_id: int
    username: str
    firstname: str
    lastname: str
    email: str
    reference: str

    def __init__(
        self,
        user_id: int,
        domain_id: int,
        username: str,
        firstname: str,
        lastname: str,
        email: str,
        reference: str = "",
    ):
        self.user_id = user_id
        self.domain_id = domain_id
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.reference = reference

    def __iter__(self):
        yield "userid", self.user_id
        yield "domainid", self.domain_id
        yield "username", self.username
        yield "firstname", self.firstname
        yield "lastname", self.lastname
        yield "email", self.email
        yield "reference", self.reference
