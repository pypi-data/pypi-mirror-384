from typing import List

from imerit_ango.models.enums import ProjectRoles, OrganizationRoles


class ProjectAssignment:
    def __init__(self, project_id: str, project_role: ProjectRoles):
        self.project_id = project_id
        self.project_role = project_role

    def toDict(self):
        return {
            'projectId': self.project_id,
            'projectRole': self.project_role.value
        }

class Invitation:
    def __init__(self, to: List[str], organization_role: OrganizationRoles, project_assignments: List[ProjectAssignment] = None ):
        self.to = to
        self.organization_role = organization_role
        self.project_assignments = project_assignments

    def toDict(self):
        resp = {
            'to': self.to,
            'organizationRole': self.organization_role.value,
        }
        if self.project_assignments:
            resp['projectAssignments'] = []
            for assignment in self.project_assignments:
                resp['projectAssignments'].append(assignment.toDict())
        return resp

class RoleUpdate:
    def __init__(self, email: str, organization_role: OrganizationRoles):
        self.email = email
        self.organization_role = organization_role

    def toDict(self):
        return {
            'email': self.email,
            'organizationRole': self.organization_role.value
        }

class ProjectMember:
    def __init__(self, email: str, project_role: ProjectRoles):
        self.email = email
        self.project_roles = project_role

    def toDict(self):
        return {
            'to': self.email,
            'projectRole': self.project_role.value
        }