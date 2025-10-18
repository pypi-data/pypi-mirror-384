from ._zermelo_api import loadAPI
from ._zermelo_collection import ZermeloCollection
from ._time_utils import get_year
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchoolInSchoolYear:
    id: int
    name: str
    school: int = field(repr=False)
    year: int = field(repr=False)
    archived: bool = field(repr=False)
    projectName: str = field(repr=False)
    schoolName: str = field(repr=False)
    schoolHrmsCode: str = field(repr=False)


class SchoolYears(ZermeloCollection[SchoolInSchoolYear]):

    def __init__(self, datestring: str = ""):
        year = get_year(datestring)
        logger.debug(year)
        query = f"schoolsinschoolyears/?year={year}&archived=False"
        super().__init__(SchoolInSchoolYear, query)

    def __repr__(self):
        return f"SchoolYears([{super().__repr__()}])"


async def load_schoolyears(schoolname, date: str = "") -> SchoolYears | None:
    try:
        api = await loadAPI(schoolname)
        await api.checkCreds()
        schoolyears = SchoolYears(date)
        await schoolyears._init()
        return schoolyears
    except Exception as e:
        logger.exception(e)
