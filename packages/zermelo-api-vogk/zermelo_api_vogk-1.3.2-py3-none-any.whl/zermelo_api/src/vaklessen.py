from ._zermelo_collection import ZermeloCollection
from .vakken import Vak
from .groepen import Groep
from ._time_utils import get_date, delta_week
from dataclasses import dataclass, InitVar, field
import asyncio
import logging

logger = logging.getLogger(__name__)

skip_docs: list[str] = ["stth", "lgverv", "lgst"]


def check_doc_skip(doc: str) -> bool:
    for skip_doc in skip_docs:
        if skip_doc.lower() in doc.lower():
            return True
    return False


def clean_checklist(checklist: list[str]):
    for doc in reversed(checklist):
        if check_doc_skip(doc):
            checklist.remove(doc)
    return checklist


@dataclass
class VakLes:
    id: int
    appointmentInstance: int
    teachers: list[str]
    students: list[str]
    subjects: list[str]
    groups: list[str]
    groupsInDepartments: list[int]
    choosableInDepartmentCodes: list[str]
    valid: bool
    cancelled: bool

    def filter(self, name: str) -> bool:
        logger.debug(f"filtering {self} ({name})")
        if self.cancelled:
            logger.debug("cancelled")
            return False
        if not self.valid:
            logger.debug("invalid")
            return False
        if not len(self.students):
            logger.debug("no students")
            return False
        if not len(self.teachers):
            logger.debug("no teachers")
            return False
        if len(self.students) > 40:
            logger.debug("groep te groot")
            return False
        if not any([name.split(".")[-1] in group for group in self.groups]):
            logger.debug(f"{name} not in {self}")
            return False
        logger.debug("True")
        return True


def clean_docs(docs: list[str]) -> list[str]:
    checklist = list(set(docs))
    clean_checklist(checklist)
    max = 0
    if len(checklist) > 1:
        logger.debug(f"multiple docs: {checklist}")
        for doc in checklist:
            doc_count = docs.count(doc)
            if doc_count > max:
                result = doc
                max = doc_count
        logger.debug(f"result: {result} ({max})")
        return [result]
    return checklist


class LesData(tuple[list[int], list[str], list[str]]):
    def __new__(cls, *U):
        return super(LesData, cls).__new__(cls, tuple(U))


class VakLessen(ZermeloCollection[VakLes]):
    id: InitVar[int] = 0
    code: InitVar[str] = ""
    groupName: str = ""
    start: InitVar[int] = 0
    eind: InitVar[int] = 0

    def __init__(
        self, id: int, code: str, groupName: str = "", start: int = 0, eind: int = 0
    ):
        query = f"appointments/?containsStudentsFromGroupInDepartment={id}&subjects={code}&type=lesson&start={start}&end={eind}&fields=appointmentInstance,id,teachers,students,subjects,groups,groupsInDepartments,choosableInDepartmentCodes,valid,cancelled"
        super().__init__(VakLes, query)
        self.groupName = groupName

    def filter(self) -> list[VakLes]:
        logger.debug(f"filtering {self}")
        return [les for les in self if les.filter(self.groupName)]

    def get_data(self) -> LesData:
        grp_bck = []
        ll_bck = []
        doc_bck = []
        leerlingen = []
        docenten = []
        grp_namen = []
        for les in self.filter():
            if len(les.students) > 40:
                if not grp_namen and (not grp_bck or len(les.groups) < len(grp_bck)):
                    logger.debug("meerdere groepen")
                    grp_bck = les.choosableInDepartmentCodes
                    ll_bck = list(set([llnr for llnr in les.students]))
                    doc_bck = list(set([doc for doc in les.teachers]))
                continue
            [leerlingen.append(llnr) for llnr in les.students if llnr not in leerlingen]
            [docenten.append(doc) for doc in les.teachers]
            [
                grp_namen.append(grp)
                for grp in les.choosableInDepartmentCodes
                if grp not in grp_namen
            ]
        logger.debug(
            f"filtering data for {self} \ngrp_namen: {grp_namen} \ndocenten: {docenten} \nleerlingen: {leerlingen}"
        )
        logger.debug(f"")
        logger.debug(
            f"backupdata: \n grp_bck: {grp_bck}\n doc_bck: {doc_bck} \nll_bck: {ll_bck}"
        )
        if not grp_namen and grp_bck:
            logger.debug(f"result groepen: {grp_bck}")
            grp_namen = grp_bck
        if not docenten and doc_bck:
            logger.debug(f"result docenten: {doc_bck}")
            docenten = doc_bck
        if not leerlingen and ll_bck:
            logger.debug(f"result leerlingen: {ll_bck}")
            leerlingen = ll_bck
        docenten = clean_docs(docenten)
        logger.debug(f"after cleaning docs: {docenten}")
        leerlingen = [int(llnr) for llnr in leerlingen]
        return LesData(leerlingen, docenten, grp_namen)


def create_new_vaklessen(vak: Vak, groep: Groep) -> list[VakLessen]:
    date = get_date()
    result: list[VakLessen] = []
    for x in [0, -1, 1, -2, 2, 3, -3]:
        dweek = x * 4
        starttijd = int(delta_week(date, dweek).timestamp())
        eindtijd = int(delta_week(date, dweek + 4).timestamp())
        result.append(
            VakLessen(
                groep.id,
                vak.subjectCode,
                groep.extendedName,
                starttijd,
                eindtijd,
            )
        )
    return result


async def get_vakgroep_lessen(vak: Vak, groep: Groep) -> VakLessen | None:
    logger.debug(f"getting vakgroep lessen for {vak} and {groep}")
    try:
        result = create_new_vaklessen(vak, groep)
        for vaklessen in result:
            logger.debug(f"init: {vaklessen}")
            await vaklessen._init()
            if not len(vaklessen):
                logger.debug("geen lessen gevonden")
                continue
            lessen = vaklessen.filter()
            logger.debug(f"lessen: {lessen}")
            if len(lessen):
                return vaklessen
        logger.debug("geen valid vaklessen gevonden.")
    except Exception as e:
        logger.error(e)


def check_data(data: LesData, vak: Vak) -> LesData | None:
    logger.debug(f"checking data for: \n  data: {data}\n  vak: {vak}")
    leerlingen, docenten, groep_namen = data
    if len(leerlingen) and len(docenten):
        namen = [
            groepnaam
            for groepnaam in groep_namen
            if vak.departmentOfBranchCode in groepnaam
        ]
        return LesData(leerlingen, docenten, namen)
    return None


async def get_vakgroep_data(vak, groep) -> LesData | None:
    logger.debug(f"getting vakgroep data for: \n  vak: {vak}\n  groep: {groep}")
    vaklessen = await get_vakgroep_lessen(vak, groep)
    if not vaklessen:
        logger.debug("geen lessen")
        return None
    logger.debug(f"vaklessen: {vaklessen}")
    lesdata = vaklessen.get_data()
    return check_data(lesdata, vak)


async def get_groep_data(vak: Vak, groep: Groep) -> tuple[Groep, LesData | None]:
    logger.debug(f"getting data for: \n  vak: {vak}\n  groep: {groep}")
    data = await get_vakgroep_data(vak, groep)
    return (groep, data)
