from typing import TypeVar
from maleo.enums.organization import ListOfOrganizationRoles, SeqOfOrganizationRoles
from maleo.enums.system import ListOfSystemRoles, SeqOfSystemRoles


ListOfDomainRoles = ListOfOrganizationRoles | ListOfSystemRoles
ListOfDomainRolesT = TypeVar("ListOfDomainRolesT", bound=ListOfDomainRoles)

OptListOfDomainRoles = ListOfDomainRoles | None
OptListOfDomainRolesT = TypeVar("OptListOfDomainRolesT", bound=OptListOfDomainRoles)


SeqOfDomainRoles = SeqOfOrganizationRoles | SeqOfSystemRoles
SeqOfDomainRolesT = TypeVar("SeqOfDomainRolesT", bound=SeqOfDomainRoles)

OptSeqOfDomainRoles = SeqOfDomainRoles | None
OptSeqOfDomainRolesT = TypeVar("OptSeqOfDomainRolesT", bound=OptSeqOfDomainRoles)
