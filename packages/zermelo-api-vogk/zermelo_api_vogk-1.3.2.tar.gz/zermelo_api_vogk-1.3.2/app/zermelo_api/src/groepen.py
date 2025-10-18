from ._zermelo_collection import ZermeloCollection
from .vakken import Vak
from dataclasses import dataclass, InitVar
import logging

logger = logging.getLogger(__name__)


@dataclass
class Groep:
    id: int
    isMainGroup: bool
    isMentorGroup: bool
    departmentOfBranch: int
    name: str
    extendedName: str


class deelnemers(tuple[list[int], list[str], list[str]]): ...


class Groepen(ZermeloCollection[Groep]):

    def __init__(self, schoolinschoolyear: int = 0):
        query = f"groupindepartments?schoolInSchoolYear={schoolinschoolyear}"
        super().__init__(Groep, query)

    def get_department_groups(
        self, departmentOfBranch: int, maingroup: bool = False
    ) -> list[Groep]:
        # returns all groups (if it is/isnt stamklas (maingroup))
        return [
            groep
            for groep in self
            if groep.departmentOfBranch == departmentOfBranch
            and groep.isMainGroup == maingroup
        ]

    def get_vakgroepen(self, vak: Vak) -> list[Groep]:
        result = []
        logger.debug(f"finding groep for vak: {vak.subjectCode}")
        for groep in self.get_department_groups(vak.departmentOfBranch):
            if groep in result:
                continue
            if vak.qualifiedCode and vak.qualifiedCode in groep.extendedName:
                logger.debug(
                    f"found {groep.name} with {vak.qualifiedCode} in {groep.extendedName}"
                )
                result.append(groep)
        return result
