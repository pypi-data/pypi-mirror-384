from ._zermelo_collection import ZermeloCollection
from dataclasses import dataclass, InitVar
import logging

logger = logging.getLogger(__name__)


def getLeerjaarNaam(string):
    names = {"LG1": "klas 1", "LG2": "klas 2", "LG3": "klas 3"}
    for name, result in names.items():
        if name in string:
            return result
    else:
        return string


@dataclass
class Leerjaar:
    id: int
    code: str
    yearOfEducation: int
    branchOfSchool: int
    teacherTeams: list[int]
    mainGroupAuthority: str
    educationType: str
    weekTimeTable: int
    teachingLevel: str
    educations: list[int]
    schoolInSchoolYear: int
    branchOfSchoolCode: str
    schoolInSchoolYearName: str
    profiles: list[int]
    schoolInSchoolYearId: int
    name: str = ""

    def __post_init__(self):
        self.name = getLeerjaarNaam(self.code.upper())


class Leerjaren(ZermeloCollection[Leerjaar]):

    def __init__(self, schoolinschoolyear: int = 0):
        query = f"departmentsofbranches?schoolInSchoolYear={schoolinschoolyear}"
        super().__init__(Leerjaar, query)
