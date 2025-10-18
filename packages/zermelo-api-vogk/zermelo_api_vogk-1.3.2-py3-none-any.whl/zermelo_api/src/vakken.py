from ._zermelo_collection import ZermeloCollection
from dataclasses import dataclass, InitVar, field
import logging

logger = logging.getLogger(__name__)

talen = ["Engels", "Duits", "Frans", "Grieks", "Latijn", "Nederlands"]


def lowercase_first_char(string: str) -> str:
    if not string:
        return ""
    string = string.strip()
    for taal in talen:
        if taal in string:
            return string
    return string[:1].lower() + string[1:]


@dataclass
class Vak:
    id: int
    subject: int
    departmentOfBranch: int
    studentCanEdit: bool
    sectionOfBranch: int
    courseType: str
    lessonHoursInClassPeriods: list[dict]
    scroungeSegments: list[int]
    excludedSegments: list[int]
    referenceWeek: dict  # (year:int, weekNumber: int, schoolYear: int)
    isExam: bool
    scheduleCode: str
    subjectType: str
    subjectCode: str
    departmentOfBranchCode: str
    iltCode: int
    qualifiedCode: str
    subjectScheduleCode: str
    subjectName: str
    sectionOfBranchAbbreviation: str

    def getName(self) -> str:
        if "/" in self.subjectName:
            logger.debug(f"old name: {self.subjectName}")
            parts = self.subjectName.split("/")
            frontpart = parts[0]
            nameparts = frontpart.split(" ")
            nameparts.pop(-1)
            name = " ".join(nameparts)
            logger.debug(f"new name: {name}")
            return lowercase_first_char(name)
        return lowercase_first_char(self.subjectName)


class Vakken(ZermeloCollection[Vak]):

    def __init__(self, schoolinschoolyear: int = 0):
        query = f"choosableindepartments?schoolInSchoolYear={schoolinschoolyear}"
        super().__init__(Vak, query)

    def get(self, vaknaam: str) -> Vak | None:
        for vak in self:
            if vak.subjectCode == vaknaam:
                return vak

    def get_subject(self, subject: str) -> tuple[int, str]:
        """returns (code, naam)"""
        for vak in self:
            if vak.subjectCode == subject:
                return (vak.subject, vak.getName())
        return (0, "Onbekend")

    def get_leerjaar_vakken(self, leerjaar_id: int, skip: bool = False) -> list[Vak]:
        return [
            vak
            for vak in self
            if vak.departmentOfBranch == leerjaar_id
            and not (
                skip
                and (
                    vak.subjectType in ["education", "profile"]
                    or vak.scheduleCode
                    in [
                        "lo",
                        "sport",
                    ]
                )
            )
        ]
