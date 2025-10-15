from pendulum import DateTime


class ListUserEnrollmentsDefinition:
    user_id: int
    all_status: bool
    entity_id: int
    select: list

    def __init__(
        self,
        user_id: int,
        entity_id: int = None,
        all_status: bool = False,
        select: list = [],
    ):
        self.user_id = user_id
        self.all_status = all_status
        self.entity_id = entity_id
        self.select = select

    def __iter__(self):
        yield "userid", self.user_id
        if self.entity_id:
            yield "entityid", self.entity_id
        yield "allstatus", self.all_status
        if self.select:
            yield "select", ",".join(self.select)


class ListEntityEnrollmentsDefinition:
    entity_id: int
    all_status: bool
    select: list

    def __init__(
        self,
        entity_id: int,
        all_status: bool = False,
        select: list = [],
    ):
        self.entity_id = entity_id
        self.all_status = all_status
        self.select = select

    def __iter__(self):
        yield "entityid", self.entity_id
        yield "allstatus", self.all_status
        if self.select:
            yield "select", ",".join(self.select)


class UpdateEnrollmentsDefinition:
    enrollment_id: int
    status: int

    def __init__(
        self,
        enrollment_id: int,
        status: int = 1,
    ):
        self.enrollment_id = enrollment_id
        self.status = status

    def __iter__(self):
        yield "enrollmentid", self.enrollment_id
        yield "status", self.status


class GetEnrollmentDefinition:
    enrollment_id: int
    select: list[str]

    def __init__(
        self,
        enrollment_id: int,
        select: list[str] = [],
    ):
        self.enrollment_id = enrollment_id
        self.select = select

    def __iter__(self):
        yield "enrollmentid", self.enrollment_id
        if self.select:
            yield "select", ",".join(self.select)


class GetEnrollmentActivityDefinition:
    enrollment_id: int
    item_id: int
    start_date: DateTime
    end_date: DateTime
    limit: int
    last: bool
    merge_overlap: bool

    def __init__(
        self,
        enrollment_id: int,
        item_id: int = None,
        start_date: DateTime = None,
        end_date: DateTime = None,
        limit: int = None,
        last: bool = False,
        merge_overlap: bool = True,
    ):
        self.enrollment_id = enrollment_id
        self.item_id = item_id
        self.start_date = start_date
        self.end_date = end_date
        self.limit = limit
        self.last = last
        self.merge_overlap = merge_overlap

    def __iter__(self):
        yield "enrollmentid", self.enrollment_id
        if self.item_id:
            yield "itemid", self.item_id
        if self.start_date:
            yield "startdate", self.start_date.to_iso8601_string()
        if self.end_date:
            yield "enddate", self.end_date.to_iso8601_string()
        if self.limit:
            yield "limit", self.limit
        if self.last:
            yield "last", self.last
        yield "mergeoverlap", self.merge_overlap
