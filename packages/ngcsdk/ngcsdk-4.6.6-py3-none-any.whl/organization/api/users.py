#
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

import json
import logging
from typing import List, Optional
from urllib.parse import quote

import requests  # pylint: disable=requests-import
import shortuuid

from ngcbase.api.pagination import pagination_helper
from ngcbase.api.utils import NGC_CLI_USER_AGENT_TEXT, USER_AGENT
from ngcbase.command.args_validation import check_if_email_used, email_id_used
from ngcbase.constants import (
    API_VERSION,
    REQUEST_TIMEOUT_SECONDS,
    SCOPED_KEY_PREFIX,
    SF_DEVICE_ID,
)
from ngcbase.errors import (
    InvalidArgumentError,
    NgcAPIError,
    NgcException,
    ResourceNotFoundException,
)
from ngcbase.util.utils import extra_args
from organization.data.api.UserCreateRequest import UserCreateRequest
from organization.data.api.UserInvitationListResponse import UserInvitationListResponse
from organization.data.api.UserListResponse import UserListResponse
from organization.data.api.UserResponse import UserResponse
from organization.data.api.UserStorageQuotaListResponse import (
    UserStorageQuotaListResponse,
)
from organization.data.api.UserStorageQuotaResponse import UserStorageQuotaResponse
from organization.data.api.UserUpdateRequest import UserUpdateRequest

PAGE_SIZE = 100
logger = logging.getLogger(__name__)

# Error message constants
STARFLEET_ID_NOT_FOUND_ERROR = "Current user's Starfleet ID not found. Please ensure you're logged in properly."


class UsersAPI:  # noqa: D101
    def __init__(self, api_client):
        self.connection = api_client.connection
        self.client = api_client

    @staticmethod
    def _construct_url(org_name, team_name=None, user_id=None):
        """Constructs users url depending on given parameters."""  # noqa: D401
        base_method = f"{API_VERSION}/org/{org_name}"
        if team_name:
            base_method = f"{base_method}/team/{team_name}"
        if user_id:
            # GET: gets information of User
            # POST: adds user, but only succeeds if they already exist in the current org
            base_method = f"{base_method}/users/{user_id}"
        else:
            # GET: lists users
            # POST: creates user
            base_method = f"{base_method}/users"
        return base_method

    def _construct_invitations_query(self, org_name, team_name=None, invitation_id=None):
        """Construct v3 invitation endpoints."""
        # Use v3 endpoints for all invitation operations
        if team_name:
            base_url = f"v3/orgs/{org_name}/teams/{team_name}/pending-invitations"
        else:
            base_url = f"v3/orgs/{org_name}/pending-invitations"

        if invitation_id:
            return f"{base_url}/{invitation_id}"
        return base_url

    def get_users(self, org_name: str, team_name: Optional[str] = None, email_filter: Optional[str] = None):
        """Get list of users from an org. If team name is provided filters on basis of it."""
        query_url = self._construct_url(org_name=org_name, team_name=team_name)
        params = []
        params.append(f"page-size={PAGE_SIZE}")
        if email_filter:
            filter_list = [{"field": "email", "value": quote(email_filter)}]
            search_params = {"filters": filter_list}
            params.append(f"q={json.dumps(search_params)}")
        query_url = "?".join([query_url, "&".join(params)])

        for page in pagination_helper(
            connection=self.connection,
            query=query_url,
            org_name=org_name,
            team_name=team_name,
            operation_name="get users",
            page_number=0,
        ):
            yield UserListResponse(page).users

    @extra_args
    def list(self, org: Optional[str] = None, team: Optional[str] = None, email_filter: Optional[str] = None):
        """Get list of users from an org. If team name is provided filters on basis of it."""
        self.client.config.validate_configuration(csv_allowed=True)
        org_name = org or self.client.config.org_name
        return self.get_users(org_name=org_name, team_name=team, email_filter=email_filter)

    def get_user_details(self, org_name: str, team_name: Optional[str], user_id: str):
        """Get details of a user."""
        response = self.connection.make_api_request(
            "GET",
            self._construct_url(org_name=org_name, team_name=team_name, user_id=user_id),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="get user details",
        )
        return UserResponse(response)

    @extra_args
    def info(self, user_id: str, org: Optional[str] = None, team: Optional[str] = None):
        """Get details of a user."""
        if not user_id:
            raise NgcException(
                "ERROR: Please use valid User ID. \nIf User ID is unknown, list users with email filter."
            ) from None
        check_if_email_used(user_id=user_id)
        user_id = str(user_id) if isinstance(user_id, int) else user_id
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        team_name = team or self.client.config.team_name
        return self.get_user_details(org_name=org_name, team_name=team_name, user_id=user_id)

    def get_invitations(self, org_name: str, team_name: Optional[str] = None, email_filter: Optional[str] = None):
        """Get list of UserInvitations for an org_name, or org/team if team is specified."""
        query_url = self._construct_invitations_query(org_name=org_name, team_name=team_name)
        params = []
        params.append(f"page-size={PAGE_SIZE}")
        if email_filter:
            filter_list = [{"field": "email", "value": quote(email_filter)}]
            search_params = {"filters": filter_list}
            params.append(f"q={json.dumps(search_params)}")
        query_url = "?".join([query_url, "&".join(params)])
        for page in pagination_helper(
            connection=self.connection,
            query=query_url,
            org_name=org_name,
            team_name=team_name,
            operation_name="get invitations",
            page_number=0,
        ):
            # Transform v3 response format to v2 schema format
            transformed_page = self._transform_v3_invitation_response(page)
            yield UserInvitationListResponse(transformed_page).invitations

    def _transform_v3_invitation_response(self, v3_response):
        """Transform v3 invitation response format to v2 schema format."""
        if not isinstance(v3_response, dict) or "invitations" not in v3_response:
            return v3_response

        transformed_invitations = []
        for idx, invitation in enumerate(v3_response["invitations"]):
            # Transform v3 field names to v2 field names
            transformed_invitation = {
                "id": idx + 1,  # Generate sequential ID since v3 doesn't provide one
                "email": invitation.get("userEmail", ""),
                "name": invitation.get("userName", ""),
                "roles": invitation.get("userRoles", []),
                "org": invitation.get("orgName", ""),
                "team": invitation.get("teamName", ""),
                "createdDate": invitation.get("createdDate", ""),
                "type": "TEAM" if invitation.get("teamName") else "ORGANIZATION",
                "isProcessed": False,  # v3 only returns pending invitations
            }
            transformed_invitations.append(transformed_invitation)

        # Preserve pagination and status info
        transformed_response = v3_response.copy()
        transformed_response["invitations"] = transformed_invitations
        return transformed_response

    @extra_args
    def list_invitations(
        self, org: Optional[str] = None, team: Optional[str] = None, email_filter: Optional[str] = None
    ):
        """Get list of UserInvitations for an org_name, or org/team if team is specified."""
        self.client.config.validate_configuration(csv_allowed=True)
        org_name = org or self.client.config.org_name
        invitations_list = self.get_invitations(org_name=org_name, team_name=team, email_filter=email_filter)
        if org_name and not team:
            # The list of invitations when team is not specified still includes invitations for Teams.
            # Must filter those out.
            org_only_invitations = []
            for page in invitations_list:
                for invitation in page:
                    if invitation.type == "ORGANIZATION":
                        org_only_invitations.append(invitation)
            return [org_only_invitations]
        return invitations_list

    def get_invitation_details(self, invitation_identifier: str, org_name: str, team_name: Optional[str] = None):
        """Get details about a specific user invitation based using their unique Invitation ID or Invitation Email
        By default, looks for specified-user's invitation in current org's invitations. If `team_name` specified,
        searches for specified-user's invitation in org/team invitations.
        User ID and Invitation ID are mutually exclusive. So if the `user_id` that is passed is a unique User ID,
        this method will return None.
        Only `add-user` commands for both org and team modules use the email argument. This is because the email is the
        only attribute of an invitation known to use when initially adding/inviting the user. Multiple invitations
        may be returned, as one email can have multiple invitations.
        There will only be one invitation returned. This is because an Invitation ID is either for
        an Organization or Team invitation.
        """  # noqa: D205
        org_invitation = None
        team_invitation = None
        if team_name:
            try:
                team_invitation_gen = self.list_invitations(org=org_name, team=team_name)
                team_invitation = next(
                    (
                        invitation
                        for page in team_invitation_gen
                        for invitation in page
                        if invitation_identifier in [str(invitation.id), invitation.email]
                    ),
                    None,
                )
            except ResourceNotFoundException:
                pass
        else:
            # NOTE: The response for 'org/{org-name}/users/invitations/{id}' endpoint includes Team invitations...
            # So must only return Invitation with matching ID if the type if "ORGANIZATION".
            team_invitation = None
            try:
                org_invitation_gen = self.list_invitations(org=org_name)
                org_invitation = next(
                    (
                        invitation
                        for page in org_invitation_gen
                        for invitation in page
                        if invitation_identifier in [str(invitation.id), invitation.email]
                        and invitation.type == "ORGANIZATION"
                    ),
                    None,
                )
            except ResourceNotFoundException:
                pass

        return org_invitation if org_invitation else team_invitation

    @extra_args
    def invitation_info(self, invitation_identifier: str, org: Optional[str] = None, team: Optional[str] = None):
        """Get details about a specific user invitation based using their unique Invitation ID or Invitation Email.
        By default, looks for specified-user's invitation in current org's invitations. If `team_name` specified,
        searches for specified-user's invitation in org/team invitations.
        User ID and Invitation ID are mutually exclusive. So if the `user_id` that is passed is a unique User ID,
        this method will return None.
        Only `add-user` commands for both org and team modules use the email argument. This is because the email is the
        only attribute of an invitation known to use when initially adding/inviting the user. Multiple invitations
        may be returned, as one email can have multiple invitations.
        When using the Invitation ID, there will only be one invitation returned. This is because an Invitation ID is
        either for an Organization or Team invitation.
        """  # noqa: D205
        if not invitation_identifier:
            raise InvalidArgumentError("ERROR: Please use a valid Invitation ID or Invitation Email") from None
        if not isinstance(invitation_identifier, str):
            raise InvalidArgumentError("ERROR: Please use a String Invitation ID or String Invitation Email") from None
        email_id_used(user_id=invitation_identifier)
        self.client.config.validate_configuration()

        org_name = org or self.client.config.org_name
        invitation_details = self.get_invitation_details(
            invitation_identifier=invitation_identifier, org_name=org_name, team_name=team
        )
        if not invitation_details:
            team_info = f"team '{team}' under org" if team else "org"
            if invitation_identifier.isdigit():
                error_msg = f"No User nor Invitation with ID '{invitation_identifier}' "
            else:
                error_msg = f"No User nor Invitation with Email '{invitation_identifier}' "
            error_msg += f"exists for {team_info} '{org_name}'."
            raise ResourceNotFoundException(error_msg)
        return invitation_details

    def create_a_user(self, email: str, name: str, roles: List[str], org_name: str, team_name: Optional[str] = None):
        """Creates user in an organization. Or, if team_name specific, creates user in org/team."""  # noqa: D401
        user_create_request = UserCreateRequest()
        user_create_request.email = email
        user_create_request.name = name
        roles_set = {*roles}
        user_create_request.roleTypes = list(roles_set)
        try:
            response = self.connection.make_api_request(
                "POST",
                self._construct_url(org_name, team_name),
                payload=user_create_request.toJSON(False),
                auth_org=org_name,
                auth_team=team_name,
                operation_name="create user",
            )
            return UserResponse(response)
        except NgcAPIError:
            raise NgcException("Error inviting user. Please make sure the roles assigned are valid.") from None

    @extra_args
    def create(self, email: str, name: str, roles: List[str], org: Optional[str] = None, team: Optional[str] = None):
        """Creates user in an organization. Or, if team_name specific, creates user in org/team."""  # noqa: D401
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        return self.create_a_user(email=email, name=name, roles=roles, org_name=org_name, team_name=team)

    def _map_ngc_to_nca_role(self, roles: List[str]) -> str:
        """Map NGC roles to NCA roles (MEMBER or ADMIN)."""
        for role in roles:
            if role in ["USER_ADMIN", "ORG_ADMIN", "ORG_OWNER"]:
                return "ADMIN"
        return "MEMBER"

    def _build_nca_invitation_payload(
        self, email: str, roles: List[str], expiry_hours: int, org_name: str, name: str = None, message: str = None
    ) -> dict:
        """Build NCA invitation payload with correct format."""
        nca_role = self._map_ngc_to_nca_role(roles)
        expiry_minutes = expiry_hours * 60  # Convert hours to minutes for backend

        # Use custom message or default message
        invite_message = message or f"You have been invited to join {org_name} organization"

        payload = {
            "email": email,
            "inviteAs": nca_role,
            "message": invite_message,
            "invitationExpirationIn": expiry_minutes,
        }

        if name:
            payload["name"] = name

        return payload

    def nca_invite_user(
        self,
        email: str,
        roles: List[str],
        team: str = None,
        expiry_hours: int = 24,
        name: str = None,
        message: str = None,
    ):
        """Invite a user to the org via NCA using Starfleet ID token."""
        self.client.config.validate_configuration()
        org_name = self.client.config.org_name

        # Get authentication token
        auth = self.client.authentication
        starfleet_token = auth._get_starfleet_token()

        # Build invitation payload with both name and message support
        payload = self._build_nca_invitation_payload(email, roles, expiry_hours, org_name, name, message)

        # Debug logging to help troubleshoot expiry issues
        logger.debug("NCA invitation payload: email=%s, expiry_hours=%s, payload=%s", email, expiry_hours, payload)

        # Note: 'name' and 'orgName' are not in the documented schema

        # For NCA invitations, we need to bypass the regular auth and use only the Starfleet token
        # Don't pass auth_org to avoid conflicting authentication headers
        headers = {
            "Authorization": f"Bearer {starfleet_token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER_AGENT} {NGC_CLI_USER_AGENT_TEXT}" if NGC_CLI_USER_AGENT_TEXT else USER_AGENT,
            "nv-ngc-org": org_name,  # Add org header manually since we're not using auth_org
        }

        # Add device ID if available
        if hasattr(self.client.config, "starfleet_device_id") and self.client.config.starfleet_device_id:
            sf_device_id_and_email = f"{SF_DEVICE_ID}-{self.client.config.starfleet_kas_email}"
            sf_device_id = shortuuid.uuid(name=sf_device_id_and_email)[:19]
            headers["X-Device-Id"] = sf_device_id

        try:
            # Make direct request with custom headers
            # Get base URL from client config if connection doesn't have it
            base_url = self.connection.base_url or self.client.config.base_url
            if not base_url:
                raise NgcException("API base URL not configured")

            # Use team-specific endpoint if team is provided
            if team:
                url = f"{base_url}/v3/orgs/{org_name}/teams/{team}/users/nca-invitations"
            else:
                url = f"{base_url}/v3/orgs/{org_name}/users/nca-invitations"

            # Log the request
            logger.debug("Requesting URL (POST): %s", url)
            logger.debug("Payload: %s", payload)

            response = requests.post(
                url, data=json.dumps(payload), headers=headers, timeout=REQUEST_TIMEOUT_SECONDS, verify=True
            )

            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response: %s", response.text)

            # Handle 409 first - user already in NCA (this is SUCCESS, not an error!)
            if response.status_code == 409:
                error_msg = response.json().get("requestStatus", {}).get("statusDescription", response.text)
                if "already member of the NCA" in error_msg:
                    logger.debug("User already in NCA, skipping invitation")
                    return {"status": "already_member", "message": error_msg}
                # Some other 409 conflict
                raise NgcException(f"Conflict: {error_msg}")

            # Handle other error cases
            if response.status_code >= 400:
                error_msg = response.json().get("requestStatus", {}).get("statusDescription", response.text)
                if response.status_code == 403:
                    raise NgcException("You don't have permission to invite users to this organization.")
                if response.status_code == 400 and "external user" in error_msg.lower():
                    if "Adding external users to the NGC org account is not allowed" in error_msg:
                        # Provide enhanced error message for specific external user groups error
                        enhanced_msg = (
                            "Cannot invite external user: Adding external users to the NGC org account is not allowed. "
                            'Instead, use "external user groups."\n\n'
                            "This organization requires external users to be added through 'external user groups' "
                            "rather than direct invitations. Please contact your organization administrator "
                            "for guidance on adding external users to this organization."
                        )
                        raise NgcException(enhanced_msg)
                    # Generic external user error
                    raise NgcException(error_msg)
                raise NgcAPIError(
                    f"Client Error: {response.status_code} Response: {error_msg}",
                    response=response,
                    explanation=response.text,
                    status_code=response.status_code,
                )

            return response.json()

        except NgcAPIError:
            raise
        except requests.exceptions.RequestException as e:
            raise NgcException(f"Network error while inviting user: {str(e)}") from e
        except (ValueError, KeyError) as e:
            # Handle specific error cases from your diagram
            if "404/500" in str(e):
                raise NgcException("404/500 DB Issue") from e
            if "404/403" in str(e):
                raise NgcException("404/403 Invite permission issue, don't go to step 3") from e
            if "409" in str(e):
                raise NgcException("409 Already Member of NCA") from e
            if "409" in str(e) and "Pending" in str(e):
                raise NgcException("409 Already Pending in NCA") from e
            raise NgcException(f"Error inviting user: {str(e)}") from e

    def add_user_to_team(self, user_id: int, roles: List[str], org_name: str, team_name: str):
        """Adds a confirmed user to the specified team."""  # noqa: D401
        role_q = "&".join(["roles={}".format(r) for r in roles])
        url = self._construct_url(org_name=org_name, team_name=team_name, user_id=user_id)
        base_url = f"{url}?{role_q}"
        self.connection.make_api_request(
            "POST", base_url, auth_org=org_name, auth_team=team_name, operation_name="add user to team"
        )

    @extra_args
    def add_to_team(self, user_id: int, roles: List[str], org: Optional[str] = None, team: Optional[str] = None):
        """Adds a confirmed user to the specified team."""  # noqa: D401
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        team_name = team or self.client.config.team_name
        return self.add_user_to_team(user_id=user_id, roles=roles, org_name=org_name, team_name=team_name)

    def remove_user(self, user_id: int, org_name: str, team_name: Optional[str] = None):
        """Removes user from an organization. Or, if team_name specified, removes user from org/team."""  # noqa: D401
        logger.debug("DELETING USER: %s", user_id)
        self.connection.make_api_request(
            "DELETE",
            self._construct_url(org_name=org_name, team_name=team_name, user_id=user_id),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="remove user",
        )

    @extra_args
    def remove(self, user_id: int, org: Optional[str] = None, team: Optional[str] = None):
        """Removes user from an organization. Or, if team_name specified, removes user from org/team."""  # noqa: D401
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        return self.remove_user(user_id=user_id, org_name=org_name, team_name=team)

    def delete_an_invitation(self, invitation_id: int, org_name: str, team_name: Optional[str] = None):  # noqa: D102
        query = self._construct_invitations_query(org_name=org_name, team_name=team_name, invitation_id=invitation_id)
        self.connection.make_api_request(
            "DELETE", query, auth_org=org_name, auth_team=team_name, operation_name="delete invitation"
        )

    @extra_args
    def delete_invitation(self, invitation_id: int, org: Optional[str] = None, team: Optional[str] = None):
        """Delete an invitation."""
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        return self.delete_an_invitation(invitation_id=invitation_id, org_name=org_name, team_name=team)

    def update_user_info(self, name: str):
        """Updates current user's information."""  # noqa: D401
        # Step 1: Update user information with PATCH request
        user_update_request = UserUpdateRequest()
        user_update_request.name = name
        query = f"{API_VERSION}/users/me"
        self.connection.make_api_request(
            "PATCH", query, payload=user_update_request.toJSON(False), operation_name="update user info"
        )
        # Step 2: Get user information (including roles) with GET request
        response = self.connection.make_api_request("GET", query, operation_name="get user info")
        return UserResponse(response)

    @extra_args
    def update(self, name: str):
        """Updates current user's information."""  # noqa: D401
        if not isinstance(name, str):
            raise InvalidArgumentError("ERROR: Name argument must be a String") from None
        self.client.config.validate_configuration()
        return self.update_user_info(name=name)

    def update_user_roles(
        self,
        user_id: int,
        org_name: str,
        team_name: Optional[str] = None,
        roles: Optional[List] = None,
        add_roles: Optional[List] = None,
        remove_roles: Optional[List] = None,
    ):
        """Updates user roles in an organization or a team."""  # noqa: D401
        # For team-level operations, use v3 endpoints
        if team_name:
            # Get user email for v3 API calls
            user_email = self._get_team_user_email(user_id, org_name, team_name)

            if roles:
                # Use v3 add-role endpoint for role replacement (add-role can handle full role sets)
                self._add_team_user_roles(email=user_email, roles=roles, org_name=org_name, team_name=team_name)
                # Return v2-style response for compatibility (get updated user details)
                return UserResponse(self.get_user_details(org_name=org_name, team_name=team_name, user_id=str(user_id)))

            add_role_response = None
            remove_role_response = None
            if add_roles:
                # Use v3 add-role endpoint for team-level operations
                self._add_team_user_roles(email=user_email, roles=add_roles, org_name=org_name, team_name=team_name)
                add_role_response = UserResponse(
                    self.get_user_details(org_name=org_name, team_name=team_name, user_id=str(user_id))
                )
            if remove_roles:
                # Use v3 remove-role endpoint for team-level operations
                self._remove_team_user_roles(
                    email=user_email, roles=remove_roles, org_name=org_name, team_name=team_name
                )
                remove_role_response = UserResponse(
                    self.get_user_details(org_name=org_name, team_name=team_name, user_id=str(user_id))
                )
            return [add_role_response, remove_role_response]

        # For org-level operations, continue using v2 endpoints
        url = self._construct_url(org_name, team_name=team_name, user_id=user_id)
        if roles:
            role_q = "&".join(["roles={}".format(r) for r in roles])
            base_url = f"{url}/update-role?{role_q}"
            response = self.connection.make_api_request(
                "PATCH", base_url, auth_org=org_name, auth_team=team_name, operation_name="update user role"
            )
            return UserResponse(response)
        add_role_response = None
        remove_role_response = None
        if add_roles:
            add_role_q = "&".join(["roles={}".format(r) for r in add_roles])
            add_role_url = f"{url}/add-role?{add_role_q}"
            add_role_response = self.connection.make_api_request(
                "PATCH", add_role_url, auth_org=org_name, auth_team=team_name, operation_name="add user roles"
            )
            add_role_response = UserResponse(add_role_response)
        if remove_roles:
            # For org-level remove operations, use v3 endpoint
            # Convert user_id to email if needed for v3 endpoint
            user_email = self._get_user_email(user_id, org_name)

            # Use v3 remove-role endpoint for org-level operations
            self._remove_org_user_roles(email=user_email, roles=remove_roles, org_name=org_name)

            # Get updated user info to return consistent response
            remove_role_response = self.info(user_id=user_id, org=org_name)
        return [add_role_response, remove_role_response]

    def _add_team_user_roles(self, email: str, roles: List[str], org_name: str, team_name: str):
        """Add roles to team user using v3 endpoint."""
        # Get current user's Starfleet ID for NV-actor-ID header
        try:
            current_user = self.user_who(org_name=org_name)
            starfleet_id = current_user.user.starfleetId
            if not starfleet_id:
                raise NgcException(STARFLEET_ID_NOT_FOUND_ERROR)
        except Exception as e:
            raise NgcException(f"Failed to get current user's Starfleet ID: {str(e)}") from e

        # Build query parameters for v3 endpoint
        roles_query = "&".join([f"roles={role}" for role in roles])

        try:
            # Use standard NGC authentication flow with NV-actor-ID header
            response = self.connection.make_api_request(
                "PATCH",
                f"/v3/orgs/{org_name}/teams/{team_name}/users/{email}/add-role?{roles_query}",
                auth_org=org_name,
                auth_team=team_name,
                extra_auth_headers={"NV-actor-ID": starfleet_id},
                operation_name="add team user roles v3",
            )
            return response
        except Exception as e:
            raise NgcException(f"Failed to add team user roles: {str(e)}") from e

    def _remove_team_user_roles(self, email: str, roles: List[str], org_name: str, team_name: str):
        """Remove roles from team user using v3 endpoint."""
        # Get current user's Starfleet ID for NV-actor-ID header
        try:
            current_user = self.user_who(org_name=org_name)
            starfleet_id = current_user.user.starfleetId
            if not starfleet_id:
                raise NgcException(STARFLEET_ID_NOT_FOUND_ERROR)
        except Exception as e:
            raise NgcException(f"Failed to get current user's Starfleet ID: {str(e)}") from e

        # Build query parameters for v3 endpoint
        roles_query = "&".join([f"roles={role}" for role in roles])

        try:
            # Use standard NGC authentication flow with NV-actor-ID header
            response = self.connection.make_api_request(
                "DELETE",
                f"/v3/orgs/{org_name}/teams/{team_name}/users/{email}/remove-role?{roles_query}",
                auth_org=org_name,
                auth_team=team_name,
                extra_auth_headers={"NV-actor-ID": starfleet_id},
                operation_name="remove team user roles v3",
            )
            return response
        except Exception as e:
            raise NgcException(f"Failed to remove team user roles: {str(e)}") from e

    def _get_team_user_email(self, user_id, org_name, team_name):
        """Get user email from user_id for team operations (which might be email or numeric ID)."""
        # If user_id already looks like an email, return it
        if "@" in str(user_id):
            return str(user_id)

        # For team-level operations, get user details with team context
        try:
            user_details = self.get_user_details(org_name=org_name, team_name=team_name, user_id=user_id)
            if user_details and user_details.user:
                return user_details.user.email
            raise NgcException(f"User {user_id} not found or has no email")
        except Exception as e:
            raise NgcException(f"Failed to get user email for user_id {user_id}: {str(e)}") from e

    @extra_args
    def update_roles(
        self,
        user_id: int,
        roles: Optional[List] = None,
        add_roles: Optional[List] = None,
        remove_roles: Optional[List] = None,
        org: Optional[str] = None,
        team: Optional[str] = None,
    ):
        """Updates user roles in an organization or a team."""  # noqa: D401
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        return self.update_user_roles(
            user_id=user_id,
            roles=roles,
            add_roles=add_roles,
            remove_roles=remove_roles,
            org_name=org_name,
            team_name=team,
        )

    def user_who(self, org_name: Optional[str] = None):
        """Returns user information."""  # noqa: D401
        if org_name:
            request_endpoint = f"{API_VERSION}/users/me?org-name={org_name}"
        else:
            request_endpoint = f"{API_VERSION}/users/me"
        response = self.connection.make_api_request(
            "GET", request_endpoint, auth_org=org_name, operation_name="get user info"
        )
        return UserResponse(response)

    def user_who_personal_key(self, sak_key):
        """Returns user information for a Scoped API Key. Normal /users/me endpoint does not work for SAK's.
        If this method change, must change the method under ngcbase.api.authentcation.get_key_details()
        and vice versa.
        """  # noqa: D205, D401
        # pylint: disable=protected-access
        sak_caller_info_object = self.client.config._get_sak_key_details(sak_key)
        return sak_caller_info_object

    @extra_args
    def who(self, org: Optional[str] = None):
        """Returns information about the currently-configured user.
        The org parameter is a filter used for searching for information about the
        currently-configured user in that org.

        If that org is invalid, an error is raised.

        If org is not specified, the org from the current configuration is used.

        If the org is valid, the response is basic meta data of the user,
        as well as user info from that org, user info from every team in that org,
        and the user's roles in that org and those teams.
        """  # noqa: D205, D401
        self.client.config._check_org(org, remote_validation=True)  # pylint: disable=protected-access
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        if self.client.config.app_key and self.client.config.app_key.startswith(SCOPED_KEY_PREFIX):
            sak_key = self.client.config.app_key
            sak_key_details = self.client.authentication.get_sak_key_details(sak_key)
            if sak_key_details and sak_key_details.type == "SERVICE_KEY":
                logger.info("Service key detected. User details are not available.")
                return 0

            sak_caller_info_object = self.user_who_personal_key(sak_key=sak_key)
            return sak_caller_info_object
        return self.user_who(org_name=org_name)

    def get_user_storage_quota(self, user_id: int, org_name: str, ace_name: str):
        """Get user storage quota for a given ACE. If ACE is omitted all quotas will be listed."""
        url = self._construct_url(org_name, user_id=user_id)
        base_url = f"{url}/quota"
        if ace_name:
            base_url = f"{base_url}?ace-name={ace_name}"
        response = self.connection.make_api_request(
            "GET", base_url, auth_org=org_name, operation_name="get user storage quota"
        )
        dataset_service_storage_info = self.client.basecommand.dataset.get_user_storage(org_name=org_name)
        return (
            UserStorageQuotaListResponse(response).userStorageQuotas,
            UserStorageQuotaResponse(dataset_service_storage_info).userStorageQuota,
        )

    @extra_args
    def storage_quota(self, user_id: int, org: Optional[str] = None, ace: Optional[str] = None):
        """Get user storage quota for a given ACE. If ACE is omitted all quotas will be listed."""
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        ace_name = ace or self.client.config.ace_name
        return self.get_user_storage_quota(user_id=user_id, org_name=org_name, ace_name=ace_name)

    def _remove_org_user_roles(self, email: str, roles: List[str], org_name: str):
        """Remove roles from user using v3 endpoint."""
        self.client.config.validate_configuration()

        # Get current user's Starfleet ID for NV-actor-ID header
        try:
            current_user = self.user_who(org_name=org_name)
            starfleet_id = current_user.user.starfleetId
            if not starfleet_id:
                raise NgcException(STARFLEET_ID_NOT_FOUND_ERROR)
        except Exception as e:
            raise NgcException(f"Failed to get current user's Starfleet ID: {str(e)}") from e

        # Build query parameters for v3 remove-role endpoint
        roles_query = "&".join([f"roles={role}" for role in roles])
        endpoint = f"/v3/orgs/{org_name}/users/{email}/remove-role?{roles_query}"

        # Use standard NGC authentication flow with NV-actor-ID header
        extra_auth_headers = {"NV-actor-ID": starfleet_id}

        try:
            response = self.connection.make_api_request(
                verb="DELETE",
                endpoint=endpoint,
                auth_org=org_name,
                extra_auth_headers=extra_auth_headers,
                operation_name="remove user roles v3",
            )
            return response if response else {"status": "success"}

        except Exception as e:
            raise NgcException(f"Failed to remove user roles: {str(e)}") from e

    def _get_user_email(self, user_id, org_name):
        """Get user email from user_id (which might be email or numeric ID)."""
        # If user_id already looks like an email, return it
        if "@" in str(user_id):
            return str(user_id)

        # For org-level operations, we need to call get_user_details directly with team_name=None
        # to construct an org-only URL (bypassing the info method which forces team context)
        try:
            user_details = self.get_user_details(org_name=org_name, team_name=None, user_id=user_id)
            if user_details and user_details.user:
                return user_details.user.email
            raise NgcException(f"User {user_id} not found or has no email")
        except Exception as e:
            raise NgcException(f"Failed to get user email for user_id {user_id}: {str(e)}") from e

    def patch_add_role_create_user(
        self, email: str, org_name: str, team_name: Optional[str] = None, ngc_roles: Optional[List[str]] = None
    ):
        """Handle PATCH addRole/createUser after successful NCA invitation."""
        try:
            # Attempt to add user with NGC roles if specified
            if not ngc_roles:
                return {"status": "no_roles", "message": "No NGC roles specified, invitation complete"}
            # Check if user already exists in org/team
            try:
                existing_users = list(self.list(org=org_name, team=team_name, email_filter=email))
                if existing_users and existing_users[0]:
                    # User exists, update roles
                    user_id = existing_users[0][0].user.id  # Get user ID
                    if team_name:
                        self.add_to_team(user_id=user_id, roles=ngc_roles, org=org_name, team=team_name)
                    else:
                        # Update org roles (implement if needed)
                        pass
                    return {"status": "roles_updated", "message": "User roles updated successfully"}
                # User doesn't exist yet, create invitation
                if team_name:
                    self.create(email=email, name="", roles=ngc_roles, org=org_name, team=team_name)
                else:
                    self.create(email=email, name="", roles=ngc_roles, org=org_name)
                return {"status": "invitation_created", "message": "NGC invitation created"}

            except NgcAPIError as e:
                if "400" in str(e):
                    raise NgcException("400 Validation Error (message will tell the reason)") from e
                if "404/500" in str(e):
                    raise NgcException("404/500 DB Issue") from e
                if "404/403" in str(e):
                    raise NgcException("404/403 Invite permission issue") from e
                raise NgcException(f"Error in role/user creation: {str(e)}") from e

        except Exception as e:
            raise NgcException(f"Failed to complete user setup: {str(e)}") from e

    def _handle_starfleet_request_error(self, response):
        """Handle errors from starfleet requests."""
        try:
            response_json = response.json()
            error_msg = response_json.get("requestStatus", {}).get("statusDescription", response.text)
            explanation = json.dumps(response_json)
        except (ValueError, KeyError):
            error_msg = response.text
            explanation = json.dumps({"error": response.text})

        raise NgcAPIError(
            f"Client Error: {response.status_code} Response: {error_msg}",
            response=response,
            explanation=explanation,
            status_code=response.status_code,
        )

    def add_user_roles_v3(self, email: str, roles: List[str], org_name: str):
        """Add roles to user using v3 endpoint."""
        self.client.config.validate_configuration()

        auth = self.client.authentication
        starfleet_token = auth._get_starfleet_token()

        # Build query parameters instead of JSON body
        roles_query = "&".join([f"roles={role}" for role in roles])

        headers = {
            "Authorization": f"Bearer {starfleet_token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER_AGENT} {NGC_CLI_USER_AGENT_TEXT}" if NGC_CLI_USER_AGENT_TEXT else USER_AGENT,
            "nv-ngc-org": org_name,
        }

        if hasattr(self.client.config, "starfleet_device_id") and self.client.config.starfleet_device_id:
            sf_device_id_and_email = f"{SF_DEVICE_ID}-{self.client.config.starfleet_kas_email}"
            sf_device_id = shortuuid.uuid(name=sf_device_id_and_email)[:19]
            headers["X-Device-Id"] = sf_device_id

        try:
            base_url = self.connection.base_url or self.client.config.base_url
            if not base_url:
                raise NgcException("API base URL not configured")

            # Use query parameters, not JSON body
            url = f"{base_url}/v3/orgs/{org_name}/users/{email}/add-role?{roles_query}"

            logger.debug("Requesting URL (PATCH): %s", url)

            response = requests.patch(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS, verify=True)

            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response: %s", response.text)

            if response.status_code >= 400:
                error_msg = response.json().get("requestStatus", {}).get("statusDescription", response.text)
                if response.status_code == 400 and "Cannot update role of self" in error_msg:
                    raise NgcException("Cannot update role of self")
                raise NgcAPIError(
                    message=f"Client Error: {response.status_code} Response: {error_msg}",
                    status_code=response.status_code,
                )

            return response.json()

        except NgcAPIError:
            raise
        except requests.exceptions.RequestException as e:
            raise NgcException(f"Network error while adding user roles: {str(e)}") from e
        except Exception as e:
            raise NgcException(f"Error adding user roles: {str(e)}") from e
