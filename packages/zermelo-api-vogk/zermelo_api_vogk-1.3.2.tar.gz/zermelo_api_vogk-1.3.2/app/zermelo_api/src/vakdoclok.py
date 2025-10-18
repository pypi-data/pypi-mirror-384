from ._zermelo_collection import ZermeloCollection
from dataclasses import dataclass, InitVar, field


@dataclass
class VakLokData:
    locationsOfBranch: list[int]
    choosableInDepartments: list[str]


class DataVakLoks(ZermeloCollection[VakLokData]):
    def __init__(self, id_branch: int, start: int, eind: int):
        query = f"appointments?branchOfSchool={id_branch}&fields=locationsOfBranch,choosableInDepartments,&start={start}&end={eind}"
        super().__init__(VakLokData, query)


@dataclass
class VakLok:
    id: int
    lokalen: list[int] = field(default_factory=list)

    def add_loks(self, lokalen: list[int]):
        for lok in lokalen:
            if lok not in self.lokalen:
                self.lokalen.append(lok)


@dataclass
class VakLoks(list[VakLok]):
    def add(self, id) -> VakLok:
        vakdoclok = self.get(id)
        if not vakdoclok:
            vakdoclok = VakLok(id)
            self.append(vakdoclok)
        return vakdoclok

    def get(self, id: int) -> VakLok | None:
        for vakdoclok in self:
            if vakdoclok.id == id:
                return vakdoclok


async def get_vakloks(id_branch: int, start: int, eind: int):
    vakdata = DataVakLoks(id_branch, start, eind)
    await vakdata._init()
    vakdocloks = VakLoks()
    for data in vakdata:
        for id in data.choosableInDepartments:
            vakdoclok = vakdocloks.add(id)
            vakdoclok.add_loks(data.locationsOfBranch)
    return vakdocloks
