import logging

from .. import entities, miscellaneous, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Organizations:
    """
    Organizations Repository

    Read our `documentation <https://dataloop.ai/docs/org-setup>`_ to learn more about Organizations in the Dataloop platform.
    """

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api

    def create(self, organization_json: dict) -> entities.Organization:
        """
        Create a new organization.

        **Prerequisites**: This method can only be used by a **superuser**.

        :param dict organization_json: json contain the Organization fields
        :return: Organization object
        :rtype: dtlpy.entities.organization.Organization
        """

        raise exceptions.PlatformException(error='2001', message='Method organizations.create() was removed')

    def list_groups(self, organization: entities.Organization = None,
                    organization_id: str = None,
                    organization_name: str = None):
        """
        List all organization groups (groups that were created within the organization).

        **Prerequisites**: You must be an organization *owner* to use this method.

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param entities.Organization organization: Organization object
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :return: groups list
        :rtype: list

        **Example**:

        .. code-block:: python

            groups_list = dl.organizations.list_groups(organization_id='organization_id')
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/groups'.format(organization.id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        groups = miscellaneous.List(response.json())
        return groups

    def list_integrations(self, organization: entities.Organization = None,
                          organization_id: str = None,
                          organization_name: str = None,
                          only_available=False):
        """
        List all organization integrations with external cloud storage.

        **Prerequisites**: You must be an organization *owner* to use this method.

        You must provide at least ONE of the following params: organization_id, organization_name, or organization.

        :param entities.Organization organization: Organization object
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param bool only_available: if True list only the available integrations
        :return: integrations list
        :rtype: list

        **Example**:

        .. code-block:: python

            list_integrations = dl.organizations.list_integrations(organization='organization-entity',
                                                only_available=True)
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if only_available:
            url_path = '/orgs/{}/availableIntegrations'.format(organization.id)
        else:
            url_path = '/orgs/{}/integrations'.format(organization.id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        available_integrations = miscellaneous.List(response.json())
        return available_integrations

    @_api_reference.add(path='/orgs/{orgId}/members', method='get')
    def list_members(self, organization: entities.Organization = None,
                     organization_id: str = None,
                     organization_name: str = None,
                     role: entities.MemberOrgRole = None):
        """
        List all organization members.

        **Prerequisites**: You must be an organization *owner* to use this method.

        You must provide at least ONE of the following params: organization_id, organization_name, or organization.

        :param entities.Organization organization: Organization object
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param entities.MemberOrgRole role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :return: projects list
        :rtype: list

        **Example**:

        .. code-block:: python

            list_members = dl.organizations.list_members(organization='organization-entity',
                                        role=dl.MemberOrgRole.MEMBER)
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/members'.format(organization.id)

        if role is not None and role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        members = miscellaneous.List(
            [entities.User.from_json(_json=user, client_api=self._client_api, project=None) for user in
             response.json()])

        if role is not None:
            members = [member for member in members if member.role == role]

        return members

    @_api_reference.add(path='/orgs', method='get')
    def list(self) -> miscellaneous.List[entities.Organization]:
        """
        Lists all the organizations in Dataloop.

        **Prerequisites**: You must be a **superuser** to use this method.

        :return: List of Organization objects
        :rtype: list

        **Example**:

        .. code-block:: python

            organizations = dl.organizations.list()
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/orgs')

        if success:
            pool = self._client_api.thread_pools(pool_name='entity.create')
            organization_json = response.json()
            jobs = [None for _ in range(len(organization_json))]
            # return triggers list
            for i_organization, organization in enumerate(organization_json):
                jobs[i_organization] = pool.submit(entities.Organization._protected_from_json,
                                                   **{'client_api': self._client_api,
                                                      '_json': organization})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            organization = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.error('Platform error getting organization')
            raise exceptions.PlatformException(response)
        return organization

    @_api_reference.add(path='/orgs/{orgId}', method='get')
    def get(self,
            organization_id: str = None,
            organization_name: str = None,
            fetch: bool = None) -> entities.Organization:
        """
        Get Organization object to be able to use it in your code.

        **Prerequisites**: You must be a **superuser** to use this method.

        You must provide at least ONE of the following params: organization_name or organization_id.

        :param str organization_id: optional - search by id
        :param str organization_name: optional - search by name
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Organization object
        :rtype: dtlpy.entities.organization.Organization

        **Example**:

        .. code-block:: python

            org = dl.organizations.get(organization_id='organization_id')
        """
        if organization_name is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if fetch is None:
            fetch = self._client_api.fetch_entities

        if fetch:
            if organization_id is not None:
                success, response = self._client_api.gen_request(req_type='get',
                                                                 path='/orgs/{}'.format(organization_id))
                if not success:
                    raise exceptions.PlatformException(response)
                organization = entities.Organization.from_json(
                    client_api=self._client_api,
                    _json=response.json()
                )
            else:
                organizations = self.list()
                organization = [organization for organization in organizations if
                                organization.name == organization_name]
                if not organization:
                    # list is empty
                    raise exceptions.PlatformException(error='404',
                                                       message='organization not found. Name: {}'.format(
                                                           organization_name))
                    # project = None
                elif len(organization) > 1:
                    # more than one matching project
                    raise exceptions.PlatformException(
                        error='404',
                        message='More than one project with same name. Please "get" by id')
                else:
                    organization = organization[0]
        else:
            organization = entities.Organization.from_json(
                _json={'id': organization_id,
                       'name': organization_name},
                client_api=self._client_api)

        return organization

    def update(self, plan: str,
               organization: entities.Organization = None,
               organization_id: str = None,
               organization_name: str = None) -> entities.Organization:
        """
        Update an organization.

        **Prerequisites**: You must be a **superuser** to update an organization.

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param str plan: OrganizationsPlans.FREEMIUM, OrganizationsPlans.PREMIUM
        :param entities.Organization organization: Organization object
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :return: organization object
        :rtype: dtlpy.entities.organization.Organization

        **Example**:

        .. code-block:: python

            org = dl.organizations.update(organization='organization-entity',
                                    plan=dl.OrganizationsPlans.FREEMIUM)
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if plan not in list(entities.OrganizationsPlans):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(plan,
                                                                                 ', '.join(list(
                                                                                     entities.OrganizationsPlans))))
        payload = {'plan': plan}
        url_path = '/orgs/{}/plan'.format(organization.id)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if success:
            return organization
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/orgs/{orgId}/members', method='post')
    def add_member(self, email: str,
                   role: entities.MemberOrgRole = entities.MemberOrgRole.MEMBER,
                   organization_id: str = None,
                   organization_name: str = None,
                   organization: entities.Organization = None):
        """
        Add members to your organization. Read about members and groups `here <https://dataloop.ai/docs/org-members-groups>`_.

        **Prerequisities**: To add members to an organization, you must be an *owner* in that organization.

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param str email: the member's email
        :param str role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param entities.Organization organization: Organization object
        :return: True if successful or error if unsuccessful
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dl.organizations.add_member(email='user@domain.com',
                                        organization_id='organization_id',
                                        role=dl.MemberOrgRole.MEMBER)
        """

        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if not isinstance(email, list):
            email = [email]

        if role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        url_path = '/orgs/{}/members'.format(organization.id)
        payload = {"emails": email, 'role': role}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return True

    @_api_reference.add(path='/orgs/{orgId}/members/{memberId}', method='delete')
    def delete_member(self, user_id: str,
                      organization_id: str = None,
                      organization_name: str = None,
                      organization: entities.Organization = None,
                      sure: bool = False,
                      really: bool = False) -> bool:
        """
        Delete member from the Organization.

        **Prerequisites**: Must be an organization *owner* to delete members.

        You must provide at least ONE of the following params: organization_id, organization_name, organization.

        :param str user_id: user id
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param entities.Organization organization: Organization object
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: True if success and error if not
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dl.organizations.delete_member(user_id='user_id',
                                            organization_id='organization_id',
                                            sure=True,
                                            really=True)
        """
        if sure and really:
            if organization is None and organization_id is None and organization_name is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Must provide an identifier in inputs')

            if organization is None:
                organization = self.get(organization_id=organization_id, organization_name=organization_name)

            url_path = '/orgs/{}/members/{}'.format(organization.id, user_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path=url_path)
            if not success:
                raise exceptions.PlatformException(response)
            else:
                return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete member from SDK. Please login to platform to delete')

    @_api_reference.add(path='/orgs/{orgId}/members', method='patch')
    def update_member(self, email: str,
                      role: entities.MemberOrgRole = entities.MemberOrgRole.MEMBER,
                      organization_id: str = None,
                      organization_name: str = None,
                      organization: entities.Organization = None):
        """
        Update member role.

        **Prerequisites**: You must be an organization *owner* to update a member's role.

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param str email: the member's email
        :param str role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param entities.Organization organization: Organization object
        :return: json of the member fields
        :rtype: dict

        **Example**:

        .. code-block:: python

            member_json = dl.organizations.update_member(email='user@domain.com',
                                            organization_id='organization_id',
                                             role=dl.MemberOrgRole.MEMBER)
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/members'.format(organization.id)
        payload = dict(role=role, email=email)

        if role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def cache_action(self,
                     organization_id: str = None,
                     organization_name: str = None,
                     organization: entities.Organization = None,
                     mode=entities.CacheAction.APPLY,
                     pod_type=entities.PodType.SMALL):
        """
        Add or remove Cache for the org

        **Prerequisites**: You must be an organization *owner*

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param str organization_id: Organization id
        :param str organization_name: Organization name
        :param entities.Organization organization: Organization object
        :param str mode: dl.CacheAction.APPLY or dl.CacheAction.DESTROY
        :param entities.PodType pod_type:  dl.PodType.SMALL, dl.PodType.MEDIUM, dl.PodType.HIGH
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dl.organizations.enable_cache(organization_id='organization_id',
                                          mode=dl.CacheAction.APPLY)
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        return organization.cache_action(mode=mode, pod_type=pod_type)
