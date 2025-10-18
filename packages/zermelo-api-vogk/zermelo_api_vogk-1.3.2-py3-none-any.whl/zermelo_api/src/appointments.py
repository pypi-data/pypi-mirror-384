from ._zermelo_api import zermelo
from ._zermelo_collection import from_zermelo_dict
from dataclasses import dataclass, InitVar, field
import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

@dataclass
class Appointment:
    id: int
    appointmentInstance: int = 0
    start: int = 0
    end: int = 0
    startTimeSlot: int = 0
    endTimeSlot: int = 0
    branch: int = 0
    type: str = "unknown"
    groupsInDepartments: list[int] = field(default_factory=list)
    locationsOfBranch: list[int] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    optional: bool = False
    valid: bool = False
    cancelled: bool = False
    cancelledReason: str = ""
    modified: bool = False
    teacherChanged: bool = False
    groupChanged: bool = False
    locationChanged: bool = False
    timeChanged: bool = False
    moved: bool = False
    created: int = 0
    hidden: bool = False
    commonSchedule: bool = False
    ignoreSubstitutions: bool = False
    changeDescription: str = ""
    schedulerRemark: str = ""
    capacity: int = 0
    content: str = ""
    lastModified: int = 0
    new: bool = True
    choosableInDepartments: list[int] = field(default_factory=list)
    choosableInDepartmentCodes: list[str] = field(default_factory=list)
    courses: list[int] = field(default_factory=list)
    alternativeSubject: str = ""
    onlineStudents: list[str] = field(default_factory=list)
    extraStudentSource: str = ""
    appointmentLastModified: int = 0
    onlineLocationUrl: str = ""
    remark: str = ""
    capacityManually: bool = False
    teachingTimeManually: bool = False
    teachingTime: int = 0
    expectedStudentCount: int = 0
    expectedStudentCountOnline: int = 0
    availableSpace: int = 0
    udmUUID: str = ""
    creator: str = ""
    subjects: list[str] = field(default_factory=list)
    teachers: list[int] = field(default_factory=list)
    onlineTeachers: list[str] = field(default_factory=list)
    students: list[str] = field(default_factory=list)

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __hash__(self):
        return hash((self.id, self.lastModified))


async def get_appointments(query: str) -> list[Appointment]:
    try:
        status, data = await zermelo.getData(query)
        if isinstance(data, Exception):
            logger.error(f"status: {status}")
            raise Exception(data)
        if status != 200:
            logger.error(f"error: {status}")
            raise Exception(data)
        if not isinstance(data, list):
            raise Exception(f"{type(data)} is not a list")
        return [from_zermelo_dict(Appointment, row) for row in data]
    except Exception as e:
        logger.exception(e)
        logger.error(query)
        return []


async def get_location_appointments(
    lok: int, schoolyear: int, **kwargs
) -> list[Appointment]:
    query = f"appointments/?locationsOfBranch={lok}&schoolInSchoolYear={schoolyear}"
    for key, val in kwargs.items():
        query += f"&{key}={val}"
    logger.debug(query)
    return await get_appointments(query)


async def get_user_appointments(user: int | str, **kwargs) -> list[Appointment]:
    query = f"appointments/?user={user}"
    for key, val in kwargs.items():
        query += f"&{key}={val}"
    logger.debug(query)
    return await get_appointments(query)


async def get_department_updates(id: int, **kwargs) -> list[Appointment]:
    query = f"appointments/?containsStudentsFromGroupInDepartment={id}"
    for key, val in kwargs.items():
        query += f"&{key}={val}"
    return await get_appointments(query)
