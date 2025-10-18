from ._zermelo_collection import ZermeloCollection
from dataclasses import dataclass, InitVar, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class Lokaal:
    id: int
    name: str
    parentteachernightCapacity: int
    courseCapacity: int
    supportsConcurrentAppointments: bool
    allowMeetings: bool
    branchOfSchool: int
    secondaryBranches: list[int]
    schoolInSchoolYear: int


class Lokalen(ZermeloCollection[Lokaal]):

    def __init__(self, schoolinschoolyear: int = 0):
        query = f"locationofbranches?schoolInSchoolYear={schoolinschoolyear}"
        super().__init__(Lokaal, query)

    def get(self, id: int) -> Lokaal | None:
        for lokaal in self:
            if lokaal.id == id:
                return lokaal
