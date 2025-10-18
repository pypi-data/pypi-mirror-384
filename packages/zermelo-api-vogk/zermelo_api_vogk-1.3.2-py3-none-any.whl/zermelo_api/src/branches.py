from ._zermelo_collection import ZermeloCollection
from ._time_utils import get_date, datetime
from .schoolyears import SchoolYears, SchoolInSchoolYear, load_schoolyears
from .users import Leerlingen, Personeel
from .leerjaren import Leerjaren
from .groepen import Groepen
from .lesgroepen import Lesgroepen
from .vakken import Vakken
from .lokalen import Lokalen
from .vakdoclok import get_vakloks, VakLoks
from dataclasses import dataclass, field, InitVar
import asyncio
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

@dataclass
class Branch:
    id: int
    schoolInSchoolYear: int
    branch: str
    name: str
    schoolYear: int
    date: datetime = datetime.now()
    leerlingen: Leerlingen = field(default_factory=Leerlingen)
    personeel: Personeel = field(default_factory=Personeel)
    leerjaren: Leerjaren = field(default_factory=Leerjaren)
    vakken: Vakken = field(default_factory=Vakken)
    groepen: Groepen = field(default_factory=Groepen)
    lokalen: Lokalen = field(default_factory=Lokalen)

    def __post_init__(self):
        logger.info(f"*** loading branch: {self.name} ***")
        self.leerlingen = Leerlingen(self.schoolInSchoolYear)
        self.personeel = Personeel(self.schoolInSchoolYear)
        self.leerjaren = Leerjaren(self.schoolInSchoolYear)
        self.groepen = Groepen(self.schoolInSchoolYear)
        self.vakken = Vakken(self.schoolInSchoolYear)
        self.lokalen = Lokalen(self.schoolInSchoolYear)

    async def _init(self):
        attrs = ["leerlingen", "personeel", "leerjaren", "groepen", "vakken", "lokalen"]
        await asyncio.gather(
            *[getattr(self, name)._init() for name in attrs], return_exceptions=False
        )

    async def find_lesgroepen(self) -> Lesgroepen | None:
        if self.leerlingen and self.personeel:
            return await Lesgroepen.create(
                self.leerjaren,
                self.vakken,
                self.groepen,
                self.leerlingen,
                self.personeel,
            )

    async def get_vak_doc_loks(self) -> VakLoks:
        start = int(self.date.timestamp())
        eind = start + 28 * 24 * 3600
        return await get_vakloks(self.id, start, eind)


class Branches(ZermeloCollection[Branch]):

    def __init__(self):
        super().__init__(Branch, "branchesofschools/")

    async def _init(self, schoolyears: SchoolYears, datestring: str = ""):
        logger.debug("init branches")
        date = get_date(datestring)
        logger.debug(f"date: {date}")
        await asyncio.gather(
            *[self.load_from_schoolyear(sy, date) for sy in schoolyears]
        )
        await asyncio.gather(*[branch._init() for branch in self])
        logger.info(self)

    async def load_from_schoolyear(self, sy: SchoolInSchoolYear, date: datetime):
        query = f"branchesofschools/?schoolInSchoolYear={sy.id}"
        await self.load_collection(query, date=date)

    def __str__(self):
        return "Branches(" + ", ".join([br.name for br in self]) + ")"

    def get(self, name: str) -> Branch | None:
        for branch in self:
            if (
                name.lower() in branch.branch.lower()
                or branch.branch.lower() in name.lower()
            ):
                return branch
        else:
            logger.error(f"NO Branch found for {name}")


async def load_branches(schoolname: str, date: str = "") -> Branches | None:
    try:
        data = await load_schools(schoolname, date)
        if not data:
            raise Exception("No branches found")
        _, branches = data
        return branches
    except Exception as e:
        logger.error(e)


async def load_schools(
    schoolname: str, date: str = ""
) -> tuple[SchoolYears, Branches] | None:
    try:
        logger.debug("loading schools:")
        schoolyears = await load_schoolyears(schoolname, date)
        logger.debug(schoolyears)
        branches = Branches()
        if not schoolyears:
            return None
        await branches._init(schoolyears, date)
        return (schoolyears, branches)
    except Exception as e:
        logger.error(e)
