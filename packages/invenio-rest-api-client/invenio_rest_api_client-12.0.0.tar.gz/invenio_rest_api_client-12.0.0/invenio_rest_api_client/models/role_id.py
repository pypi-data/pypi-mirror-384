from enum import Enum


class RoleId(str, Enum):
    CONTACTPERSON = "contactperson"
    DATACOLLECTOR = "datacollector"
    DATACURATOR = "datacurator"
    DATAMANAGER = "datamanager"
    DISTRIBUTOR = "distributor"
    EDITOR = "editor"
    HOSTINGINSTITUTION = "hostinginstitution"
    OTHER = "other"
    PRODUCER = "producer"
    PROJECTLEADER = "projectleader"
    PROJECTMANAGER = "projectmanager"
    PROJECTMEMBER = "projectmember"
    REGISTRATIONAGENCY = "registrationagency"
    REGISTRATIONAUTHORITY = "registrationauthority"
    RELATEDPERSON = "relatedperson"
    RESEARCHER = "researcher"
    RESEARCHGROUP = "researchgroup"
    RIGHTSHOLDER = "rightsholder"
    SPONSOR = "sponsor"
    SUPERVISOR = "supervisor"
    WORKPACKAGELEADER = "workpackageleader"

    def __str__(self) -> str:
        return str(self.value)
