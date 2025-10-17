# $Id: stratos.py 79680 2025-10-15 18:49:06Z pomakis $

from __future__ import annotations
import time
import datetime
import json
import enum
import geojson
import validators
import requests
import math
from urllib.parse import quote
import os
import zipfile
import tempfile
import collections
import typing
from PIL import Image
import io
from threading import Timer

class Stratos:
    """The CubeWerx Stratos Administration Interface."""

    def __init__(self, deploymentUrl: str, username: str, password: str,
                 authUrl: str=None, language: str=None):
        """Create a new `Stratos` object.

        Args:
            deploymentUrl: The URL of a CubeWerx Stratos deployment.
                E.g., "https://somewhere.com/cubewerx/".
            username: The username (with an Administrator role) to log
                in as.
            password: the password of the specified username.
            authUrl: The URL of the CubeWerx Stratos Authentication Server
                to use (e.g., "https://somewhereelse.com/cubewerx/auth"),
                or None to use the one provided by the specified deployment.
            language: the user's preferred language(s) as a comma-separated
                list of RFC 4647 language tags (e.g., "en-CA,en,fr-CA,fr"),
                or None.  Note that currently most of the strings that
                CubeWerx Stratos produces are available only in English.

        If the login is unsuccessful for any reason, a `LoginException`
        is raised.  The reason can be ascertained by which specific
        subclass is raised.

        Raises:
            `NotAStratosException`: The specified deploymentUrl is not a
                CubeWerx Stratos deployment.
            `IncompatibleStratosVersionException`: The CubeWerx Stratos
                Geospatial Data Server is not of a compatible version.
            `NotAnAuthServerException`: the specified authUrl is not a
                CubeWerx Stratos Authentication Server.
            `AuthServerVersionTooLowException`: The version number of the
                CubeWerx Stratos Authentication Server is too low.
            `InvalidCredentialsException`: Invalid username or password.
            `NotAdministratorException`: The user does not have
                Administrator privileges.
            `LoginAttemptsTooFrequentException`: Login attempts are being
                made too frequently.
            `NoMoreSeatsException`: No more seats are available for the
                user (not applicable for most servers).
        """
        # Append a trailing "/" to the deployment URL if necessary.
        if not deploymentUrl.endswith("/"): deploymentUrl += "/"

        # Verify arguments.
        if not validators.url(deploymentUrl):
            raise ValueError("Invalid deployment URL")
        if authUrl and not validators.url(authUrl):
            raise ValueError("Invalid authentication-server URL")
        if not username:
            raise ValueError("No username provided")

        # Verify that the specified deployment actually points to a
        # CubeWerx Stratos deployment of a compatible version.  Since
        # there's no guarantee that future versions of CubeWerx Stratos
        # will behave the same way as 9.8 (or the 9.7 development stream
        # leading up to it), we have little choice but to only consider
        # 9.7.x or 9.8.x as compatible versions.
        response = requests.get(deploymentUrl + "cubeserv/default/alive")
        if response.status_code != 200: raise NotAStratosException()
        cwVersion = response.headers.get("CubeWerx-Stratos-Version")
        if not cwVersion:
            cwVersion = response.headers.get("CubeWerx-Suite-Version")
        if not cwVersion:  # earlier versions didn't provide this header
            raise IncompatibleStratosVersionException(None, "9.8.x")
        else:
            xyzList = cwVersion.split(".")
            versionNumInt = int(xyzList[0]) * 1000000 \
                + int(xyzList[1]) * 1000 \
                + int(xyzList[2])
            if versionNumInt < 9007002 or versionNumInt >= 9009000:
                raise IncompatibleStratosVersionException(cwVersion, "9.8.x")

        # Log in.
        authUrl = authUrl.rstrip("/") if authUrl else deploymentUrl + "auth"
        credentials, authorizationToken = \
            self.__login(authUrl, username, password)

        # Assign object values.
        self.__credentialsRefreshRate = 8*60 # 8 minutes
        self.__credentialsRefreshTimer = None
        self._deploymentUrl = deploymentUrl
        self._authUrl = authUrl
        self.__language = language if language else None
        self._cubeservUrl = deploymentUrl + "cubeserv/default"
        self._adminUrl = self._cubeservUrl + "/admin"
        self._credentials = Credentials(credentials)
        self.__authorizationToken = authorizationToken

        self.__versionObj = None

        # TODO: Perhaps query the server for the value of the
        # auth.credentialsValidityDuration configuration parameter
        # and use that to decide an appropriate value for
        # __credentialsRefreshRate.

        # Set a timer to refresh the user's credentials from time to time.
        self.__setRefreshCredentialsTimer()

    def __del__(self):
        """@private"""
        if self.__credentialsRefreshTimer:
          self.__credentialsRefreshTimer.cancel()
          self.__credentialsRefreshTimer = None

    @property
    def credentials(self) -> Credentials:
        """The credentials of the CubeWerx Stratos administration user
        that we're logged in as.
        """
        return self._credentials

    @property
    def serverVersion(self) -> str:
        """The x.y.z version number of the CubeWerx Stratos Geospatial
        Data Server."""
        self.__fetchVersionObj()
        return self.__versionObj.get("versionNumber")

    @property
    def serverVersionFull(self) -> str:
        """The full version string of the CubeWerx Stratos Geospatial
        Data Server."""
        self.__fetchVersionObj()
        return self.__versionObj.get("fullStr")

    @property
    def licenseExpirationDate(self) -> datetime.date | None:
        """The license expiry date of the CubeWerx Stratos Geospatial
        Data Server, or None if the license has no expiry date."""
        self.__fetchVersionObj()
        dateStr = self.__versionObj.get("licenseExpiration")
        return datetime.date.fromisoformat(dateStr) if dateStr else None

    @property
    def language(self) -> str | None:
        """The user's preferred language(s) as a comma-separated list
        of RFC 4647 language tags (e.g., "en-CA,en,fr-CA,fr"), or None.
        Note that currently most of the strings that CubeWerx Stratos
        produces are available only in English."""
        return self.__language

    @language.setter
    def language(self, value: str | None):
        self.__language = language if language else None

    @property
    def commonRequestHeaders(self) -> dict:
        """The HTTP headers that must be added to manually-crafted admin
        API or OGC API server requests in order to pass the correct
        credentials and language preferences, etc."""
        headers = {
            "Authorization": "CwAuth " + self.__authorizationToken
        }
        if self.__language:
            headers["Accept-Language"] = self.__language
        return headers

    @property
    def __jsonRequestHeaders(self) -> dict:
        requestHeaders = { "Accept": "application/json" }
        requestHeaders.update(self.commonRequestHeaders)
        return requestHeaders

    def getStats(self, nPeriods: int=24,
            nSecondsPerPeriod: int=3600) -> Stats:
        """Fetch current system statistics.

        Args:
            nPeriods: The number of time periods to return in the
                nActiveUsers list.
            nSecondsPerPeriod: The duration in seconds of each time
                period in the nActiveUsers list.

        Returns:
            A `Stats` object providing current system statistics.
        """
        statsUrl = self._adminUrl + "/stats"
        params = {
            "nPeriods": nPeriods,
            "periodDuration": nSecondsPerPeriod
        }
        response = requests.get(statsUrl, headers=self.__jsonRequestHeaders,
            params=params)
        ServerException.raise_for_status(response)
        return Stats(response.json())

    def getRequestHistory(self, maxPeriods: int=24) -> RequestHistory:
        """Fetch a summary of the recent request history.

        Args:
            maxPeriods: The maximum number of time periods (typically
                but not necessarily months, depending on configuration)
                to return.

        Returns:
            A summary of the recent request history.
        """
        requestHistoryUrl = self._adminUrl + "/requestHistory"
        params = { "maxPeriods": maxPeriods }
        response = requests.get(requestHistoryUrl,
            headers=self.__jsonRequestHeaders, params=params)
        ServerException.raise_for_status(response)
        return RequestHistory(response.json())

    def getLoginHistory(self,
            username: str | None = None,
            ipAddress: str | None = None,
            fromTime: datetime.datetime | None = None,
            toTime: datetime.datetime | None = None,
            order: str = "forward",
            num: int = 100) -> list[LoginHistoryEntry]:
        """Fetch a login history.

        Args:
            username: The CwAuth user to fetch the login history of,
                or None to fetch the login history of all users.
            ipAddress: The IP address to fetch the login history of,
                or None to fetch the login history of all IP addresses.
                If an IPv4 address with less than four octets is specified,
                it matches all IP address beginning with the specified
                octets.
            fromTime: The start date and time inclusive (in the server's
                time zone) of the login history to fetch, or None to fetch
                back indefinitely.
            toTime: The end date and time inclusive (in the server's time
                zone) of the login history to fetch, or None to fetch to
                the current time.
            order: The chronological order of the returned entries,
                one of "forward" or "reverse".
            num: The maximum number of most-recent entries to return.

        Returns:
            A list of `LoginHistoryEntry` objects.
        """
        loginHistoryUrl = self._adminUrl + "/loginHistory"
        params = {}
        if username: params["username"] = username
        if ipAddress: params["ipAddress"] = ipAddress
        if fromTime: params["from"] = fromTime.isoformat()
        if toTime: params["to"] = toTime.isoformat()
        params["order"] = order
        params["num"] = num
        response = requests.get(loginHistoryUrl,
            headers=self.__jsonRequestHeaders, params=params)
        ServerException.raise_for_status(response)
        loginHistory = []
        for entryJson in response.json():
            loginHistory.append(LoginHistoryEntry(entryJson))
        return loginHistory

    def getConfigParams(self) -> dict[str,ConfigParam]:
        """Fetch the available configuration parameters and their values.

        Returns:
            A dictionary mapping configuration parameter names to
            `ConfigParam` objects.
        """
        configUrl = self._adminUrl + "/config"
        response = requests.get(configUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        configParams = {}
        for configParamJson in response.json():
            configParam = ConfigParam(configParamJson, configUrl, self)
            configParams[configParam.name] = configParam

        return configParams

    def getAuthUsers(self, usernames: list=None) -> list[AuthUser]:
        """Fetch a list of CwAuth users.

        Args:
            usernames: A list of usernames to fetch, or None/[] to fetch
                all users.  If specified, the users will be returned in the
                specified order.  If a specified username doesn't exist,
                it's omitted from the returned list.

        Returns:
            The list of all or selected CwAuth users of the Stratos
            Geospatial Data Server.
        """
        usersUrl = self._adminUrl + "/users"
        response = requests.get(usersUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        users = []
        if usernames:
            for username in usernames:
                for userJson in response.json():
                    if userJson.get("username") == username:
                        users.append(AuthUser(dictionary=userJson))
        else:
            for userJson in response.json():
                users.append(AuthUser(dictionary=userJson))

        return users

    def getAuthUser(self, username: str) -> AuthUser | None:
        """Fetch the specified CwAuth user.

        Args:
            username: a username

        Returns:
            The CwAuth user with the specified username, or None if no
            such user exists.
        """
        userUrl = self._adminUrl + "/users/" + quote(username)
        response = requests.get(userUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)
        return AuthUser(dictionary=response.json())

    def addOrReplaceAuthUser(self, user: AuthUser) -> bool:
        """Add a new CwAuth user to the Stratos Geospatial Data Server.
        If a user with the same username already exists, that user's
        definition is replaced.

        Args:
            user: A CwAuth user definition.  Must have an e-mail address
                and a password set.

        Returns:
            True if an existing user was replaced, or False if a new user
            was added.
        """
        # Validate requirements of AuthUser object
        if not user.emailAddress:
            raise ValueError("E-mail address of user not specified")
        if user.password is None:
            raise ValueError("Password of user not specified")

        userUrl = self._adminUrl + "/users/" + quote(user.username)
        response = requests.put(userUrl, headers=self.__jsonRequestHeaders,
            json=user._dict)
        ServerException.raise_for_status(response)
        existingReplaced = (response.status_code == 200)
        return existingReplaced

    def updateAuthUser(self, user: AuthUser):
        """Commit a CwAuth user update to the Stratos Geospatial Data
        Server.  The intended flow is 1) fetch the definition of a
        user with Stratos.getAuthUsers() or Stratos.getAuthUser(), 2)
        update one or more properties of that user, and 3) call this
        method to commit those changes.

        Arguments:
            user: A modified CwAuth user definition.
        """
        userUrl = self._adminUrl + "/users/" + quote(user.username)
        response = requests.patch(userUrl, headers=self.__jsonRequestHeaders,
            json=user._patchDict)
        ServerException.raise_for_status(response)

    def removeAuthUser(self, user: AuthUser | str) -> bool:
        """Remove the specified CwAuth user from the Stratos Geospatial
        Data Server.  The special "admin" user cannot be removed.

        Note that if this `AuthUser` is in an `AuthUser` list that was
        fetched via a call to Stratos.getAuthUsers(), the object isn't
        automatically removed from the list.  It's up to the caller to
        do that if necessary.

        Args:
            user: A CwAuth user definition or username.

        Returns:
            True if the user was removed, or False if the user didn't
            exist.
        """
        username = user.username if isinstance(user, AuthUser) else user
        if username == "admin":
            raise ValueError('Cannot remove user "admin"')
        userUrl = self._adminUrl + "/users/" + quote(username)
        response = requests.delete(userUrl, headers=self.commonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)
        return existingRemoved

    def getRoles(self, roleNames: list=None) -> list[Role]:
        """Fetch a list of roles.

        Args:
            roleNames: A list of role names to fetch, or None/[] to fetch
                all roles; if specified, the roles will be returned in the
                specified order.  If a specified role name doesn't exist,
                it's omitted from the returned list.

        Returns:
            The list of all or selected roles of the Stratos Geospatial
            Data Server.
        """
        rolesUrl = self._adminUrl + "/roles"
        response = requests.get(rolesUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        roles = []
        if roleNames:
            for roleName in roleNames:
                for roleJson in response.json():
                    if roleJson.get("name") == roleName:
                        roles.append(Role(dictionary=roleJson))
        else:
            for roleJson in response.json():
                roles.append(Role(dictionary=roleJson))

        return roles

    def getRole(self, roleName: str) -> Role | None:
        """Fetch the specified role.

        Args:
            roleName: A role name.

        Returns:
            The role with the specified name, or None if no such
            role exists.
        """
        roleUrl = self._adminUrl + "/roles/" + quote(roleName)
        response = requests.get(roleUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)
        return Role(dictionary=response.json())

    def addOrReplaceRole(self, role: Role) -> bool:
        """Add a new role to the Stratos Geospatial Data Server.  If a
        role with the same name already exists, that role's definition
        is replaced.

        Args:
            role: A role definition.

        Returns:
            True if an existing role was replaced, or False if a new role
            was added.
        """
        roleUrl = self._adminUrl + "/roles/" + quote(role.name)
        response = requests.put(roleUrl, headers=self.__jsonRequestHeaders,
            json=role._dict)
        ServerException.raise_for_status(response)
        existingReplaced = (response.status_code == 200)
        return existingReplaced

    def updateRole(self, role: Role):
        """Commit a CwAuth role update to the Stratos Geospatial Data
        Server.  The intended flow is 1) fetch the definition of a role
        with Stratos.getRoles() or Stratos.getRole(), 2) update one or
        more properties of that role, and 3) call this method to commit
        those changes.

        Args:
            role: A modified role definition.
        """
        roleUrl = self._adminUrl + "/roles/" + quote(role.name)
        response = requests.patch(roleUrl, headers=self.__jsonRequestHeaders,
            json=role._patchDict)
        ServerException.raise_for_status(response)

    def removeRole(self, role: Role | str) -> bool:
        """Remove the specified role from the Stratos Geospatial
        Data Server.  Built-in roles such as "Administrator" cannot
        be removed.  (This can be checked with role.isBuiltin.)

        Args:
            role: A role definition or role name.

        Returns:
            True if the role was removed, or False if the role didn't
            exist.
        """
        # Reject attempts to remove built-in roles.  (Although, if the
        # caller provides just a role name, then only the well-known
        # role name "Administrator" can be checked here.)
        if ((isinstance(role, Role) and role.isBuiltin) or
                (isinstance(role, str) and role.name == "Administrator")):
            raise ValueError('Built-in role "%s" cannot be removed' %
                role.name)

        rolename = role.name if isinstance(role, Role) else role
        roleUrl = self._adminUrl + "/roles/" + quote(rolename)
        response = requests.delete(roleUrl, headers=self.__jsonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)
        return existingRemoved

    def getApiKeys(self) -> list[ApiKey]:
        """Fetch the list of API keys.

        Returns:
            The list of all API keys of the Stratos Geospatial
            Data Server.
        """
        apiKeysUrl = self._adminUrl + "/apiKeys"
        response = requests.get(apiKeysUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        apiKeys = []
        for apiKeyJson in response.json():
            apiKeys.append(ApiKey(dictionary=apiKeyJson))

        return apiKeys

    def getApiKey(self, key: str) -> ApiKey | None:
        """Fetch the specified API key.

        Args:
            key: An API key string.

        Returns:
            The API key with the specified key string, or None if no
            such API key exists.
        """
        apiKeyUrl = self._adminUrl + "/apiKeys/" + quote(key)
        response = requests.get(apiKeyUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)
        return ApiKey(dictionary=response.json())

    def addOrReplaceApiKey(self, apiKey: ApiKey) -> bool:
        """Add a new API key to the Stratos Geospatial Data Server.
        If an API key with the same key string already exists, that
        API key's definition is replaced.  If apiKey.key isn't set,
        the server will auto-generate a key string and set apiKey.key
        accordingly.

        Args:
            apiKey: An API key definition.

        Returns:
            True if an existing API key was replaced, or False if a new
            API key was added.
        """
        apiKeysUrl = self._adminUrl + "/apiKeys"
        if apiKey.key:
            apiKeyUrl = apiKeysUrl + "/" + quote(apiKey.key)
            response = requests.put(apiKeyUrl,
                headers=self.__jsonRequestHeaders, json=apiKey._dict)
            ServerException.raise_for_status(response)
            existingReplaced = (response.status_code == 200)
            return existingReplaced
        else:
            response = requests.post(apiKeysUrl,
                headers=self.__jsonRequestHeaders, json=apiKey._dict)
            ServerException.raise_for_status(response)
            responseJson = response.json()
            apiKey._dict["apiKey"] = responseJson.get("apiKey")
            return False

    def updateApiKey(self, apiKey: ApiKey):
        """Commit an API key update to the Stratos Geospatial Data
        Server.  The intended flow is 1) fetch the definition of an
        API key with Stratos.getApiKeys() or Stratos.getApiKey(), 2)
        update one or more properties of that API key, and 3) call this
        method to commit those changes.

        Args:
            apiKey: A modified API key definition.
        """
        apiKeyUrl = self._adminUrl + "/apiKeys/" + quote(apiKey.key)
        response = requests.patch(apiKeyUrl, headers=self.__jsonRequestHeaders,
            json=apiKey._patchDict)
        ServerException.raise_for_status(response)

    def removeApiKey(self, apiKey: ApiKey | str) -> bool:
        """Remove the specified API key from the Stratos Geospatial
        Data Server.

        Args:
            apiKey: An API key definition or key string.

        Returns:
            True if the API key was removed, or False if the API key
            didn't exist.
        """
        key = apiKey.key if isinstance(apiKey, ApiKey) else apiKey
        apiKeyUrl = self._adminUrl + "/apiKeys/" + quote(key)
        response = requests.delete(apiKeyUrl, headers=self.__jsonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)
        return existingRemoved

    def getQuotas(self) -> list[Quota]:
        """Fetch the list of quotas.

        Returns:
            The list of the current quotas that are in place in the
            Stratos Geospatial Data Server.
        """
        quotasUrl = self._adminUrl + "/quotas"
        response = requests.get(quotasUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        quotas = []
        for quotaJson in response.json():
            quotas.append(Quota(quotaJson))

        return quotas

    def getQuota(self, id: str) -> Quota | None:
        """Fetch the specified quota.

        Args:
            id: A quota ID.

        Returns:
            The quota with the specified ID, or None if no such quota
            exists.
        """
        quotaUrl = self._adminUrl + "/quotas/" + quote(id)
        response = requests.get(quotaUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)
        return Quota(response.json())

    def addQuota(self, identityType: QuotaIdentityType, identity: str,
                 field: QuotaField, service: str, operation: str,
                 granularity: QuotaGranularity, limit: int,
                 usage: int = 0) -> Quota:
        """Add a new quota.

        Args:
            identityType: The type of identity that this quota is on.
            identity: The identity (username, role or API key) that this
                quota is on.  The specified username, role or API key must
                exist.
            field: The thing being quotad.
            service: The service (as known by CubeWerx Stratos Analytics)
                that this quota applies to. E.g., "WMS", "WMTS", "WCS",
                "WFS", "WPS", "CSW", or "*" if the quota applies to all
                services.
            operation: The operation (as known by CubeWerx Stratos
                Analytics) that this quota applies to. (e.g., "GetMap",
                "GetFeature"), or "*" if the quota applies to all
                operations.
            granularity: The granularity of this quota (i.e., what unit
                of time it applies to.
            limit: The limit that this quota imposes.
            usage: The current usage (which will be automatically reset
                at the beginning of every unit of time specified by
                the granularity field).

        Returns:
            The new quota.
        """
        quotasUrl = self._adminUrl + "/quotas"
        postDict = {
            "identityType": str(identityType),
            "identity": str(identity),
            "field": str(field),
            "service": str(service) if service else "*",
            "operation": str(operation) if operation else "*",
            "granularity": str(granularity),
            "limit": max(int(limit), 0),
            "usage": max(int(usage), 0)
        }
        response = requests.post(quotasUrl, headers=self.__jsonRequestHeaders,
            json=postDict)
        ServerException.raise_for_status(response)
        return Quota(response.json())

    def updateQuota(self, quota: Quota | str,
                    limit: int | None = None, usage: int | None = None):
        """Update the limit and/or usage of a quota.

        Args:
            quota: A quota definition or ID.
            limit: The new limit that this quota imposes, or None to
                not change.
            usage: The new current usage (which will be automatically
                reset at the beginning of every unit of time specified
                by the granularity field), or None to not change.
        """
        if limit is None and usage is None: return
        isObject = isinstance(quota, Quota)
        id = quota.id if isObject else quota
        quotaUrl = self._adminUrl + "/quotas/" + quote(id)
        patchDict = {}
        if limit is not None:
            limit = max(int(limit), 0)
            patchDict["limit"] = limit
            if isObject: quota._Quota__limit = limit
        if usage is not None:
            usage = max(int(usage), 0)
            patchDict["usage"] = usage
            if isObject: quota._Quota__usage = usage
        response = requests.patch(quotaUrl, headers=self.__jsonRequestHeaders,
            json=patchDict)
        ServerException.raise_for_status(response)

    def removeQuota(self, quota: Quota | str) -> bool:
        """Remove the specified quota from the Stratos Geospatial Data
        Server.

        Args:
            quota: A quota definition or ID.

        Returns:
            True if the quota was removed, or False if the quota
            didn't exist.
        """
        id = quota.id if isinstance(quota, Quota) else quota
        quotaUrl = self._adminUrl + "/quotas/" + quote(id)
        response = requests.delete(quotaUrl, headers=self.__jsonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)
        return existingRemoved

    def getCubeSTORs(self) -> list[CubeSTOR]:
        """Fetch the list of CubeSTOR database details.

        Returns:
            The list of all CubeSTOR databases of the Stratos
            Geospatial Data Server.
        """
        cubestorsUrl = self._adminUrl + "/cubestors"
        response = requests.get(cubestorsUrl, headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        cubestors = []
        for cubestorJson in response.json():
            cubestors.append(CubeSTOR(cubestorJson))

        return cubestors

    def getCubeSTOR(self, dbName: str) -> CubeSTOR | None:
        """Fetch the details of the specified CubeSTOR database.

        Args:
            dbName: A CubeSTOR database name.

        Returns:
            The details of the CubeSTOR database with the specified name,
            or None if no such database exists.
        """
        cubestorUrl = self._adminUrl + "/cubestors/" + quote(dbName)
        response = requests.get(cubestorUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)
        return CubeSTOR(response.json())

    def addCubeSTOR(self, dbName: str, title: str | None,
                    description: str | None) -> CubeSTOR:
        """Add a new CubeSTOR database to the Stratos Geospatial
        Data Server.

        Args:
            dbName: The CubeSTOR database name to use.  Must be no longer
                than 64 characters.
            title: The title of the database, or None.
            description: A short description of the database, or None.

        Returns:
            The new CubeSTOR database details.
        """
        cubestorUrl = self._adminUrl + "/cubestors/" + quote(dbName)
        putDict = {}
        if title: putDict["title"] = title
        if description: putDict["description"] = description
        response = requests.put(cubestorUrl, headers=self.__jsonRequestHeaders,
            json=putDict)
        ServerException.raise_for_status(response)
        return CubeSTOR(response.json())

    def updateCubeSTOR(self, cubestor: CubeSTOR | str,
                       title: str | None = None,
                       description: str | None = None):
        """Update the title and/or description of a CubeSTOR database.

        Args:
            cubestor: A CubeSTOR details object or database name.
            title: the new title of the database, "" to clear the title,
                or None to not change.
            description - The new short description of the database, ""
                to clear the description, or None to not change.
        """
        if title is None and description is None: return
        isObject = isinstance(cubestor, CubeSTOR)
        dbName = cubestor.dbName if isObject else cubestor
        cubestorUrl = self._adminUrl + "/cubestors/" + quote(dbName)
        patchDict = {}
        if title is not None:
            title = str(title)
            patchDict["title"] = title
            if isObject:
                cubestor._CubeSTOR__title = title if title else None
        if description is not None:
            description = str(description)
            patchDict["description"] = description
            if isObject:
                cubestor._CubeSTOR__description = \
                    description if description else None
        response = requests.patch(cubestorUrl,
            headers=self.__jsonRequestHeaders, json=patchDict)
        ServerException.raise_for_status(response)

    def removeCubeSTOR(self, cubestor: CubeSTOR | str) -> bool:
        """Remove the specified CubeSTOR database from the Stratos
        Geospatial Data Server.  WARNING: This will remove any and all
        data that has been loaded into this database.  Some databases
        cannot be removed (determinable by the canDelete property
        of the `CubeSTOR` object).  One such situation is if the
        CubeSTOR database is currently the source of of a data store.
        In this situation, the database must first be removed as the
        source of the data store (via a call to updateDataStore()
        or removeDataStore()).

        Note that if this `CubeSTOR` is in a `CubeSTOR` list that was
        fetched via a call to Stratos.getCubeSTORs(), the object isn't
        automatically removed from the list.  It's up to the caller to
        do that if necessary.

        Args:
            cubestor: A CubeSTOR details object or database name.

        Returns:
            True if the CubeSTOR database was removed, or False if the
            CubeSTOR database didn't exist.
        """
        isObject = isinstance(cubestor, CubeSTOR)
        dbName = cubestor.dbName if isObject else cubestor
        cubestorUrl = self._adminUrl + "/cubestors/" + quote(dbName)
        response = requests.delete(cubestorUrl,
            headers=self.commonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)
        return existingRemoved

    def getDataStores(self) -> list[DataStore]:
        """Fetch the list of CubeWerx Stratos data stores.

        Returns:
            The list of all data stores of the Stratos Geospatial
            Data Server.
        """
        dataStoresUrl = self._adminUrl + "/dataStores"
        response = requests.get(dataStoresUrl,
            headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)

        dataStores = []
        for dataStoreJson in response.json():
            dataStore = DataStore(jsonRep=dataStoreJson)
            dataStoreUrl = dataStoresUrl + "/" + quote(dataStore.name)
            ogcApiLandingPageUrl = (self._cubeservUrl + "/ogcapi/" +
                quote(dataStore.name))
            dataStore._setServerAssociation(self, dataStoreUrl,
                ogcApiLandingPageUrl)
            dataStores.append(dataStore)

        return dataStores

    def getDataStore(self, name: str) -> DataStore | None:
        """Fetch the specified CubeWerx Stratos data store.

        Args:
            name: a data store name

        Returns:
            The CubeWerx Stratos data store with the specified name,
            or None if no such data store exists.
        """
        dataStoreUrl = self._adminUrl + "/dataStores/" + quote(name)
        response = requests.get(dataStoreUrl, headers=self.__jsonRequestHeaders)
        if response.status_code == 404: return None
        ServerException.raise_for_status(response)

        dataStore = DataStore(jsonRep=response.json())
        ogcApiLandingPageUrl = (self._cubeservUrl + "/ogcapi/" +
            quote(dataStore.name))
        dataStore._setServerAssociation(self, dataStoreUrl,
            ogcApiLandingPageUrl)
        return dataStore

    def addOrReplaceDataStore(self, dataStore: DataStore) -> bool:
        """Add a new data store to the Stratos Geospatial Data Server.
        If a data store with the same name already exists, that data
        store's definition is replaced.

        Args:
            dataStore: A data store definition.  Must have a data store
                type and source set.

        Returns:
            True if an existing data store was replaced, or False if a
            new data store was added.
        """
        # Validate requirements of DataStore object.
        if not dataStore.type:
            raise ValueError("Type of data store not specified")
        if not dataStore.source:
            raise ValueError("Source of data store not specified")

        # Add or replace this data store.
        # TODO: Should this be allowed for an existing data store that
        # already has layers?  Probably not.
        dataStoreUrl = self._adminUrl + "/dataStores/" + quote(dataStore.name)
        response = requests.put(dataStoreUrl, headers=self.__jsonRequestHeaders,
            json=dataStore._jsonRep)
        ServerException.raise_for_status(response)
        existingReplaced = (response.status_code == 200)

        ogcApiLandingPageUrl = (self._cubeservUrl + "/ogcapi/" +
            quote(dataStore.name))
        dataStore._setServerAssociation(self, dataStoreUrl,
            ogcApiLandingPageUrl)

        return existingReplaced

    def updateDataStore(self, dataStore: DataStore):
        """Commit a data store update to the Stratos Geospatial Data
        Server.  The intended flow is 1) fetch the definition of a data
        store with Stratos.getDataStores() or Stratos.getDataStore(),
        2) update one or more properties of that data store, and 3)
        call this method to commit those changes.

        Args:
            dataStore: A modified data store definition.
        """
        dataStoreUrl = self._adminUrl + "/dataStores/" + quote(dataStore.name)
        response = requests.patch(dataStoreUrl,
            headers=self.__jsonRequestHeaders, json=dataStore._patchDict)
        ServerException.raise_for_status(response)

    def removeDataStore(self, dataStore: DataStore | str) -> bool:
        """Remove the specified data store from the Stratos Geospatial
        Data Server.  Some data stores cannot be removed (determinable
        by the canDelete property of the `DataStore` object).

        Note that if this `DataStore` is in an `DataStore` list that
        was fetched via a call to Stratos.getDataStores(), the object
        isn't automatically removed from the list.  It's up to the
        caller to do that if necessary.

        Args:
            dataStore: A data store definition or name.

        Returns:
            True if the data store was removed, or False if the data
            store didn't exist.
        """
        name = dataStore.name \
            if isinstance(dataStore, DataStore) else dataStore
        dataStoreUrl = self._adminUrl + "/dataStores/" + quote(name)
        response = requests.delete(dataStoreUrl,
            headers=self.commonRequestHeaders)
        existingRemoved = True
        if response.status_code == 404:
            existingRemoved = False
        else:
            ServerException.raise_for_status(response)

        dataStore._setServerAssociation(None, None, None)

        return existingRemoved

    def getProcessingAcrs(self) -> list[AccessControlRule]:
        """Fetch the access control rules that are currently in place
        for the processing server (i.e., the OGC WPS and the "OGC API -
        Processes" endpoints.  These access control rules can be modified
        and then sent back to the server with a call to
        `setProcessingAcrs`.

        Returns:
            The access control rules that are currently in place for
            the processing server (i.e., the OGC WPS and the "OGC API -
            Processes" endpoints).
        """
        processingUrl = self._adminUrl + "/processing"
        response = requests.get(processingUrl,
                                headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)
        responseJson = response.json()
        accessControlRulesJson = responseJson.get("accessControlRules")
        accessControlRules = []
        if isinstance(accessControlRulesJson, list):
            for acrJson in accessControlRulesJson:
                accessControlRules.append(AccessControlRule(acrJson))
        return accessControlRules

    def setProcessingAcrs(self, accessControlRules: list[AccessControlRule] | None):
        """Set the access control rules for the processing server (i.e.,
        the OGC WPS and the "OGC API - Processes" endpoints).  These
        access control rules shouldn't refer to any content, and should
        not have any "except" clauses.  The only operation classes they
        should grant are EXECUTE_PROCESS and MANAGE_PROCESSES.

        Args:
            accessControlRules: The new set of access control rules to
                put in place for the processing server (i.e., the OGC
                WPS and the "OGC API - Processes" endpoints).
        """
        if not accessControlRules: accessControlRules = []
        processingUrl = self._adminUrl + "/processing"
        acrsJson = []
        for acr in accessControlRules:
            acrsJson.append(acr._jsonRep)
        patchBody = { "accessControlRules": acrsJson }
        response = requests.patch(processingUrl,
            headers=self.__jsonRequestHeaders, json=patchBody)
        ServerException.raise_for_status(response)

    def getCataloguesAcrs(self) -> list[AccessControlRule]:
        """Fetch the access control rules that are currently in place
        for the catalogue server (i.e., the OGC WRS and the "OGC API -
        Records" endpoints.  These access control rules can be modified
        and then sent back to the server with a call to
        `setCataloguesAcrs`.

        Returns:
            The access control rules that are currently in place for
            the catalogue server (i.e., the OGC WRS and the "OGC API -
            Records" endpoints).
        """
        cataloguesUrl = self._adminUrl + "/catalogues"
        response = requests.get(cataloguesUrl,
                                headers=self.__jsonRequestHeaders)
        ServerException.raise_for_status(response)
        responseJson = response.json()
        accessControlRulesJson = responseJson.get("accessControlRules")
        accessControlRules = []
        if isinstance(accessControlRulesJson, list):
            for acrJson in accessControlRulesJson:
                accessControlRules.append(AccessControlRule(acrJson))
        return accessControlRules

    def setCataloguesAcrs(self, accessControlRules: list[AccessControlRule] | None):
        """Set the access control rules for the catalogue server (i.e.,
        the OGC WRS and the "OGC API - Records" endpoints).  These
        access control rules shouldn't refer to any content, and should
        not have any "except" clauses.  The only operation classes they
        should grant are GET_RECORD, INSERT_RECORD, UPDATE_RECORD and
        DELETE_RECORD.

        Args:
            accessControlRules: The new set of access control rules to
                put in place for the catalogue server (i.e., the OGC
                WPS and the "OGC API - Records" endpoints).
        """
        if not accessControlRules: accessControlRules = []
        cataloguesUrl = self._adminUrl + "/catalogues"
        acrsJson = []
        for acr in accessControlRules:
            acrsJson.append(acr._jsonRep)
        patchBody = { "accessControlRules": acrsJson }
        response = requests.patch(cataloguesUrl,
            headers=self.__jsonRequestHeaders, json=patchBody)
        ServerException.raise_for_status(response)

    def __setRefreshCredentialsTimer(self):
        self.__credentialsRefreshTimer = Timer(self.__credentialsRefreshRate,
            self.__refreshCredentialsTimerFn)
        self.__credentialsRefreshTimer.daemon = True
        self.__credentialsRefreshTimer.start()

    def __refreshCredentialsTimerFn(self):
        self.__refreshCredentials()
        self.__setRefreshCredentialsTimer()

    def __refreshCredentials(self):
        refreshUrl = self._authUrl + "/refresh"
        requestHeaders = { "Accept": "application/json" }
        requestHeaders.update(self.commonRequestHeaders)
        response = requests.get(refreshUrl, headers=requestHeaders)
        ServerException.raise_for_status(response)

        # Verify that the authentication server returned a status of
        # "credentialsRefreshed".
        # TODO: handle "credentialsExpired"?
        authStatus = response.headers.get("CwAuth-Status", "unknown")
        if authStatus != "credentialsRefreshed":
            raise LoginException()

        # Parse the response.
        responseJson = response.json()
        credentials = responseJson.get("credentials")
        authorizationToken = responseJson.get("authorizationToken")

        # Verify that the user still has the Administrator role.
        roles = credentials.get("roles", [])
        if not "Administrator" in roles:
            raise NotAdministratorException(username)

        # Adjust the current state.
        self.__authorizationToken = authorizationToken
        self._credentials = Credentials(credentials)

    @staticmethod
    def __login(authUrl: str, username: str, password: str):
        # Try to log in to the specified server.
        # (see "https://requests.readthedocs.io/en/latest/")
        loginUrl = authUrl + "/login"
        requestHeaders = { "Accept": "application/json" }
        data = { "username": username, "password": password }
        response = requests.post(loginUrl, headers=requestHeaders, data=data)
        ServerException.raise_for_status(response)

        # Make sure this is a CubeWerx Stratos version 9.7.x or higher.
        cwVersion = response.headers.get("CubeWerx-Stratos-Version")
        if not cwVersion:
            cwVersion = response.headers.get("CubeWerx-Suite-Version")
        if not cwVersion:
            raise NotAnAuthServerException()
        else:
            xyzList = cwVersion.split(".")
            versionNumInt = int(xyzList[0]) * 1000000 \
                + int(xyzList[1]) * 1000 \
                + int(xyzList[2])
            if versionNumInt < 9007002:
                raise AuthServerVersionTooLowException(cwVersion, "9.7.2")

        # Verify that the authentication server returned a status of
        # "loginSuccessful".
        authStatus = response.headers.get("CwAuth-Status", "unknown")
        if authStatus == "loginFailed":
            raise InvalidCredentialsException()
        elif authStatus == "loginAttemptsTooFrequent":
            raise LoginAttemptsTooFrequentException()
        elif authStatus == "noMoreSeats":
            raise NoMoreSeatsException(username)
        elif authStatus != "loginSuccessful":
            raise LoginException() # catch-all for other auth statuses

        responseJson = response.json()
        credentials = responseJson.get("credentials")
        authorizationToken = responseJson.get("authorizationToken")

        # Verify that the user has the Administrator role.
        roles = credentials.get("roles", [])
        if not "Administrator" in roles:
            raise NotAdministratorException(username)

        # We're done!
        return credentials, authorizationToken

    def __fetchVersionObj(self):
        if not self.__versionObj:
            response = requests.get(self._adminUrl + "/version",
                headers=self.__jsonRequestHeaders)
            ServerException.raise_for_status(response)
            self.__versionObj = response.json()

##############################################################################

class AccessControlRule:
    """A CubeWerx Access Control Rule.

    A rule grants whatever is specified by the "grant" clauses minus
    whatever is specified by the "except" clauses.
    """

    def __init__(self, jsonRep: dict={}):
        """Create a new access control rule.

        Args:
            jsonRep: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        self.__appliesTo = []
        self.__expiresAt = None
        self.__grants = []
        self.__excepts = []

        if jsonRep:
            appliesTo = jsonRep.get("appliesTo")
            if isinstance(appliesTo, list):
                self.__appliesTo = appliesTo # future compatibility
            else:
                self.__appliesTo = str(appliesTo).split(",")

            expiresAtStr = jsonRep.get("expiresAt")
            if expiresAtStr:
                self.__expiresAt = \
                    datetime.datetime.fromisoformat(expiresAtStr)

            grantsJson = jsonRep.get("grants")
            if isinstance(grantsJson, list):
                for grantJson in grantsJson:
                    self.__grants.append(AccessControlRuleClause(grantJson))

            exceptsJson = jsonRep.get("excepts")
            if isinstance(exceptsJson, list):
                for exceptJson in exceptsJson:
                    self.__excepts.append(AccessControlRuleClause(exceptJson))

    @property
    def appliesTo(self) -> list[str]:
        """The identities that this rule applies to.  A specific syntax
        is required for each identity.  E.g., "cwAuth{*}", "cwAuth{jsmith}",
        "cwAuth{%Analyst}", "oidConnect{mySub@https://myIssuer.com}",
        "oidConnect{https://myIssuer.com}", "ipAddress{20.76.201.171}",
        ipAddress{20.76.201}", "everybody"."""
        return self.__appliesTo

    # TODO: Hide the ugly string-encoded syntax for the different identity
    # types.  Perhaps we should tie the AuthUser and OidUser classes together
    # with an Identity base class, and add AuthRole, IpAddress and Everybody
    # classes.

    @property
    def expiresAt(self) -> datetime.datetime | None:
        """When this rule expires, or None for never.  After this date and
        time, the rule ceases to grant access."""
        return self.__expiresAt

    @expiresAt.setter
    def expiresAt(self, value: datetime.datetime | None):
        self.__expiresAt = value

    @property
    def grants(self) -> list[AccessControlRuleClause]:
        """The clauses that indicate what's being granted by this rule."""
        return self.__grants

    @property
    def excepts(self) -> list[AccessControlRuleClause]:
        """The clauses that indicate exceptions to what's being granted
        by this rule.  Note that these clauses do not revoke any access
        that may be granted by another rule."""
        return self.__excepts

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}
        jsonRep["appliesTo"] = ",".join(self.__appliesTo)
        if (self.__expiresAt):
            jsonRep["expiresAt"] = self.__expiresAt.isoformat()

        jsonRep["grants"] = grants = []
        for grantClause in self.__grants:
            grants.append(grantClause._jsonRep)

        if self.__excepts:
            jsonRep["excepts"] = excepts = []
            for exceptClause in self.__excepts:
                excepts.append(exceptClause._jsonRep)

        return jsonRep

    def __repr__(self):
        return repr(self._jsonRep)

##############################################################################

class AccessControlRuleClause:
    """A CubeWerx Access Control Rule Clause.

    There are two types of rule clauses: "grant" and "except".
    A "grant" clause specifies the operation classes that are being
    granted, and the content that is being granted for those operations.
    If no operation classes are specified, it means "all operations".
    Similarly, if no content is specified, it means "all content".

    An "except" clause specifies exceptions to what's being granted by
    the rule.  It does not cause the rule to revoke any access that may
    be granted by another rule.
    """

    def __init__(self, jsonRep: dict={}):
        """Create a new access control rule clause.

        Args:
            jsonRep: A dictionary supplying properties; do not specify;
                for internal use only.
        """
        self.__operationClasses = []
        self.__content = []

        if jsonRep:
            operationClassesJson = jsonRep.get("operationClasses")
            if isinstance(operationClassesJson, list) \
                    and "*" not in operationClassesJson:
                for operationClassStr in operationClassesJson:
                    operationClass = OperationClass(operationClassStr)
                    self.__operationClasses.append(operationClass)

            contentJson = jsonRep.get("content")
            if isinstance(contentJson, list):
                for contentRefJson in contentJson:
                    self.__content.append(ContentRef(None, contentRefJson))

    @property
    def operationClasses(self) -> list[OperationClass]:
        """The operation classes that are being granted (or excepted in
        the case of an "except" clause).  If empty, all operation classes
        are granted (or excepted)."""
        return self.__operationClasses

    @property
    def content(self) -> list[ContentRef]:
        """The content that's being granted (or excepted in the case
        of an "except" clause).  If empty, all content is granted (or
        excepted)."""
        return self.__content

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}

        if self.__operationClasses:
            jsonRep["operationClasses"] = operationClassesJson = []
            for operationClass in self.__operationClasses:
                operationClassesJson.append(str(operationClass))

        if self.__content:
            jsonRep["content"] = contentJson = []
            for contentRef in self.__content:
                contentJson.append(contentRef._jsonRep)

        return jsonRep

    def __repr__(self):
        return repr(self._jsonRep)

##############################################################################

class ApiKey:
    """An API key.

    To create a new API key, create a new `ApiKey` object (either
    specifying the desired key string or letting the server
    auto-generate one for you), set any other desired properties,
    and call Stratos.addOrReplaceApiKey().

    To change the details of an existing API key, fetch the `ApiKey`
    object via Stratos.getApiKeys() or Stratos.getApiKey(), update one
    or more properties of tha API key, and call Stratos.updateApiKey()
    object to commit those changes.

    To remove an API key, call Stratos.removeApiKey().
    """

    def __init__(self, key: str=None, dictionary: dict={}):
        """Create a new `ApiKey` object.

        Args:
            key: The desired API key string, or ""/None to let the server
                auto-generate one.
            dictionary: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        if key:
            if not "apiKey" in dictionary: dictionary["apiKey"] = key
        self._dict = dictionary

        # Keep track of the properties that are programmatically changed
        # so that an appropriate patch dictionary can be constructed.
        self.__descriptionChanged = False
        self.__contactChanged = False
        self.__expiresAtChanged = False
        self.__isEnabledChanged = False

    @property
    def key(self):
        """The API key string."""
        return self._dict.get("apiKey")

    @property
    def description(self) -> str | None:
        """A brief textual description of this API key, or None."""
        return self._dict.get("description")

    @description.setter
    def description(self, value: str | None):
        if value:
            self._dict["description"] = value
        else:
            self._dict.pop("description", None)
        self.__descriptionChanged = True

    @property
    def contactEmail(self) -> str | None:
        """The e-mail address to contact regarding this API key, or None."""
        return self._dict.get("contact")

    @contactEmail.setter
    def contactEmail(self, value: str | None):
        if value:
            if not validators.email(value):
                raise ValueError("Invalid emailAddress")
            self._dict["contact"] = value
        else:
            self._dict.pop("contact", None)
        self.__contactChanged = True

    @property
    def expiresAt(self) -> datetime.datetime | None:
        """The date and time (UTC) that this API key expires (after which
        time it's effectively disabled), or None if this API key never
        expires."""
        dateTimeStr = self._dict.get("expiresAt")
        return datetime.datetime.fromisoformat(dateTimeStr) \
            if dateTimeStr else None

    @expiresAt.setter
    def expiresAt(self, value: datetime.datetime | None):
        if value:
            self._dict["expiresAt"] = value.isoformat()
        else:
            self._dict.pop("expiresAt", None)
        self.__expiresAtChanged = True

    @property
    def isEnabled(self) -> bool:
        """Is this API key enabled (subject to `expiresAt`)?"""
        return self._dict.get("isEnabled", true)

    @isEnabled.setter
    def isEnabled(self, value: bool):
        self._dict["isEnabled"] = bool(value)
        self.__isEnabledChanged = True

    @property
    def _patchDict(self) -> dict:
        patch = {}
        if self.__descriptionChanged:
            patch["description"] = self.description
        if self.__contactChanged:
            patch["contact"] = self.contactEmail
        if self.__expiresAtChanged:
            patch["expiresAt"] = self._dict.get("expiresAt")
        if self.__isEnabledChanged:
            patch["isEnabled"] = self.isEnabled
        return patch

##############################################################################

class AreaSource:
    """A reference to a source of polygons, multi-surfaces and/or
    envelopes to be used for access control.
    """

    def __init__(self, urlOrFilePath: str | None = None,
                 format: str | None = None,
                 where: str = None):
        """Create a new area-source reference.

        Args:
            urlOrFilePath: A URL or local file path (absolute or relative
                to the server URL or directory) to the source, or None
                (but then required to be set via the property).
            format: The name of the convert-library driver that should be
                used to read this source (e.g., "GeoJSON", "shape"), or
                None.  If None, an attempt will be made to sniff the format.
            where: A CQL2 WHERE clause filter to select a subset of the
                geometries, or None to apply no filter.
        """
        self.__urlOrFilePath = urlOrFilePath if urlOrFilePath else None
        self.__format = format if format else None
        self.__where = where if where else None

    @staticmethod
    def _fromJsonRep(jsonRep: dict):
        return AreaSource(jsonRep.get("urlOrFilePath"),
            jsonRep.get("format"), jsonRep.get("where"))

    @property
    def urlOrFilePath(self) -> str | None:
        """A URL or local file path (absolute or relative to the
        server URL or directory) to the source, or None."""
        return self.__urlOrFilePath

    @urlOrFilePath.setter
    def urlOrFilePath(self, value: str | None):
        self.__urlOrFilePath = value if value else None

    @property
    def format(self) -> str | None:
        """The name of the convert-library driver that should be used to
        read this source (e.g., "GeoJSON", "shape"), or None.  If None,
        an attempt will be made to sniff the format."""
        return self.__format

    @format.setter
    def format(self, value: str | None):
        self.__format = value if value else None

    @property
    def where(self) -> str | None:
        """A CQL2 WHERE clause filter to select a subset of the
        geometries, or None to apply no filter."""
        return self.__where

    @where.setter
    def where(self, value: str | None):
        self.__where = value if value else None

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}
        if self.__urlOrFilePath:
            jsonRep["urlOrFilePath"] = self.__urlOrFilePath
        if self.__format:
            jsonRep["format"] = self.__format
        if self.__where:
            jsonRep["where"] = self.__where
        return jsonRep

    def __repr__(self):
        return repr(self._jsonRep)

##############################################################################

class AuthUser:
    """A CubeWerx Stratos CwAuth user account.

    To create a new CubeWerx Stratos CwAuth user, create a new `AuthUser`
    object (specifying the desired username), set the required e-mail
    address and password for the user, set any other desired properties,
    and call Stratos.ddOrReplaceAuthUser().

    To change the details of an existing CubeWerx Stratos CwAuth user
    account, fetch the `AuthUser` object via the Stratos.getAuthUsers()
    or Stratos.getAuthUser(), update one or more properties of that user,
    and call Stratos.updateAuthUser() to commit those changes.

    To remove a CubeWerx Stratos CwAuth user account, call
    Stratos.removeAuthUser().
    """

    def __init__(self, username: str=None, dictionary: dict={}):
        """Create a new `AuthUser` object.

        Args:
            username: The user's username.  Each CubeWerx Stratos CwAuth
                user account must have a unique username.  Required unless
                supplied via the dictionary parameter.
            dictionary: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        print(dictionary)
        if username:
            if not "username" in dictionary: dictionary["username"] = username
        elif not "username" in dictionary:
            raise Exception("username needs to be specified")
        self._dict = dictionary

        # Keep track of the properties that are programmatically changed
        # so that an appropriate patch dictionary can be constructed.
        self.__firstNameChanged = False
        self.__lastNameChanged = False
        self.__emailAddressChanged = False
        self.__rolesChanged = False
        self.__maxSeatsChanged = False
        self.__isEditableChanged = False
        self.__isEnabledChanged = False

    @property
    def username(self):
        """The unique username of this CubeWerx Stratos CwAuth user
        account."""
        return self._dict.get("username")

    @property
    def firstName(self) -> str | None:
        """The first (given) name of this CubeWerx Stratos CwAuth user
        account (possibly also with middle name(s) and/or initial(s)),
        or None."""
        return self._dict.get("firstName")

    @firstName.setter
    def firstName(self, value: str | None):
        if value:
            self._dict["firstName"] = str(value)
        else:
            self._dict.pop("firstName", None)
        self.__firstNameChanged = True

    @property
    def lastName(self) -> str | None:
        """The last (family) name (i.e., surname) of this CubeWerx
        Stratos CwAuth user account, or None."""
        return self._dict.get("lastName")

    @lastName.setter
    def lastName(self, value: str | None):
        if value:
            self._dict["lastName"] = str(value)
        else:
            self._dict.pop("lastName", None)
        self.__lastNameChanged = True

    @property
    def displayName(self) -> str:
        """An appropriate name to display for this CubeWerx Stratos
        CwAuth user account, either the user's first and/or last name
        if set, or the user's username otherwise."""
        displayName = ""
        firstName = self.firstName
        lastName = self.lastName
        if firstName: displayName += firstName
        if firstName and lastName: displayName += " "
        if lastName: displayName += lastName
        if not displayName: displayName = self.username
        return displayName

    @property
    def emailAddress(self) -> str | None:
        """The e-mail address of this CubeWerx Stratos CwAuth user
        account, or None."""
        return self._dict.get("emailAddress")

    @emailAddress.setter
    def emailAddress(self, value: str):
        if not validators.email(str(value)):
            raise ValueError("Invalid emailAddress")
        self._dict["emailAddress"] = str(value)
        self.__emailAddressChanged = True

    @property
    def roles(self) -> list[str]:
        """The list of roles that this CubeWerx Stratos CwAuth user
        account has.  These are the role names only.  To get the full
        `Role` objects (for descriptions, etc.), pass this list to
        Stratos.getRoles().  This list of roles can be re-specified with
        a user.roles = [...] assignment.  However, to add or remove a
        role to/from the existing list, use AuthUser.addRole() or
        AuthUser.removeRole() rather than user.roles.append() or
        user.roles.remove()."""
        return self._dict.get("roles", [])

    @roles.setter
    def roles(self, value: list[str]):
        self._dict["roles"] = value if value else []
        self.__rolesChanged = True

    def addRole(self, roleName: str):
        """Add a role to this CubeWerx Stratos CwAuth user account.

        Args:
            roleName: The name of the role to add to this CubeWerx
                Stratos CwAuth user account.  The specified role must
                exist.  If the user already has this role, this is a
                no-op.
        """
        if roleName:
            if not self._dict.get("roles"): self._dict["roles"] = []
            if not roleName in self._dict["roles"]:
                self._dict["roles"].append(roleName)
            self.__rolesChanged = True

    def removeRole(self, roleName: str):
        """Remove a role from this CubeWerx Stratos CwAuth user account.

        Args:
            roleName: The name of the role to remove (revoke) from this
                CubeWerx Stratos CwAuth user account.  If the user
                doesn't have this role, this is a no-op.
        """
        if (self._dict["roles"] and roleName and
                roleName in self._dict["roles"]):
            self._dict["roles"].remove(roleName)
            self.__rolesChanged = True

    @property
    def maxSeats(self) -> int | None:
        """The maximum number of times this CubeWerx Stratos CwAuth user
        account can be logged in, or None."""
        return self._dict.get("maxSeats")

    @maxSeats.setter
    def maxSeats(self, value: int | None):
        if value is not None and int(value) >= 0:
            self._dict["maxSeats"] = int(value)
        else:
            self._dict.pop("maxSeats", None)
        self.__maxSeatsChanged = True

    @property
    def isEditable(self) -> bool:
        """Is this CubeWerx Stratos CwAuth user allowed to edit their
        own information?"""
        return self._dict.get("isEditable", True)

    @isEditable.setter
    def isEditable(self, value: bool):
        self._dict["isEditable"] = bool(value)
        self.__isEditableChanged = True

    @property
    def isEnabled(self) -> bool:
        """Is this CubeWerx Stratos CwAuth user account enabled (i.e.,
        can users sign in with this account)?"""
        return self._dict.get("isEnabled", True)

    @isEnabled.setter
    def isEnabled(self, value: bool):
        self._dict["isEnabled"] = bool(value)
        self.__isEnabledChanged = True

    @property
    def password(self) -> str | None:
        """The password for this CubeWerx Stratos CwAuth user account,
        or None.  Note that none of the user information returned by
        Stratos.getAuthUsers() or Stratos.getAuthUser() will include
        a password.  However, a password must be set when calling
        Stratos.addOrReplaceAuthUser()."""
        return self._dict.get("password")

    @password.setter
    def password(self, value: str):
        self._dict["password"] = str(value) if str(value) else ""

    @property
    def _patchDict(self) -> dict:
        patch = {}
        if self.__firstNameChanged:
            patch["firstName"] = self.firstName
        if self.__lastNameChanged:
            patch["lastName"] = self.lastName
        if self.__emailAddressChanged:
            patch["emailAddress"] = self.emailAddress
        if self.__rolesChanged:
            patch["roles"] = self.roles
        if self.__maxSeatsChanged:
            patch["maxSeats"] = self.maxSeats
        if self.__isEditableChanged:
            patch["isEditable"] = self.isEditable
        if self.__isEnabledChanged:
            patch["isEnabled"] = self.isEnabled
        return patch

##############################################################################

class ConfigParam:
    """The details of a CubeWerx Stratos configuration parameter.
    """

    def __init__(self, jsonRep: dict, configUrl: str, stratos: Stratos):
        """@private"""
        self.__initFromJsonRep(jsonRep)
        self.__configParamUrl = configUrl + "/" + self.__name
        self.__stratos = stratos

    def __initFromJsonRep(self, jsonRep: dict):
        self.__name = jsonRep.get("name")
        self.__description = jsonRep.get("description")
        self.__type = ConfigParamType._parse(jsonRep.get("type", "String"))
        self.__range = jsonRep.get("range")
        self.__isGlobal = jsonRep.get("isGlobal", False)
        self.__defaultValueStr = jsonRep.get("defaultValueStr")
        self.__explicitValueStr = jsonRep.get("explicitValueStr")

        if "defaultValue" in jsonRep.keys():
            rawDefaultVal = jsonRep.get("defaultValue")
            if self.__type == ConfigParamType.NUMBER:
                self.__defaultValue = \
                    math.inf if rawDefaultVal is None else rawDefaultVal
            elif self.__type == ConfigParamType.MULTILINGUAL_STRING:
                self.__defaultValue = MultilingualString(rawDefaultVal)
            else:
                self.__defaultValue = rawDefaultVal
        else:
            self.__defaultValue = None

        if "explicitValue" in jsonRep.keys():
            rawExplicitVal = jsonRep.get("explicitValue")
            if self.__type == ConfigParamType.NUMBER:
                self.__explicitValue = \
                    math.inf if rawExplicitVal is None else rawExplicitVal
            elif self.__type == ConfigParamType.MULTILINGUAL_STRING:
                self.__explicitValue = MultilingualString(rawExplicitVal)
            else:
                self.__explicitValue = rawExplicitVal
        else:
            self.__explicitValue = None

    @property
    def name(self) -> str:
        """The name of this configuration parameter."""
        return self.__name

    @property
    def description(self) -> str | None:
        """A description of this configuration parameter, or None."""
        return self.__description

    @property
    def type(self) -> ConfigParamType:
        """The type of this configuration parameter."""
        return self.__type

    @property
    def range(self) -> list[str]:
        """The list of allowed case-insensitive values of this configuration
        parameter if of type ENUMERATED, or None otherwise."""
        return self.__range

    @property
    def isGlobal(self) -> bool:
        """Whether or not this is a global configuration parameter that
        affects all deployments."""
        return self.__isGlobal

    @property
    def defaultValueStr(self) -> str:
        """The string representation of the default value of this
        configuration parameter."""
        return self.__defaultValueStr

    @property
    def defaultValue(self):
        """The default value of this configuration parameter, expressed as
        the appropriate Python type according to the following table:

            Config Param Type    Python type
            -----------------    -----------
            BOOLEAN              bool
            NUMBER               float (can be math.inf)
            STRING               str
            PASSWORD             str
            PERCENTAGE           float (0..100)
            URL                  str
            DURATION             float (in seconds)
            ENUMERATED           str
            MULTILINGUAL_STRING  cubewerx.stratos.MultilingualString
            STRING_LIST          list[str]
            STRING_MAP           dict[str,str]
            JSON                 bool|int|float|str|list|dict
        """
        return self.__defaultValue

    @property
    def explicitValueStr(self) -> str | None:
        """The string representation of the value that's explicitly set
        for this configuration parameter, or None if the default value
        is active.  Setting this (or clearing it by setting it to None)
        will automatically update the server."""
        return self.__explicitValueStr

    @explicitValueStr.setter
    def explicitValueStr(self, valueStr: str):
        paramUrl = self.__configParamUrl
        if valueStr is None:
            requestHeaders = self.__stratos.commonRequestHeaders
            response = requests.delete(paramUrl, headers=requestHeaders)
            ServerException.raise_for_status(response)
            self.__explicitValue = None
            self.__explicitValueStr = None
        else:
            requestHeaders = {
                "Content-Type": "text/plain; charset=utf-8",
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.put(paramUrl, headers=requestHeaders,
                data=str(valueStr).encode('utf-8'))
            ServerException.raise_for_status(response)
            responseJson = response.json()
            self.__initFromJsonRep(response.json())

    @property
    def explicitValue(self):
        """The value that's explicitly set for this configuration
        parameter, expressed as the appropriate Python type, or None if
        the default value is active.  Setting this (or clearing it by
        setting it to None) will automatically update the server.

            Config Param Type    Python type
            -----------------    -----------
            BOOLEAN              bool
            NUMBER               float (can be math.inf)
            STRING               str
            PASSWORD             str
            PERCENTAGE           float (0..100)
            URL                  str
            DURATION             float (in seconds)
            ENUMERATED           str
            MULTILINGUAL_STRING  cubewerx.stratos.MultilingualString
            STRING_LIST          list[str]
            STRING_MAP           dict[str,str]
            JSON                 bool|int|float|str|list|dict
        """
        return self.__explicitValue

    @explicitValue.setter
    def explicitValue(self, value):
        paramUrl = self.__configParamUrl
        if value is None:
            requestHeaders = self.__stratos.commonRequestHeaders
            response = requests.delete(paramUrl, headers=requestHeaders)
            ServerException.raise_for_status(response)
            self.__explicitValue = None
            self.__explicitValueStr = None
        else:
            # Convert the value to the appropriate JSON type if necessary.
            try:
                if self.__type == ConfigParamType.BOOLEAN:
                    jsonRep = bool(value)
                elif self.__type == ConfigParamType.NUMBER:
                    jsonRep = float(value)
                    if (math.isinf(jsonRep)): jsonRep = None
                elif self.__type == ConfigParamType.STRING:
                    jsonRep = str(value)
                elif self.__type == ConfigParamType.PASSWORD:
                    jsonRep = str(value)
                elif self.__type == ConfigParamType.PERCENTAGE:
                    jsonRep = max(min(float(value), 100), 0)
                elif self.__type == ConfigParamType.URL:
                    jsonRep = str(value)
                elif self.__type == ConfigParamType.DURATION:
                    jsonRep = max(float(value), 0)
                elif self.__type == ConfigParamType.ENUMERATED:
                    jsonRep = str(value)
                elif self.__type == ConfigParamType.MULTILINGUAL_STRING:
                    jsonRep = value._jsonRep
                elif self.__type == ConfigParamType.STRING_LIST:
                    jsonRep = []
                    for strVal in value:
                        jsonRep.append(str(strVal))
                elif self.__type == ConfigParamType.STRING_MAP:
                    jsonRep = {}
                    for key, value in dict(value).items():
                        jsonRep[str(key)] = str(value)
                else:
                    jsonRep = value
            except TypeError as e:
                raise TypeError("type of value must be compatible with " +
                    "configuration parameter type")

            requestHeaders = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.put(paramUrl, headers=requestHeaders,
                json=jsonRep)
            ServerException.raise_for_status(response)
            responseJson = response.json()
            self.__initFromJsonRep(response.json())

##############################################################################

class ConfigParamType(enum.StrEnum):
    """An enumeration of the configuration parameter types.
    """

    BOOLEAN             = "Boolean"
    NUMBER              = "Number"
    STRING              = "String"
    PASSWORD            = "Password"
    PERCENTAGE          = "Percentage"
    URL                 = "URL"
    DURATION            = "Duration"
    ENUMERATED          = "Enumerated"
    MULTILINGUAL_STRING = "MultilingualString"
    STRING_LIST         = "StringList"
    STRING_MAP          = "StringMap"
    JSON                = "JSON"

    # ugly hack to handle case insensitive parsing from server
    @staticmethod
    def _parse(typeStr: str):
        lowerTypeStr = typeStr.lower()
        if lowerTypeStr == "boolean":
            return ConfigParamType.BOOLEAN
        elif lowerTypeStr == "number":
            return ConfigParamType.NUMBER
        elif lowerTypeStr == "string":
            return ConfigParamType.STRING
        elif lowerTypeStr == "password":
            return ConfigParamType.PASSWORD
        elif lowerTypeStr == "percentage":
            return ConfigParamType.PERCENTAGE
        elif lowerTypeStr == "url":
            return ConfigParamType.URL
        elif lowerTypeStr == "duration":
            return ConfigParamType.DURATION
        elif lowerTypeStr == "multilingualstring":
            return ConfigParamType.MULTILINGUAL_STRING
        elif lowerTypeStr == "stringlist":
            return ConfigParamType.STRING_LIST
        elif lowerTypeStr == "stringmap":
            return ConfigParamType.STRING_MAP
        elif lowerTypeStr == "json":
            return ConfigParamType.JSON
        else:
            return ConfigParamType.STRING

##############################################################################

class ContentRef:
    """The content that's being granted (or excepted in the case of
    an "except" clause).

    Within a "grant" clause, content is all-inclusive by default.  That
    is, if no spatial area is specified, it means "everywhere", if no
    feature filters are specified, it means "all features", and if no
    property names are specified, it means "all properties".  Within an
    "except" clause, however, content is all-inclusive by default only
    if it's empty (other than the required "name" property).  Otherwise
    it only includes (excepts) the mentioned thing(s).
    """

    def __init__(self, name: str=None, jsonRep: dict={}):
        """Create a new content reference.

        Args:
            name: The name/ID of the feature set, layer or process that's
                being granted (or excepted in the case of an "except"
                clause), or "*" for all.  Required unless supplied via the
                jsonRep parameter.
            jsonRep: a dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        self.__name = jsonRep.get("name")
        if not self.__name:
            self.__name = name
        if not self.__name:
            raise Exception("name needs to be specified")

        self.__areas = []
        self.__minScaleDenominator = None
        self.__finestResolution = None
        self.__where = None
        self.__properties = []
        self.__watermark = None

        if jsonRep:
            areasJson = jsonRep.get("areas")
            if isinstance(areasJson, list):
                for areaJson in areasJson:
                    if "urlOrFilePath" in areaJson:
                        self.__areas.append(AreaSource._fromJsonRep(areaJson))
                    else:
                        polygon = geojson.Polygon(**areaJson)
                        self.__areas.append(polygon)

            minScaleDenominator = jsonRep.get("minScaleDenominator")
            if minScaleDenominator:
                self.__minScaleDenominator = minScaleDenominator

            finestResolution = jsonRep.get("finestResolution")
            if finestResolution:
                self.__finestResolution = finestResolution

            where = jsonRep.get("where")
            if where:
                self.__where = where

            propertiesJson = jsonRep.get("properties")
            if isinstance(propertiesJson, list):
                for propertyJson in propertiesJson:
                  self.__properties.append(str(propertyJson))

            watermarkJson = jsonRep.get("watermark")
            if watermarkJson:
                self.__watermark = Watermark._fromJsonRep(watermarkJson)

    @property
    def name(self) -> str:
        """The name/ID of the feature set, layer or process that's
        being granted (or excepted in the case of an "except" clause),
        or "*" for all."""
        return self.__name

    @name.setter
    def name(self, value: str):
        self.__name = str(value) if value else "*"

    @property
    def areas(self) -> list[geojson.Polygon|AreaSource]:
        """The spatial areas that are being granted (or excepted in the
        case of an \"except\" clause)."""
        return self.__areas

    @property
    def minScaleDenominator(self) -> float | None:
        """The level of detail to grant access to, expressed as a
        minimum scale denominator (e.g., a minimum scale denominator of
        100000 indicates that no detail finer than a scale of 1/100000
        should be granted), or None to not limit level of detail in this
        way.  The lower the specified number, the more detail is granted.
        This is mutually exclusive with the `finestResolution` property.
        I.e., setting this property, even to None, automatically sets the
        `finestResolution` property to None."""
        return self.__minScaleDenominator

    @minScaleDenominator.setter
    def minScaleDenominator(self, value: float | None):
        if value is not None and value <= 0:
            raise ValueError("minScaleDenominator must be a positive number")
        self.__minScaleDenominator = float(value) if value else None
        self.__finestResolution = None

    @property
    def finestResolution(self) -> dict | None:
        """The level of detail to grant access to, expressed as a
        dictionary with a "resolution" field indicating a resolution
        (i.e., units per pixel) and a "crs" field indicating the
        coordinate reference system that the resolution should be
        interpreted with respect to (e.g., { "resolution": 10000, "crs":
        "EPSG:3857" }), or None to not limit level of detail in this
        way.  The lower the specified number, the more detail is granted.
        This is mutually exclusive with the `minScaleDenominator` property
        I.e., setting this property, even to None, automatically sets the
        `minScaleDenominator` property to None."""
        return self.__finestResolution

    @finestResolution.setter
    def finestResolution(self, value: dict | None):
        if value:
            if not isinstance(value, dict):
                raise TypeError("dict or None expected")
            if not "resolution" in value:
                raise ValueError("missing required 'resolution' field")
            resolution = float(value["resolution"])
            if resolution < 0:
                raise ValueError("resolution must be a non-negative number")
            if not "crs" in value:
                raise ValueError("missing required 'crs' field")
            crs = str(value["crs"])
            if not crs:
                raise ValueError("missing 'crs' value")
            self.__finestResolution = { "resolution": resolution, "crs": crs }
        else:
            self.__finestResolution = None
        self.__minScaleDenominator = None

    @property
    def where(self) -> str | None:
        """A CQL2 WHERE clause filter that limits feature-set content
        to only those features that pass through the filter, or None
        to apply no filter."""
        return self.__where

    @where.setter
    def where(self, value: str | None):
        self.__where = str(value) if value else None

    @property
    def properties(self) -> list[str]:
        """The set of feature-set properties to grant access to (or
        except in the case of an "except" clause).  If no properties
        are specified, it means "all properties"."""
        return self.__properties

    @property
    def watermark(self) -> Watermark | None:
        """A watermark to apply for map layer rendering, or None."""
        return self.__watermark

    @watermark.setter
    def watermark(self, value: Watermark | None):
        self.__watermark = value

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}

        jsonRep["name"] = self.__name

        if self.__areas:
            jsonRep["areas"] = areasJson = []
            for area in self.__areas:
                if isinstance(area, AreaSource):
                    if area.urlOrFilePath:
                        areasJson.append(area._jsonRep)
                else:
                    geoJsonStr = geojson.dumps(area)
                    areasJson.append(json.loads(geoJsonStr))

        if self.__minScaleDenominator:
            jsonRep["minScaleDenominator"] = self.__minScaleDenominator

        if self.__finestResolution:
            jsonRep["finestResolution"] = self.__finestResolution

        if self.__where:
            jsonRep["where"] = self.__where

        if self.__properties:
            jsonRep["properties"] = self.__properties

        if self.__watermark:
            jsonRep["watermark"] = self.__watermark._jsonRep

        return jsonRep

    def __repr__(self):
        return repr(self._jsonRep)

##############################################################################

class Credentials:
    """The credentials of the CubeWerx Stratos administration user
    that we're logged in as.
    """

    def __init__(self, dictionary: dict):
        """@private"""
        self._dict = dictionary

    @property
    def username(self):
        """The unique username of this CubeWerx Stratos CwAuth user
        account."""
        return self._dict.get("authUsername")

    @property
    def firstName(self) -> str | None:
        """The first name of this CubeWerx Stratos CwAuth user account
        (possibly also with middle name(s) and/or initial(s)), or None."""
        return self._dict.get("firstName")

    @property
    def lastName(self) -> str | None:
        """The last name of this CubeWerx Stratos CwAuth user account,
        or None."""
        return self._dict.get("lastName")

    @property
    def displayName(self) -> str:
        """An appropriate name to display for this CubeWerx Stratos
        CwAuth user account, either the user's first and/or last name
        if set, or the user's username otherwise."""
        displayName = ""
        firstName = self.firstName
        lastName = self.lastName
        if firstName: displayName += firstName
        if firstName and lastName: displayName += " "
        if lastName: displayName += lastName
        if not displayName: displayName = self.username
        return displayName

    @property
    def emailAddress(self) -> str | None:
        """The e-mail address of this CubeWerx Stratos CwAuth user
        account, or None."""
        return self._dict.get("emailAddress")

    @property
    def roles(self) -> list[str]:
        """The list of roles that this CubeWerx Stratos CwAuth user
        account has.  These are the role names only.  To get the full
        `Role` objects (for descriptions, etc.), pass this list to
        Stratos.getRoles()."""
        return self._dict.get("roles", [])

##############################################################################

class CubeSTOR:
    """The details of a CubeSTOR database.

    Do not instantiate directly.  To get a list of CubeSTOR
    database details or the details of a specific CubeSTOR
    database, call Stratos.getCubeSTORs() or Stratos.getCubeSTOR()
    respectively.  To create, update or remove a CubeSTOR database,
    call Stratos.addCubeSTOR(), Stratos.updateCubeSTOR() or
    Stratos.removeCubeSTOR() respectively.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__dbName = jsonRep.get("dbName")

        title = jsonRep.get("title")
        self.__title = str(title) if title else None

        description = jsonRep.get("description")
        self.__description = str(description) if description else None

        nFeatureSets = jsonRep.get("nFeatureSets")
        self.__nFeatureSets = int(nFeatureSets) if nFeatureSets else 0

        dataStoreName = jsonRep.get("dataStoreName")
        self.__dataStoreName = str(dataStoreName) if dataStoreName else None

        self.__canDelete = bool(jsonRep.get("canDelete", False))

    @property
    def dbName(self) -> str:
        """The name of this CubeSTOR database."""
        return self.__dbName

    @property
    def title(self) -> str | None:
        """The title of this CubeSTOR database, or None."""
        return self.__title

    @property
    def description(self) -> str | None:
        """A brief textual description of this CubeSTOR database, or
        None."""
        return self.__description

    @property
    def nFeatureSets(self) -> int:
        """The number of feature sets that are in this CubeSTOR database."""
        return self.__nFeatureSets

    @property
    def dataStoreName(self) -> str | None:
        """The name of the data store that this CubeSTOR database is the
        source of, or None if this CubeSTOR database is not the source of
        any data store."""
        return self.__dataStoreName

    @property
    def canDelete(self) -> bool:
        """Whether or not this CubeSTOR database can currently be
        removed through this API."""
        return self.__canDelete

##############################################################################

class DataStore:
    """A CubeWerx Stratos data store.

    To create a new CubeWerx Stratos data store, create a new `DataStore`
    object (specifying the desired name), set the required data store
    type and source properties, set any other desired properties,
    and call Stratos.addOrReplaceDataStore().

    To change the details of an existing CubeWerx Stratos data store,
    fetch the `DataStore` object via Stratos.getDataStores() or
    Stratos.getDataStore(), update one or more properties of that data
    store, and call Stratos.updateDataStore() to commit those changes.
    Layer manipulation is an exception; any changes to the layers of
    a data store are updated on the server immediately.

    To remove a CubeWerx Stratos data store, call Stratos.removeDataStore().
    """

    def __init__(self, name: str=None, jsonRep: dict={}):
        """Create a new `DataStore` object.

        Args:
            name: The desired name of the data store.  Each data store must
                have a unique name.  The name must be no longer than 64
                characters, must not contain a colon, and must not be one
                of the two reserved values "processing" or "catalogues".
                Required unless supplied via the jsonRep parameter.
            jsonRep: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        self.__name = jsonRep.get("name")
        if not self.__name:
            if len(name) > 64 or ":" in name or name in ["processing", "catalogues"]:
                raise Exception("invalid name")
            self.__name = name
        if not self.__name:
            raise Exception("name needs to be specified")

        # For each changeable property, grab a copy of the string
        # representation of the original value so that we can compare
        # later to see if it has changed (in order to construct a proper
        # PATCH dictionary).

        typeJson = jsonRep.get("type")
        self.__type = str(typeJson) if typeJson else None
        self.__typeOrigRep = repr(self.__type)

        sourceJson = jsonRep.get("source")
        self.__source = str(sourceJson) if sourceJson else None
        self.__sourceOrigRep = repr(self.__source)

        titleJson = jsonRep.get("title")
        self.__title = MultilingualString(titleJson) if titleJson else None
        self.__titleOrigRep = repr(self.__title)

        descriptionJson = jsonRep.get("description")
        self.__description = MultilingualString(descriptionJson) \
            if descriptionJson else None
        self.__descriptionOrigRep = repr(self.__description)

        attributionTitleJson = jsonRep.get("attributionTitle")
        self.__attributionTitle = MultilingualString(attributionTitleJson) \
            if attributionTitleJson else None
        self.__attributionTitleOrigRep = repr(self.__attributionTitle)

        attributionUrlJson = jsonRep.get("attributionUrl")
        self.__attributionUrl = str(attributionUrlJson) \
            if attributionUrlJson else None
        self.__attributionUrlOrigRep = repr(self.__attributionUrl)

        attributionHtmlJson = jsonRep.get("attributionHtml")
        self.__attributionHtml = MultilingualString(attributionHtmlJson) \
            if attributionHtmlJson else None
        self.__attributionHtmlOrigRep = repr(self.__attributionHtml)

        attributionLogoUrlJson = jsonRep.get("attributionLogoUrl")
        self.__attributionLogoUrl = str(attributionLogoUrlJson) \
            if attributionLogoUrlJson else None
        self.__attributionLogoUrlOrigRep = repr(self.__attributionLogoUrl)

        licenseTitleJson = jsonRep.get("licenseTitle")
        self.__licenseTitle = MultilingualString(licenseTitleJson) \
            if licenseTitleJson else None
        self.__licenseTitleOrigRep = repr(self.__licenseTitle)

        licenseUrlJson = jsonRep.get("licenseUrl")
        self.__licenseUrl = str(licenseUrlJson) if licenseUrlJson else None
        self.__licenseUrlOrigRep = repr(self.__licenseUrl)

        licenseHtmlJson = jsonRep.get("licenseHtml")
        self.__licenseHtml = MultilingualString(licenseHtmlJson) \
            if licenseHtmlJson else None
        self.__licenseHtmlOrigRep = repr(self.__licenseHtml)

        isExternalServiceJson = jsonRep.get("isExternalService", False)
        self.__isExternalService = bool(isExternalServiceJson)
        self.__isExternalServiceOrigRep = repr(self.__isExternalService)

        omitDataStoreThemeJson = jsonRep.get("omitDataStoreTheme", False)
        self.__omitDataStoreTheme = bool(omitDataStoreThemeJson)
        self.__omitDataStoreThemeOrigRep = repr(self.__omitDataStoreTheme)

        stylesUrlJson = jsonRep.get("stylesUrl")
        self.__stylesUrl = str(stylesUrlJson) if stylesUrlJson else None
        self.__stylesUrlOrigRep = repr(self.__stylesUrl)

        extraStylesUrlJson = jsonRep.get("extraStylesUrl")
        self.__extraStylesUrl = str(extraStylesUrlJson) \
            if extraStylesUrlJson else None
        self.__extraStylesUrlOrigRep = repr(self.__extraStylesUrl)

        provideSpectralIndexStylesJson = \
            jsonRep.get("provideSpectralIndexStyles")
        self.__provideSpectralIndexStyles = \
            bool(provideSpectralIndexStylesJson)
        self.__provideSpectralIndexStylesOrigRep = \
            repr(self.__provideSpectralIndexStyles)

        simulateTilesJson = jsonRep.get("simulateTiles")
        self.__simulateTiles = simulateTilesJson \
            if isinstance(simulateTilesJson, list) else []
        self.__simulateTilesOrigRep = repr(self.__simulateTiles)

        hintsJson = jsonRep.get("hints")
        self.__hints = hintsJson if isinstance(hintsJson, dict) else {}
        self.__hintsOrigRep = repr(self.__hints)

        accessControlRulesJson = jsonRep.get("accessControlRules")
        self.__accessControlRules = []
        if isinstance(accessControlRulesJson, list):
            for acrJson in accessControlRulesJson:
                self.__accessControlRules.append(AccessControlRule(acrJson))
        self.__accessControlRulesOrigRep = repr(self.__accessControlRules)

        # will be set later by _setServerAssociation
        self.__stratos = None
        self.__dataStoreAdminUrl = None
        self.__ogcApiLandingPageUrl = None

        self.__layerCache = None

    @property
    def name(self) -> str:
        """The unique name/ID of this CubeWerx Stratos data store."""
        return self.__name

    @property
    def type(self) -> str | None:
        """The type of data store (i.e., the type of its source).  Valid
        values are "cubestor" (for a CubeSTOR database), "oradb" (for a
        CubeWerx OraDB database), "ogcapi" (for an OGC API Service),
        "wms" (for an OGC Web Map Service), "wmts" (for an OGC Web Map
        Tile Service), "wfs" (for an OGC Web Map Feature Service),
        "arcgismap" for an ESRI® ArcGIS® Map service, and "GeoJSON" (for
        a GeoJSON source."""
        return self.__type

    @type.setter
    def type(self, value: str | None):
        self.__type = str(value) if value else None

    @property
    def source(self) -> str | None:
        """The name (for data stores of type "cubestor"), connect string
        (for data stores of type "oradb") or URL (for all other data
        store types) of the source of the data store.  For data stores
        of type "cubestor", it's recommended that the GUI admin client
        fetch the list of available CubeSTORs via a call to
        Stratos.getCubeSTORs() and present them in a drop-down list."""
        return self.__source

    @source.setter
    def source(self, value: str | None):
        self.__source = str(value) if value else None

    @property
    def title(self) -> MultilingualString | None:
        """The title of this data store, or None.  If None, the title of
        the source is used."""
        return self.__title

    @title.setter
    def title(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__title = value
            else:
                self.__title = MultilingualString(value)
        else:
            self.__title = None

    @property
    def description(self) -> MultilingualString | None:
        """A brief textual description of this data store, or None.
        If None, the description of the source is used."""
        return self.__description

    @description.setter
    def description(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__description = value
            else:
                self.__description = MultilingualString(value)
        else:
            self.__description = None

    @property
    def attributionTitle(self) -> MultilingualString | None:
        """A human-readable attribution for this data store, or None."""
        return self.__attributionTitle

    @attributionTitle.setter
    def attributionTitle(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__attributionTitle = value
            else:
                self.__attributionTitle = MultilingualString(value)
        else:
            self.__attributionTitle = None

    @property
    def attributionUrl(self) -> str | None:
        """A URL to link to for the attribution of this data store, or
        None."""
        return self.__attributionUrl

    @attributionUrl.setter
    def attributionUrl(self, value: str | None):
        self.__attributionUrl = str(value) if value else None

    @property
    def attributionHtml(self) -> MultilingualString | None:
        """A human-readable attribution (with HTML markup) for this
        data store, or None; overrides both attributionTitle and
        attributionUrl."""
        return self.__attributionHtml

    @attributionHtml.setter
    def attributionHtml(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__attributionHtml = value
            else:
                self.__attributionHtml = MultilingualString(value)
        else:
            self.__attributionHtml = None

    @property
    def attributionLogoUrl(self) -> str | None:
        """A URL of a logo to display for the attribution of this data
        store, or None."""
        return self.__attributionLogoUrl

    @attributionLogoUrl.setter
    def attributionLogoUrl(self, value: str | None):
        self.__attributionLogoUrl = str(value) if value else None

    @property
    def licenseTitle(self) -> MultilingualString | None:
        """Human-readable text describing how this data store is
        licensed, or None."""
        return self.__licenseTitle

    @licenseTitle.setter
    def licenseTitle(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__licenseTitle = value
            else:
                self.__licenseTitle = MultilingualString(value)
        else:
            self.__licenseTitle = None

    @property
    def licenseUrl(self) -> str | None:
        """A URL to link to for the license of this data store, or None."""
        return self.__licenseUrl

    @licenseUrl.setter
    def licenseUrl(self, value: str | None):
        self.__licenseUrl = str(value) if value else None

    @property
    def licenseHtml(self) -> MultilingualString | None:
        """Human-readable text (with HTML markup) describing how this
        data store is licensed, or None.  Overrides both licenseTitle and
        licenseUrl."""
        return self.__licenseHtml

    @licenseHtml.setter
    def licenseHtml(self, value: MultilingualString | str | None):
        if value:
            if isinstance(value, MultilingualString):
                self.__licenseHtml = value
            else:
                self.__licenseHtml = MultilingualString(value)
        else:
            self.__licenseHtml = None

    @property
    def isExternalService(self) -> bool:
        """Whether or not the source of this data store is an external
        service that CubeWerx Stratos clients can access directly.  If
        True, the Stratos Geospatial Data Server may redirect certain
        client requests directly to the source server for more efficient
        operation."""
        return self.__isExternalService

    @isExternalService.setter
    def isExternalService(self, value: bool):
        self.__isExternalService = bool(value)

    @property
    def omitDataStoreTheme(self) -> bool:
        """The CubeWerx Stratos WMS and WMTS web services are
        capable of combining multiple data stores into a single set
        of offerings, and furthermore are capable of providing their
        the list of available layers as a hierarchical set of themes.
        Normally each data store served by such a web service is given
        its own top-level theme.  Setting this to True will disable this
        behavour for this data store, putting the offerings of this data
        store (which may themselves be organized by a theme hierarchy)
        directly as top-level items."""
        return self.__omitDataStoreTheme

    @omitDataStoreTheme.setter
    def omitDataStoreTheme(self, value: bool):
        self.__omitDataStoreTheme = bool(value)

    @property
    def stylesUrl(self) -> str | None:
        """A URL to a Styled-Layer Descriptor (SLD) document providing
        a set of styles for (and therefore defining the layers of) the
        coverages and/or feature sets provided by the source of this
        data store.  Not necessary if the data store source provides
        its own layers and styles."""
        return self.__stylesUrl

    @stylesUrl.setter
    def stylesUrl(self, value: str | None):
        self.__stylesUrl = str(value) if value else None

    @property
    def extraStylesUrl(self) -> str | None:
        """A URL to a Styled-Layer Descriptor (SLD) document providing
        an additional set of styles for the coverages and/or feature sets
        provided by the source of this data store, augmenting what may be
        provided by the data store source or by the stylesUrl field."""
        return self.__extraStylesUrl

    @extraStylesUrl.setter
    def extraStylesUrl(self, value: str | None):
        self.__extraStylesUrl = str(value) if value else None

    @property
    def provideSpectralIndexStyles(self) -> bool:
        """Whether or not to provide a set of spectral-index styles for
        the coverages of this data store.  For each coverage, only the
        spectral-index styles that are compatible with the channels/bands
        of that coverage will be provided."""
        return self.__provideSpectralIndexStyles

    @provideSpectralIndexStyles.setter
    def provideSpectralIndexStyles(self, value: bool):
        self.__provideSpectralIndexStyles = bool(value)

    @property
    def simulateTiles(self) -> list[str]:
        """Some data store types (such as "cubestor", "ogcapi",
        and "wmts") are capable of natively providing map tiles,
        while others aren't.  Setting this gives the Stratos
        Geospatial Data Server permission to provide a tile interface
        by making tile-sized map requests to the data store source.
        The value is a list of coordinate-reference-system strings
        indicating the coordinate reference systems that such simulated
        tiles should be provided in.  It's common to provide tiles in at
        least the Web Mercator (EPSG:3857) coordinate reference system.
        This should only be set to a non-empty list if the data store
        source is incapable of natively providing map tiles."""
        return self.__simulateTiles

    @simulateTiles.setter
    def simulateTiles(self, value: list[str] | str | None):
        if value:
            if isinstance(value, list):
                self.__simulateTiles = value
            else:
                self.__simulateTiles = [ str(value) ]
        else:
            self.__simulateTiles = []

    @property
    def hints(self) -> dict[str,str]:
        """A set of hints to provide to the CubeWerx Stratos convert
        library to help it understand or process the data store source."""
        return self.__hints

    @hints.setter
    def hints(self, value: dict[str,str] | None):
        self.__hints = value if value else []

    @property
    def accessControlRules(self) -> list[AccessControlRule]:
        """The set of access control rules for this data store."""
        return self.__accessControlRules

    @accessControlRules.setter
    def accessControlRules(self, value: list[AccessControlRule] | None):
        self.__accessControlRules = value if value else []

    @property
    def canBeManaged(self) -> bool:
        """Whether or not layers can be added to or removed from this
        data store, and whether or not the contents of the layers of
        this data store can be managed.  True if and only if the data
        store is of type "cubestor" and is part of a Stratos Geospatial
        Data Server.  I.e., if the caller manually creates a new
        `DataStore` object, it can't be managed until
        Stratos.addOrReplaceDataStore() is called."""
        return (self.type == "cubestor" and
                self.__stratos and
                self.__dataStoreAdminUrl and
                self.__ogcApiLandingPageUrl)

    @property
    def ogcApiUrl(self) -> str | None:
        """The URL of the OGC API landing page for this data store, or
        None if the data store is not yet associated with a Stratos
        Geospatial Data Server."""
        return self.__ogcApiLandingPageUrl

    def getLayers(self, forceRefetch: bool = False) -> list[Layer]:
        """Return the list of layers (feature sets) that this data store
        provides.

        Args:
            forceRefetch: If True, the list of layers is (re-)fetched from
                the server even if a cached copy exists.

        Returns:
            The list of layers that this data store provides.
        """
        # If we're not associated with a Stratos Geospatial Data Server
        # yet, simply return an empty list.
        if not self.__stratos or not self.__ogcApiLandingPageUrl:
            return []

        # Return cached results if available.
        if not forceRefetch and self.__layerCache is not None:
            return self.__layerCache

        # Fetch the {ogcApiLandingPage}/collections document.
        collectionsUrl = self.__ogcApiLandingPageUrl + "/collections"
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = { "limit": "unlimited" }
        response = requests.get(collectionsUrl, headers=requestHeaders,
            params=params)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Parse the collections into Layer objects.
        layers = []
        collectionsJson = responseJson.get("collections")
        if isinstance(collectionsJson, list):
            for collectionJson in collectionsJson:
                layer = Layer(collectionJson, self, collectionsUrl,
                    self.__stratos)
                if layer: layers.append(layer)

        # Cache the results.
        self.__layerCache = layers

        return layers

    def getLayer(self, layerId: str, forceRefetch: bool = False) -> Layer | None:
        """Return the specified layer (feature set) within this data store.

        Args:
            layerId: a layer ID
            forceRefetch: If True, the list of layers is (re-)fetched from
                the server even if a cached copy exists.

        Returns:
            The layer with the specified name, or None if no such layer
            exists in this data store.
        """
        layers = self.getLayers(forceRefetch)
        for layer in layers:
            if layer.id == layerId:
                return layer
        return None

    def addVectorLayer(self, id: str,
                       jsonSchema: object | str | None = None,
                       title: str | None = None,
                       description: str | None = None,
                       addDefaultStyle: bool = True) -> Layer:
        """Add a vector layer to this data store.  This can only
        be done for data stores whose canBeManaged property is True.
        The layer is immediately added to the Stratos Geospatial Data
        Server; there's no need to call Stratos.updateDataStore() to
        commit the addition.

        Args:
            id: The ID/name to give the layer.  The data store must not
                already have a layer with this ID.
            jsonSchema: The JSON schema describing the data that will be
                loaded into this layer, or None.  It can be passed as
                an object (like what json.load() provides), a string
                representation of the schema, or a file path or URL to
                a JSON schema.  As per "OGC API - Features - Part 5:
                Schemas", if a property is marked with "x-ogc-role":
                "primary-geometry", then it's considered the property
                that will hold the feature's primary geometry.  If no
                geometry property is present, one will be automatically
                added.  If the schema is specified as None, the features
                of the resulting layer will have no properties (other
                than its geometry).
            title: A title to give the layer, or None.
            description: A brief textual description to give the layer,
                or None.
            addDefaultStyle: Whether or not to automatically add a default
                style to the layer (making maps and map tiles available
                for it).
        RETURNS:
            The new vector layer.
        """
        if self.type != "cubestor":
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")
        if not self.__stratos or not self.__dataStoreAdminUrl:
            raise CwException("this data store is not yet part of a "
                              "Stratos Geospatial Data Server")

        # Resolve the JSON schema into an object if not provided as such.
        if jsonSchema is None:
            jsonSchema = { "type": "object", "properties": {} }
        elif isinstance(jsonSchema, str):
            jsonSchema = jsonSchema.strip()
            if jsonSchema.startswith("{"):
                jsonSchema = json.loads(jsonSchema)
            else:
                jsonSchemaFile = open(jsonSchema)
                jsonSchema = json.load(jsonSchemaFile)
                jsonSchemaFile.close()

        # Make the HTTP PUT request to create the collection.
        collectionsUrl = self.__ogcApiLandingPageUrl + "/collections"
        collectionUrl = collectionsUrl + "/" + quote(id)
        requestHeaders = {
            "Content-Type": "application/schema+json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        if title: params["title"] = title
        if description: params["description"] = description
        params["addDefaultStyle"] = bool(addDefaultStyle)
        response = requests.put(collectionUrl, headers=requestHeaders,
            params=params, data=json.dumps(jsonSchema))
        ServerException.raise_for_status(response)

        # Fetch the definition of the new collection.
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.get(collectionUrl, headers=requestHeaders)
        ServerException.raise_for_status(response)

        # Parse the definition of the new collection into a Layer object,
        # and update the layer cache.
        newLayer = Layer(response.json(), self, collectionsUrl,
            self.__stratos)
        if (self.__layerCache is not None):
            self.__layerCache.append(newLayer)

        # We're done!
        return newLayer

    def addVectorLayerWithData(self, id: str,
                               filePathsOrFeatureCollection: list[str] | geojson.FeatureCollection,
                               title: str | None = None,
                               description: str | None = None,
                               dataCoordSys: str | None = None,
                               nominalResM: float | None = None,
                               addDefaultStyle: bool = True,
                               updateTiles: bool = False) -> Layer:
        """Add a vector layer to this data store and populate it with some
        initial data.  The schema of the layer will be sniffed from this
        initial data.  This can only be done for data stores whose
        canBeManaged property is True.  The layer is immediately added to
        the Stratos Geospatial Data Server; there's no need to call
        Stratos.updateDataStore() to commit the addition.
        Args:
            id: The ID/name to give the layer.  The data store must not
                already have a layer with this ID.
            filePathsOrFeatureCollection: Either a list of one or more
                fully-qualified local file paths of source vector
                data to be loaded (including any necessary auxilliary
                files), or a GeoJSON FeatureCollection to be loaded.
                It's also possible to specify a single-element list
                consisting of the fully-qualified local file path of a
                ZIP file containing the source data to load, as long
                as it meets the following requirements: a) it's the
                only specified file, b) it has a '.zip' suffix, and c)
                it consists only of files or of exactly one directory
                whose contents exist only of files.
            title: A title to give the layer, or None.
            description: A brief textual description to give the layer,
                or None.
            dataCoordSys: The coordinate system that the data is in (e.g.
                "http://www.opengis.net/def/crs/OGC/1.3/CRS84"), or None
                to auto-detect.
            nominalResM: The nominal resolution of this data in metres, or
                None to autodetect.  This helps the server know how deep
                to pregenerate tiles.
            addDefaultStyle: Whether or not to automatically add a default
                style to the layer (making maps and map tiles available
                for it).
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        RETURNS:
            The new vector layer.
        """
        if self.type != "cubestor":
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")
        if not self.__stratos or not self.__dataStoreAdminUrl:
            raise CwException("this data store is not yet part of a "
                              "Stratos Geospatial Data Server")

        # Prepare the server request.
        collectionsUrl = self.__ogcApiLandingPageUrl + "/collections"
        collectionUrl = collectionsUrl + "/" + quote(id)
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        if title: params["title"] = title
        if description: params["description"] = description
        if dataCoordSys:
            params["dataCoordSys"] = str(dataCoordSys)
        if nominalResM and float(nominalResM) > 0:
            params["nominalResM"] = float(nominalResM)
        params["addDefaultStyle"] = bool(addDefaultStyle)
        params["updateTiles"] = bool(updateTiles)

        if isinstance(filePathsOrFeatureCollection, list):
            nFiles = len(filePathsOrFeatureCollection)
            if nFiles < 1:
                # No data files were specified.
                raise ValueError("a filePaths list must contain at least one path")
            elif nFiles == 1 and filePathsOrFeatureCollection[0].endswith('.zip'):
                # A ZIP file was specified.  Open it.
                zipFile = os.open(filePathsOrFeatureCollection[0], 'rb')
            else:
                # One or more data files were specified.  Package them together
                # into a temporary ZIP archive.
                zipFile = tempfile.TemporaryFile(suffix='.zip')
                zipArchive = zipfile.ZipFile(zipFile, "x")
                for filePath in filePathsOrFeatureCollection:
                    filename = os.path.basename(filePath)
                    if filename:
                        zipArchive.write(filePath, filename)
                zipArchive.close()
                zipFile.seek(0)

            # Make the HTTP PUT request to create the collection.
            requestHeaders["Content-Type"] = "application/zip"
            response = requests.put(collectionUrl, headers=requestHeaders,
                params=params, data=zipFile)
            ServerException.raise_for_status(response)

            # Close (and remove) the temporary ZIP file.
            zipFile.close()
        elif isinstance(filePathsOrFeatureCollection, geojson.FeatureCollection):
            # A GeoJSON object was specified.
            # Make the HTTP PUT request to create the collection.
            requestHeaders["Content-Type"] = "application/geo+json"
            response = requests.put(collectionUrl, headers=requestHeaders,
                params=params, data=geojson.dumps(filePathsOrFeatureCollection))
            ServerException.raise_for_status(response)
        else:
            raise TypeError("list[str] or geojson.FeatureCollection expected")

        # Fetch the definition of the new collection.
        response = requests.get(collectionUrl, headers=requestHeaders)
        ServerException.raise_for_status(response)

        # Parse the definition of the new collection into a Layer object,
        # and update the layer cache.
        newLayer = Layer(response.json(), self, collectionsUrl,
            self.__stratos)
        if (self.__layerCache is not None):
            self.__layerCache.append(newLayer)

        # We're done!
        return newLayer

    def addCoverageLayer(self, id: str, title: str = None,
                         description: str = None,
                         addDefaultStyle: bool = True) -> Layer:
        """Add a coverage layer to this data store.  This can only
        be done for data stores whose canBeManaged property is True.
        The layer is immediately added to the Stratos Geospatial Data
        Server; there's no need to call Stratos.updateDataStore() to
        commit the addition.

        Args:
            id: The ID/name to give the layer.  The data store must not
                already have a layer with this ID.
            title: A title to give the layer, or None.
            description: A brief textual description to give the layer,
                or None.
            addDefaultStyle: Whether or not to automatically add a default
                style to the layer (making maps and map tiles available
                for it).
        RETURNS:
            The new coverage layer.
        """
        if self.type != "cubestor":
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")
        if not self.__stratos or not self.__ogcApiLandingPageUrl:
            raise CwException("this data store is not yet part of a "
                              "Stratos Geospatial Data Server")

        # Make the HTTP PUT request to create the collection.
        collectionsUrl = self.__ogcApiLandingPageUrl + "/collections"
        collectionUrl = collectionsUrl + "/" + quote(id)
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        params["addDefaultStyle"] = bool(addDefaultStyle)
        jsonBody = {}
        if title: jsonBody["title"] = title
        if description: jsonBody["description"] = description
        response = requests.put(collectionUrl, headers=requestHeaders,
            params=params, json=jsonBody)
        ServerException.raise_for_status(response)

        # Fetch the definition of the new collection.
        response = requests.get(collectionUrl, headers=requestHeaders)
        ServerException.raise_for_status(response)

        # Parse the definition of the new collection into a Layer object,
        # and update the layer cache.
        newLayer = Layer(response.json(), self, collectionsUrl,
            self.__stratos)
        if (self.__layerCache is not None):
            self.__layerCache.append(newLayer)

        # We're done!
        return newLayer

    def removeLayer(self, layer: Layer | str) -> bool:
        """Remove a layer from this data store.  This can only be
        done for data stores whose canBeManaged property is True, and
        should only be done if no tile update is in progress for the
        layer.  The layer is immediately removed from the Stratos
        Geospatial Data Server; there's no need to call
        Stratos.updateDataStore() to commit the removal.

        WARNING: This will remove all data associated with the layer!!!
        This could be catastrophic if done unintentionally, so be careful!

        Args:
            layer: A layer definition or ID/name.

        Returns:
            True if the layer was removed, or False if the layer didn't
            exist.
        """
        if self.type != "cubestor":
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")
        if not self.__stratos or not self.__dataStoreAdminUrl:
            return False

        # Determine the ID of the layer to remove.
        id = layer.id if isinstance(layer, Layer) else layer

        # Make the HTTP DELETE request to delete the collection.
        collectionsUrl = self.__ogcApiLandingPageUrl + "/collections"
        collectionUrl = collectionsUrl + "/" + quote(id)
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.delete(collectionUrl, headers=requestHeaders)
        if response.status_code == 404: return False
        ServerException.raise_for_status(response)

        # Remove this layer from the layer cache.
        if (self.__layerCache is not None):
            for i in range(len(self.__layerCache)):
                if self.__layerCache[i].id == id:
                    del self.__layerCache[i]
                    break

        # We're done!
        return True

    def _setServerAssociation(self, stratos: Stratos | None,
            dataStoreAdminUrl: str | None, ogcApiLandingPageUrl: str | None):
        self.__stratos = stratos
        self.__dataStoreAdminUrl = dataStoreAdminUrl
        self.__ogcApiLandingPageUrl = ogcApiLandingPageUrl
        self.__layerCache = None

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}
        jsonRep["type"] = self.__type
        jsonRep["source"] = self.__source
        if self.__title:
            jsonRep["title"] = self.__title._jsonRep
        if self.__description:
            jsonRep["description"] = self.__description._jsonRep
        if self.__attributionTitle:
            jsonRep["attributionTitle"] = self.__attributionTitle._jsonRep
        if self.__attributionUrl:
            jsonRep["attributionUrl"] = self.__attributionUrl
        if self.__attributionHtml:
            jsonRep["attributionHtml"] = self.__attributionHtml._jsonRep
        if self.__attributionLogoUrl:
            jsonRep["attributionLogoUrl"] = self.__attributionLogoUrl
        if self.__licenseTitle:
            jsonRep["licenseTitle"] = self.__licenseTitle._jsonRep
        if self.__licenseUrl:
            jsonRep["licenseUrl"] = self.__licenseUrl
        if self.__licenseHtml:
            jsonRep["licenseHtml"] = self.__licenseHtml._jsonRep
        if self.__isExternalService:
            jsonRep["isExternalService"] = self.__isExternalService
        if self.__omitDataStoreTheme:
            jsonRep["omitDataStoreTheme"] = self.__omitDataStoreTheme
        if self.__stylesUrl:
            jsonRep["stylesUrl"] = self.__stylesUrl
        if self.__extraStylesUrl:
            jsonRep["extraStylesUrl"] = self.__extraStylesUrl
        if self.__provideSpectralIndexStyles:
            jsonRep["provideSpectralIndexStyles"] = \
                self.__provideSpectralIndexStyles
        if self.__simulateTiles:
            jsonRep["simulateTiles"] = self.__simulateTiles
        if self.__hints:
            jsonRep["hints"] = self.__hints

        jsonRep["accessControlRules"] = acrs = []
        for acr in self.__accessControlRules:
            acrs.append(acr._jsonRep)

        return jsonRep

    @property
    def _patchDict(self) -> dict:
        patch = {}

        if repr(self.__type) != self.__typeOrigRep:
            patch["type"] = self.__type
        if repr(self.__source) != self.__sourceOrigRep:
            patch["source"] = self.__source
        if repr(self.__title) != self.__titleOrigRep:
            patch["title"] = self.__title._jsonRep
        if repr(self.__description) != self.__descriptionOrigRep:
            patch["description"] = self.__description._jsonRep
        if repr(self.__attributionTitle) != self.__attributionTitleOrigRep:
            patch["attributionTitle"] = self.__attributionTitle._jsonRep
        if repr(self.__attributionUrl) != self.__attributionUrlOrigRep:
            patch["attributionUrl"] = self.__attributionUrl
        if repr(self.__attributionHtml) != self.__attributionHtmlOrigRep:
            patch["attributionHtml"] = self.__attributionHtml._jsonRep
        if repr(self.__attributionLogoUrl) != self.__attributionLogoUrlOrigRep:
            patch["attributionLogoUrl"] = self.__attributionLogoUrl
        if repr(self.__licenseTitle) != self.__licenseTitleOrigRep:
            patch["licenseTitle"] = self.__licenseTitle._jsonRep
        if repr(self.__licenseUrl) != self.__licenseUrlOrigRep:
            patch["licenseUrl"] = self.__licenseUrl
        if repr(self.__licenseHtml) != self.__licenseHtmlOrigRep:
            patch["licenseHtml"] = self.__licenseHtml._jsonRep
        if repr(self.__isExternalService) != self.__isExternalServiceOrigRep:
            patch["isExternalService"] = self.__isExternalService
        if repr(self.__omitDataStoreTheme) != self.__omitDataStoreThemeOrigRep:
            patch["omitDataStoreTheme"] = self.__omitDataStoreTheme
        if repr(self.__stylesUrl) != self.__stylesUrlOrigRep:
            patch["stylesUrl"] = self.__stylesUrl
        if repr(self.__extraStylesUrl) != self.__extraStylesUrlOrigRep:
            patch["extraStylesUrl"] = self.__extraStylesUrl
        if repr(self.__provideSpectralIndexStyles) != \
                self.__provideSpectralIndexStylesOrigRep:
            patch["provideSpectralIndexStyles"] = \
                self.__provideSpectralIndexStyles
        if repr(self.__simulateTiles) != self.__simulateTilesOrigRep:
            patch["simulateTiles"] = self.__simulateTiles
        if repr(self.__hints) != self.__hintsOrigRep:
            patch["hints"] = self.__hints
        if repr(self.__accessControlRules) != self.__accessControlRulesOrigRep:
            patch["accessControlRules"] = acrs = []
            for rule in self.__accessControlRules:
                acrs.append(rule._jsonRep)

        return patch

##############################################################################

class Layer:
    """A layer (called a "collection" in the OGC API) that's available
    through a data store.

    Do not instantiate directly.  To add a layer to a data store,
    call either DataStore.addVectorLayer() or DataStore.addCoverageLayer().
    """

    def __init__(self, jsonRep: dict,
                 dataStore: cubewerx.stratos.DataStore.DataStore,
                 collectionsUrl: str, stratos: Stratos):
        """@private"""
        self.__id = jsonRep.get("id")
        if not self.__id:
            raise ValueError("jsonRep missing required 'id' field")

        title = jsonRep.get("title")
        self.__title = str(title) if title else None

        description = jsonRep.get("description")
        self.__description = str(description) if description else None

        self.__links = jsonRep.get("links", [])

        self.__wgs84Extent = None
        extentJson = jsonRep.get("extent")
        if extentJson:
            spatialJson = extentJson.get("spatial")
            if spatialJson:
                bboxJson = spatialJson.get("bbox")
                if isinstance(bboxJson, list) and len(bboxJson) > 0:
                    firstBbox = bboxJson[0]
                    if isinstance(firstBbox, list) and len(firstBbox) > 3:
                        self.__wgs84Extent = firstBbox

        self.__isVectors = (jsonRep.get("itemType") == "feature")
        self.__isCoverage = False
        self.__isMappable = False
        for link in self.__links:
            rel = link.get("rel")
            if rel:
                if rel.endswith("/coverage") or rel.endswith(":coverage]"):
                    self.__isCoverage = True
                elif rel.endswith("/coverage-scenes"):
                    self.__isCoverage = True
                elif rel.endswith(":coverage-scenes]"):
                    self.__isCoverage = True
                elif rel.endswith("/map") or rel.endswith(":map]"):
                    self.__isMappable = True
                    # Technically this is true even if no styles are
                    # listed, although our CubeSTOR layers typically don't
                    # behave that way.

        self.__dataStore = dataStore
        self.__collectionUrl = collectionsUrl + "/" + quote(self.__id)
        self.__itemsUrl = self.__collectionUrl + "/items"
        self.__stylesUrl = self.__collectionUrl + "/styles"
        self.__stratos = stratos

        self.__styles = []
        stylesJson = jsonRep.get("styles")
        if isinstance(stylesJson, list):
            for styleJson in stylesJson:
                style = Style(styleJson, self.__stylesUrl,
                    self.canBeManaged, self.__stratos)
                self.__styles.append(style)

        self.__lastTileUpdateProgress = None
        self.__lastTileUpdateProgressTime = -math.inf

    @property
    def id(self) -> str:
        """The ID/name of this layer."""
        return self.__id

    @property
    def title(self) -> str | None:
        """The title of this layer, or None.  Setting this (or clearing
        it by setting it to the empty string or None) will automatically
        update the server."""
        return self.__title

    @title.setter
    def title(self, title: str | None):
        if title != self.__title:
            requestHeaders = {
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.patch(self.__collectionUrl,
                headers=requestHeaders, json={"title": title})
            ServerException.raise_for_status(response)
            self.__title = title

    @property
    def description(self) -> str | None:
        """A brief textual description of this layer, or None.  Setting
        this (or clearing it by setting it to the empty string or None)
        will automatically update the server."""
        return self.__description

    @description.setter
    def description(self, description: str | None):
        if description != self.__description:
            requestHeaders = {
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.patch(self.__collectionUrl,
                headers=requestHeaders, json={"description": description})
            ServerException.raise_for_status(response)
            self.__description = description

    @property
    def wgs84Extent(self) -> list | None:
        """The WGS 84 Geographic bounding box of this layer ([minLon,
        minLat, maxLon, maxLat]), or None.  If minLon > maxLon, then the
        bounding box spans the antimeridian."""
        return self.__wgs84Extent

    # TODO: temporalExtent property
    # TODO: nativeCrs property
    # TODO: styles property
    # TODO: defaultStyle property

    @property
    def isVectors(self) -> bool:
        """Whether or not this a vector layer."""
        return self.__isVectors

    @property
    def isCoverage(self) -> bool:
        """Whether or not this a coverage layer."""
        return self.__isCoverage

    @property
    def isMappable(self) -> bool:
        """Whether or not maps can be requested from this layer."""
        return self.__isMappable

    @property
    def canBeManaged(self) -> bool:
        """Whether or not the data and styles of this layer can be
        manipulated."""
        return self.__dataStore.type == "cubestor"

    @property
    def ogcApiUrl(self) -> str:
        """The URL of the OGC API collection representing this layer."""
        return self.__collectionUrl

    @property
    def styles(self) -> list[Style]:
        """The styles available for this layer."""
        return self.__styles

    @property
    def tileUpdateProgress(self) -> float:
        """The progress (as a percentage from 0 to 100) of the current or
        last tile-update job for this layer."""
        # Make sure we don't hit the server more then twice a second.
        currentTime = time.time()
        if currentTime < self.__lastTileUpdateProgressTime + 0.5:
            return self.__lastTileUpdateProgress
        else:
            progressUrl = self.__collectionUrl + "/tileUpdateProgress"
            requestHeaders = {
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.get(progressUrl, headers=requestHeaders)
            ServerException.raise_for_status(response)
            progress = response.json().get("percentage")
            self.__lastTileUpdateProgress = progress
            self.__lastTileUpdateProgressTime = currentTime
            return progress

    def getMap(self, width: int | None = None, height: int | None = None,
               wgs84Extent: list[float] | None = None,
               style: Style | str | None = None) -> Image.Image:
        """Return a map of the layer as an image in the Spherical
        Mercator (EPSG:3857) coordinate system.  This can only be done
        if `isMappable`.  Note that the map might not show source images
        or vector features that were very recently added, as the tiling
        of this new data might not yet be complete.

        Args:
            width: The width of the map in pixels, or None for auto.
            height: The height of the map in pixels, or None for auto.
            wgs84Extent: The WGS 84 Geographic spatial extent of the area
                of interest (expressed as [minLon, minLat, maxLon, maxLat]),
                or None to request a map of the entire layer.
            style: The style to use (either a Style object or the ID/Name
                of the style), or None to use the default style.
        Returns:
            The requested map image.
        """
        # Fetch and return the requested map image.
        # (Note that we can't simply return the URL of the map image,
        # because it might require an authorized user to access.)
        if style:
            styleId = style.id if isinstance(style, Style) else style
            mapUrl = self.__collectionUrl + "/styles/" + quote(styleId) + "/map"
        else:
            mapUrl = self.__collectionUrl + "/map"
        params = {}
        if width and int(width) > 0:
            params["width"] = int(width)
        if height and int(height) > 0:
            params["height"] = int(height)
        if isinstance(wgs84Extent, list) and len(wgs84Extent) == 4:
            # Unfortunately, this encodes the commas.  Fortunately, our
            # server will accept bbox values with either encoded or unencoded
            # commas.
            params["bbox"] = "%s,%s,%s,%s" % (wgs84Extent[0], wgs84Extent[1],
                                              wgs84Extent[2], wgs84Extent[3])
            params["bbox-crs"] = "CRS:84"
        params["crs"] = "EPSG:3857"
        requestHeaders = self.__stratos.commonRequestHeaders
        response = requests.get(mapUrl,
            headers=requestHeaders, params=params)
        ServerException.raise_for_status(response)
        return Image.open(io.BytesIO(response.content))

    def getNVectorFeatures(self,
                           wgs84Extent: geojson.Polygon | list[float] | None = None,
                           relation: SpatialRelation = "SpatialRelation.INTERSECTS") -> int:

        """Return the number vector features in this layer.

        Args:
            wgs84Extent: The WGS 84 Geographic spatial extent of the area
                of interest (expressed as a GeoJSON Polygon or as a
                [minLon, minLat, maxLon, maxLat] array), or None to request
                the number of features of the entire layer.
            relation: The spatial relation to use when comparing against
                the specified wgs84Extent
        Returns:
            The number of vector features in this layer.
        """
        if not self.__isVectors: return 0

        params = { "crs": "CRS:84" }
        Layer.__addGeomAndRelationParams(params, wgs84Extent, relation)
        params["limit"] = 0
        requestHeaders = {
            "Accept": "application/geo+json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.head(self.__itemsUrl,
            headers=requestHeaders, params=params)
        ServerException.raise_for_status(response)
        nFeaturesStr = response.headers.get("OGC-NumberMatched")
        return int(nFeaturesStr) if nFeaturesStr else 0

    def getVectorFeatures(self,
                  wgs84Extent: geojson.Polygon | list[float] | None = None,
                  relation: SpatialRelation = "SpatialRelation.INTERSECTS",
                  limit: int | None = None, offset: int = 0,
                  simplifyToScale: float | None = None) -> geojson.FeatureCollection:
        """Fetch the vector features of this layer.  This can only be done
        if `isVectors`.

        Args:
            wgs84Extent: The WGS 84 Geographic spatial extent of the area
                of interest (expressed as a GeoJSON Polygon or as a
                [minLon, minLat, maxLon, maxLat] array), or None to request
                the features of the entire layer.
            relation: The spatial relation to use when comparing against
                the specified wgs84Extent
            limit: The maximum number of vector features to return, or None
                to let the server decide.
            offset: The zero-based start index of the first feature to
                return.  Useful for paging.
            simplifyToScale: The scale (ratio of the distance on the map
                to the corresponding distance on the ground) to simplify
                the geometries to, or None to not simplify.
        Returns:
            The vector features of this layer.
        """
        if not self.__isVectors: return geojson.FeatureCollection([])

        params = { "crs": "CRS:84" }
        Layer.__addGeomAndRelationParams(params, wgs84Extent, relation)
        if limit is not None and int(limit) >= 0:
            params["limit"] = int(limit)
        if int(offset) > 0:
            params["offset"] = int(offset)
        if simplifyToScale is not None and float(simplifyToScale) > 0:
            params["scale-denominator"] = float(simplifyToScale)
        requestHeaders = {
            "Accept": "application/geo+json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.get(self.__itemsUrl,
            headers=requestHeaders, params=params)
        ServerException.raise_for_status(response)
        return geojson.loads(response.text)

    def addVectorFeatures(self,
            filePathsOrFeatureCollection: list[str] | geojson.FeatureCollection,
            dataCoordSys: str | None = None,
            nominalResM: float | None = None,
            updateTiles: bool = False):
        """Add one or more vector features to this layer.  This can only
        be done if `canBeManaged` and `isVectors`.  Note that this does
        not update the wgs84Extent property of the `Layer` object.

        Args:
            filePathsOrFeatureCollection: Either a list of one or more
                fully-qualified local file paths of source vector
                data to be loaded (including any necessary auxilliary
                files), or a GeoJSON FeatureCollection to be loaded.
                It's also possible to specify a single-element list
                consisting of the fully-qualified local file path of a
                ZIP file containing the source data to load, as long
                as it meets the following requirements: a) it's the
                only specified file, b) it has a '.zip' suffix, and c)
                it consists only of files or of exactly one directory
                whose contents exist only of files.
            dataCoordSys: The coordinate system that the data is in (e.g.
                "http://www.opengis.net/def/crs/OGC/1.3/CRS84"), or None
                to auto-detect.
            nominalResM: The nominal resolution of this data in metres, or
                None to autodetect.  This helps the server know how deep
                to pregenerate tiles.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Prepare the server request.
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        if dataCoordSys:
            params["dataCoordSys"] = str(dataCoordSys)
        if nominalResM and float(nominalResM) > 0:
            params["nominalResM"] = float(nominalResM)
        params["updateTiles"] = bool(updateTiles)

        if isinstance(filePathsOrFeatureCollection, list):
            nFiles = len(filePathsOrFeatureCollection)
            if nFiles < 1:
                # No data files were specified.
                raise ValueError("a filePaths list must contain at least one path")
            elif nFiles == 1 and filePathsOrFeatureCollection[0].endswith('.zip'):
                # A ZIP file was specified.  Open it.
                zipFile = os.open(filePathsOrFeatureCollection[0], 'rb')
            else:
                # One or more data files were specified.  Package them together
                # into a temporary ZIP archive.
                zipFile = tempfile.TemporaryFile(suffix='.zip')
                zipArchive = zipfile.ZipFile(zipFile, "x")
                for filePath in filePathsOrFeatureCollection:
                    filename = os.path.basename(filePath)
                    if filename:
                        zipArchive.write(filePath, filename)
                zipArchive.close()
                zipFile.seek(0)

            # Make the HTTP POST request to add these features
            requestHeaders["Content-Type"] = "application/zip"
            response = requests.post(self.__itemsUrl, headers=requestHeaders,
                params=params, data=zipFile)
            ServerException.raise_for_status(response)

            # Close (and remove) the temporary ZIP file.
            zipFile.close()
        elif isinstance(filePathsOrFeatureCollection, geojson.FeatureCollection):
            # A GeoJSON object was specified.
            # Make the HTTP POST request to add these features
            requestHeaders["Content-Type"] = "application/geo+json"
            response = requests.post(self.__itemsUrl, headers=requestHeaders,
                params=params, data=geojson.dumps(filePathsOrFeatureCollection))
            ServerException.raise_for_status(response)
        else:
            raise TypeError("list[str] or geojson.FeatureCollection expected")

    def removeVectorFeatures(self,
                  wgs84Extent: geojson.Polygon | list[float] | None = None,
                  relation: SpatialRelation = "SpatialRelation.INTERSECTS",
                  updateTiles: bool = False) -> int:
        """Remove vector features from this layer.  This can only
        be done if `canBeManaged` and `isVectors`.  Note that this does
        not update the wgs84Extent property of the `Layer` object.

        Args:
            wgs84Extent: The WGS 84 Geographic spatial extent of the area
                to remove the features from (expressed as a GeoJSON Polygon
                or as a [minLon, minLat, maxLon, maxLat] array), or None to
                remove all of the features of the layer.
            relation: The spatial relation to use when comparing against
                the specified wgs84Extent
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        Returns:
            The number of vector features removed.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        params = {}
        Layer.__addGeomAndRelationParams(params, wgs84Extent, relation)
        requestHeaders = self.__stratos.commonRequestHeaders
        response = requests.delete(self.__itemsUrl,
            headers=requestHeaders, params=params)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Parse out and return the number of features that were removed.
        nRemoved = 0
        transactionSummaryJson = responseJson.get("transactionSummary")
        if transactionSummaryJson:
            totalDeletedJson = transactionSummaryJson.get("totalDeleted")
            if totalDeletedJson:
                nRemoved = int(totalDeletedJson)
        return nRemoved

    def getSourceImages(self, includeGood: bool = True,
                        includeBad: bool = False) -> list[SourceImage]:
        """Return a list of all of the source images of this layer,
        regardless of what collection (if any) they're in.  Only useful
        for coverage layers.

        Args:
            includeGood: Whether or not to include good source images.
            includeBad: Whether or not to include bad source images.

        Returns:
            A list of the source images of this layer.
        """
        # Fetch the .../collections/{collectionId}/scenes document.
        scenesUrl = self.__collectionUrl + "/scenes"
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {
            "includeGood": includeGood,
            "includeBad": includeBad,
            "limit": 1000000,
        }
        response = requests.get(scenesUrl, headers=requestHeaders,
            params=params)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Parse the scenes into SourceImage objects.
        sourceImages = []
        scenesJson = responseJson.get("scenes")
        if isinstance(scenesJson, list):
            for sceneJson in scenesJson:
                sourceImage = SourceImage(sceneJson, scenesUrl, self.__stratos)
                if sourceImage: sourceImages.append(sourceImage)

        return sourceImages

    def addSourceImages(self, filePaths: list[str],
                        hints: SourceImageHints = None,
                        updateTiles: bool = False) -> list[SourceImage]:
        """Add one or more source images to this layer.  This can only
        be done if `canBeManaged` and `isCoverage`.  Source images
        added in this way don't get added to a specific collection.
        Also note that this does not update the wgs84Extent property of
        the `Layer` object.

        Args:
            filePaths: The fully-qualified local file paths to the source
                image(s) to be added, including any necessary auxilliary
                files.  Alternatively, a ZIP file containing the source
                image(s) to be added can be specified, as long as it meets
                the following requirements: a) it's the only specified
                file, b) it has a '.zip' suffix, and c) it consists only
                of files or of exactly one directory whose contents exist
                only of files.
            hints: Hints to help the Stratos Geospatial Data Server
                interpret the source images, or None.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        Returns:
            A list of the source images that were added.  Note that some
            of the source images may be marked as bad, and should be
            adjusted or removed.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        nFiles = len(filePaths)
        if nFiles < 1:
            # No source images were specified.  Trivial return.
            return []
        elif nFiles == 1 and filePaths[0].endswith('.zip'):
            # A ZIP file was specified.  Open it.
            zipFile = os.open(filePaths[0], 'rb')
        else:
            # One or more source-image files were specified.  Package
            # them together into a temporary ZIP archive.
            zipFile = tempfile.TemporaryFile(suffix='.zip')
            zipArchive = zipfile.ZipFile(zipFile, "x")
            for filePath in filePaths:
                filename = os.path.basename(filePath)
                if filename:
                    zipArchive.write(filePath, filename)
            zipArchive.close()
            zipFile.seek(0)

        # Make an HTTP POST request to the scenes endpoint.
        scenesUrl = self.__collectionUrl + "/scenes"
        requestHeaders = {
            "Accept": "application/json",
            "Content-Type": "application/zip"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        if hints is not None:
             params.update(hints._dict)
        params["updateTiles"] = bool(updateTiles)
        response = requests.post(scenesUrl, headers=requestHeaders,
                                 params=params, data=zipFile)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Close (and remove) the temporary ZIP file.
        zipFile.close()

        # Read the resulting SourceImage objects from the response.
        sourceImages = []
        if isinstance(responseJson, list):
            for sceneJson in responseJson:
                sourceImage = SourceImage(sceneJson, scenesUrl, self.__stratos)
                if sourceImage: sourceImages.append(sourceImage)

        # We're done!
        return sourceImages

    def removeSourceImages(self, sourceImages: list[SourceImage|str],
                           updateTiles: bool = False):
        """Remove one or more source images from this layer, regardless
        of whether or not they're in a specific collection.  This can
        only be done if `canBeManaged` and `isCoverage`.  Also note
        that this does not update the wgs84Extent property of the
        `Layer` object.

        Args:
            sourceImages: The source-image objects or IDs to remove.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Make an HTTP DELETE request to each specified scene.
        # Pass updateTiles=false to all but the last one.
        scenesUrl = self.__collectionUrl + "/scenes"
        nSourceImages = len(sourceImages)
        for i in range(nSourceImages):
            sourceImage = sourceImages[i]
            sceneId = sourceImage.id if isinstance(sourceImage, SourceImage) \
                else sourceImage
            sceneUrl = scenesUrl + "/" + sceneId

            if i < nSourceImages-1:
                params = { "updateTiles": false }
            else:
                params = { "updateTiles": bool(updateTiles) }

            response = requests.delete(sceneUrl,
                headers=self.__stratos.commonRequestHeaders, params=params)
            ServerException.raise_for_status(response)

    def getCollections(self) -> list[SourceImageCollection]:
        """Return a list of all of the source-image collections of
        this layer.

        Returns:
            A list of the source-image collections of this layer.
        """
        # Fetch the .../collections/{collectionId}/groups document.
        groupsUrl = self.__collectionUrl + "/groups"
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = { "limit": 1000000 }
        response = requests.get(groupsUrl, headers=requestHeaders,
            params=params)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Parse the groups into SourceImageCollection objects.
        collections = []
        groupsJson = responseJson.get("groups")
        if isinstance(groupsJson, list):
            for groupJson in groupsJson:
                collection = SourceImageCollection(groupJson, groupsUrl,
                                                   self.__stratos)
                if collection: collections.append(collection)

        return collections

    def addCollection(self, title: str | None = None,
                      description: str | None = None,
                      referenceOnlyPath: str | None = None,
                      defaultHints: list[SourceImageHints] | None = None,
                     ) -> SourceImageCollection:
        """Add an empty source-image collection to this layer.  This can
        only be done if `canBeManaged` and `isCoverage`.  The collection
        is immediately added to the Stratos Geospatial Data Server.

        Args:
            title: A title to give the collection, or None.
            description:  A brief textual description to give the
                collection, or None.
            referenceOnlyPath: If specified, this will be created as a
                reference-only collection for the source images in the
                specified local directory (beginning with a '/'), remote
                HTTP directory (beginning with an 'https://') or remote
                S3 directory (beginning with an 's3://').  The directory
                must exist and be accessible by the server.  If the
                directory is a remote Amazon S3 directory, the access
                keys for the S3 bucket must be present in the value of
                the s3.awsKeys configuration parameter.  Source images
                may not be added to or removed from reference-only
                collections using this API.  Whenever source images are
                added to or removed from the directory by some other
                means (e.g., direct upload or filesystem copy), the
                collection should be rescanned by calling
                `SourceImageCollection.rescan`.
            defaultHints: A set of default hints to apply to all new
                source images that are added to this collection, or None.

        Returns:
            The new source-image collection.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Make an HTTP POST request to the groups endpoint.
        groupsUrl = self.__collectionUrl + "/groups"
        requestHeaders = {
            "Accept": "application/json",
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        postDict = {}
        if title:
            postDict["title"] = str(title)
        if description:
            postDict["description"] = str(description)
        if referenceOnlyPath:
            postDict["referenceOnlyPath"] = str(referenceOnlyPath)
        if defaultHints is not None:
            postDict["defaultHints"] = defaultHints._dict
        response = requests.post(groupsUrl, headers=requestHeaders,
                                 json=postDict)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Read the resulting SourceImageCollection object from the response.
        collection = SourceImageCollection(responseJson, groupsUrl,
                                           self.__stratos)

        # We're done!
        return collection

    def removeCollection(self, collection: SourceImageCollection | str,
                         updateTiles: bool = False) -> bool:
        """Remove the specified source-image collection from this layer.
        This can only be done if `canBeManaged` and `isCoverage`.

        WARNING: Unless it's a reference-only collection, all of the
        source-image files will also be removed, so be careful!

        Args:
            collection: A source-image collection definition or ID.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.

        Returns:
            True if the collection was removed, or False if the collection
            didn't exist.
        """
        if not self.canBeManaged:
            raise CwException("layer manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Determine the ID of the collection to remove.
        id = collection.id if isinstance(collection, SourceImageCollection) \
            else collection

        # Make the HTTP DELETE request to delete the group.
        groupsUrl = self.__collectionUrl + "/groups"
        groupUrl = groupsUrl + "/" + quote(id)
        requestHeaders = {
            "Accept": "application/json"
        }
        params = { "updateTiles": bool(updateTiles) }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.delete(groupUrl, headers=requestHeaders,
            params=params)
        if response.status_code == 404: return False
        ServerException.raise_for_status(response)

        # We're done!
        return True

    def getStyle(self, styleId: str) -> Style | None:
        """Return the style with the specified ID, or None if this
        layer has no such style.

        Args:
            styleId: The ID of the style to return.
        """
        for style in self.styles:
            if style.id == styleId:
                return style
        return None

    def addStyle(self, styleId: str, sld11UserStyleXmlStr: str,
                 updateTiles: bool = False) -> Style:
        """Adds a new style to this layer.  This can only be done if
        `canBeManaged`.

        Args:
            styleId: The ID to assign this style.
            sld11UserStyleXmlStr: An SLD 1.1 UserStyle element containing
                the style definition.  The UserStyle <Name> within this
                definition must match the specified styleId.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        """
        if not self.canBeManaged:
            raise CwException("style manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Throw an error if the layer already has a style with this ID.
        existingStyle = self.getStyle(styleId)
        if existingStyle:
            raise CwException("layer \"%s\" already has a style with an ID of \"%s\"", (this.id, styleId))

        # Make a request to the server to add the style.
        styleUrl = self.__stylesUrl + "/" + quote(styleId)
        requestHeaders = {
            "Content-Type": "application/vnd.ogc.sld+xml; version=1.1",
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        params["updateTiles"] = bool(updateTiles)
        response = requests.put(styleUrl, headers=requestHeaders,
            params=params, data=sld11UserStyleXmlStr)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Add this style to the list of available styles for this layer.
        newStyle = Style(responseJson, self.__stylesUrl,
            self.canBeManaged, self.__stratos)
        self.__styles.append(newStyle)
        self.____isMappable = True

        return newStyle

    def removeStyle(self, style: Style | str) -> bool:
        """Remove the specified style from this layer.  This can only
        be done if `canBeManaged`.

        Args:
            style: The style object or ID to remove.

        Returns:
            True if the style was removed, or False if the layer didn't
            have this style.
        """
        if not self.canBeManaged:
            raise CwException("style manipulation can only be performed on "
                              "data stores of type \"cubestor\"")

        # Determine the style ID.
        styleId = style.id if isinstance(style, Style) else style

        # Return False if the layer doesn't have a style with this ID.
        existingStyle = self.getStyle(styleId)
        if not existingStyle:
            return False

        # Make a request to the server to remove the style.
        requestHeaders = self.__stratos.commonRequestHeaders
        response = requests.delete(existingStyle.ogcApiUrl,
            headers=requestHeaders)
        ServerException.raise_for_status(response)

        # Remove this style from the list of available styles for this layer.
        self.__styles.remove(existingStyle)
        self.__isMappable = bool(self.__styles)

        return True

    def updateTiles(self, sequential: bool = False,
                    showProgress: bool = False):
        """Triggers a tile update on the data and map tiles of the layer.
        If possible, further manipulation of the data or styles of this
        layer should be avoided until the tile update is complete.

        Args:
            sequential: If False, the method will return immediately and
                the tile-update job will proceed concurrently.  The
                progress of the tile update job can be monitored with the
                `tileUpdateProgress` property.  If True, the method won't
                return until the tile-update job is complete (useful for
                scripting).
            showProgress: Whether or not to report the tile update
                progress.  Only relevant if sequential=True.
        """
        # Send a request to the server to start a tile-update job
        # for this layer.
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.patch(self.__collectionUrl,
            headers=requestHeaders, json={"updateTiles": True})
        ServerException.raise_for_status(response)

        # If sequential mode was requested, poll the tile-update progress
        # in a loop until the tile update is complete.
        if sequential:
            if showProgress:
                print("tile-update progress:   0%", end="", flush=True)
            while True:
                time.sleep(1)
                percentage = self.tileUpdateProgress
                if showProgress:
                    print("\b\b\b\b" + str(int(percentage)).rjust(3) + "%",
                          end="", flush=True)
                if percentage >= 100: break
            print()

    @staticmethod
    def __addGeomAndRelationParams(params: list,
            wgs84Extent: geojson.Polygon | list[float] | None,
            relation: SpatialRelation):
        # Requirement 24A of the "OGC API - Features - Part 1: Core"
        # specification (OGC 17-069r4) dictates that a "bbox" parameter
        # always be handled with the INTERSECTS operator, regardless of
        # the value of any specified "relation" parameter.  We don't want
        # to burden the client with this quirk, so we'll convert the bbox
        # to an equivalent GeoJSON polygon if necessary.
        if isinstance(wgs84Extent, list) and len(wgs84Extent) == 4:
            if relation != SpatialRelation.INTERSECTS:
                wgs84Extent = geojson.Polygon([[
                    (wgs84Extent[0], wgs84Extent[1]),
                    (wgs84Extent[2], wgs84Extent[1]),
                    (wgs84Extent[2], wgs84Extent[3]),
                    (wgs84Extent[0], wgs84Extent[3]),
                    (wgs84Extent[0], wgs84Extent[1])
                ]])

        # Add the approriate parameters.
        if isinstance(wgs84Extent, geojson.Polygon):
            params["geometry"] = geojson.dumps(wgs84Extent)
            params["relation"] = relation
        elif isinstance(wgs84Extent, list) and len(wgs84Extent) == 4:
            # Unfortunately, this encodes the commas.  Fortunately, our
            # server will accept bbox values with either encoded or unencoded
            # commas.
            params["bbox"] = "%s,%s,%s,%s" % (wgs84Extent[0], wgs84Extent[1],
                                              wgs84Extent[2], wgs84Extent[3])

##############################################################################

class LoginHistoryEntry:
    """An entry of the login history.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        timestampStr = jsonRep.get("timestamp")
        self.__timestamp = datetime.datetime.fromisoformat(timestampStr)
        self.__ipAddress = jsonRep.get("ipAddress")
        authUserVal = jsonRep.get("authUser")
        oidUserVal = jsonRep.get("oidUser")
        self.__user = authUserVal if authUserVal else OidUser(oidUserVal)

    @property
    def timestamp(self) -> datetime.datetime:
        """The date and time (in the server's time zone) of the login."""
        return self.__timestamp

    @property
    def ipAddress(self) -> str | None:
        """The IP address of the login, or None if unknown."""
        return self.__ipAddress

    @property
    def user(self) -> str | OidUser:
        """The user account the login, either a string representing the
        username of a CwAuth user or an OidUser object representing an
        OpenID Connect user."""
        return self.__user

##############################################################################

class MultilingualString(collections.UserDict):
    """A string expressed in potentially-multiple languages.

    This is a dictionary that maps ISO 639-1/RFC 3066 language identifiers
    (e.g., "en-CA", "fr") to the string expressed in that language.  The
    optional mapping from the empty string ("") indicates the string
    expressed in an unknown/default language.
    """

    def __init__(self, value: str | dict[str,str]):
      """Create a new multilingual string.

      Args:
          value: Either a simple string (whose language is undefined) or
              a dictionary as described above.
      """
      if isinstance(value, dict):
        super().__init__(value)
      else:
        super().__init__({"": str(value)})

    @property
    def _jsonRep(self) -> str | dict[str,str]:
        nKeys = len(self.data)
        if nKeys == 0:
            return ""
        elif nKeys == 1 and "" in self.data:
            return str(self.data[""])
        else:
            return self.data

##############################################################################

class OidUser(typing.TypedDict):
    """An OpenID Connect user identity.

    Keys:
        issuer: The issuer URL of the OpenID Connect server that provides
            the identity.
        sub: the "sub" (subject) claim of the user identity at the
            specified OpenID Connect server, or None to refer to all
            user identities at the specified OpenID Connect server.
    """

    issuer: str
    sub: str | None

##############################################################################

class OperationClass(enum.StrEnum):
    """An enumeration of the operation classes that can be access
    controlled.  Note that the EXECUTE_PROCESS and MANAGE_PROCESSES
    operation classes should only be specified in the access control
    rules for the processing server (see Stratos.getProcessingAcrs()
    and Stratos.setProcessingAcrs()), and the GET_RECORD, INSERT_RECORD,
    UPDATE_RECORD and DELETE_RECORD operation classes should only be
    specified in the access control rules for the catalogue server (see
    Stratos.getCataloguesAcrs() and Stratos.setCataloguesAcrs()).
    """

    GET_MAP               = "GetMap"
    GET_FEATURE_INFO      = "GetFeatureInfo"
    GET_FEATURE           = "GetFeature"
    INSERT_FEATURE        = "InsertFeature"
    UPDATE_FEATURE        = "UpdateFeature"
    DELETE_FEATURE        = "DeleteFeature"
    MANAGE_FEATURE_SETS   = "ManageFeatureSets"
    MANAGE_STORED_QUERIES = "ManageStoredQueries"
    MANAGE_STYLES         = "ManageStyles"
    EXECUTE_PROCESS       = "ExecuteProcess"
    MANAGE_PROCESSES      = "ManageProcesses"
    GET_RECORD            = "GetRecord"
    INSERT_RECORD         = "InsertRecord"
    UPDATE_RECORD         = "UpdateRecord"
    DELETE_RECORD         = "DeleteRecord"

##############################################################################

class Quota:
    """A quota.

    Do not instantiate directly.  To get a list of quotas or a specific
    quota, call Stratos.getQuotas() or Stratos.getQuota() respectively.
    To create, update or remove a quota, call Stratos.addQuota(),
    Stratos.updateQuota() or Stratos.removeQuota() respectively.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__id = jsonRep.get("quotaId")
        self.__identityType = QuotaIdentityType(jsonRep.get("identityType"))
        self.__identity = jsonRep.get("identity")
        self.__field = QuotaField(jsonRep.get("field"))

        service = jsonRep.get("service")
        self.__service = service if service else "*"

        operation = jsonRep.get("operation")
        self.__operation = operation if operation else "*"

        self.__granularity = QuotaGranularity(jsonRep.get("granularity"))
        self.__fromDate = datetime.date.fromisoformat(jsonRep.get("fromDate"))
        self.__toDate = datetime.date.fromisoformat(jsonRep.get("toDate"))
        self.__limit = int(jsonRep.get("limit"))
        self.__usage = int(jsonRep.get("usage"))

        warningNumSent = jsonRep.get("warningNumSent")
        self.__warningNumSent = int(warningNumSent) if warningNumSent else 0

    @property
    def id(self) -> str:
        """The ID of this quota."""
        return self.__id

    @property
    def identityType(self) -> QuotaIdentityType:
        """The type of identity that this quota is on."""
        return self.__identityType

    @property
    def identity(self) -> str:
        """The identity (username, role or API key) that this quota
        is on."""
        return self.__identity

    @property
    def field(self) -> QuotaField:
        """The thing being quotad."""
        return self.__field

    @property
    def service(self) -> str:
        """The service (as known by CubeWerx Stratos Analytics) that this
        quota applies to (e.g., "WMS", "WMTS", "WCS", "WFS", "WPS", "CSW"),
        or "*" if the quota applies to all services."""
        return self.__service

    @property
    def operation(self) -> str:
        """The operation (as known by CubeWerx Stratos Analytics) that
        this quota applies to. (e.g., "GetMap", "GetFeature"), or "*"
        if the quota applies to all operations."""
        return self.__operation

    @property
    def granularity(self) -> QuotaGranularity:
        """The granularity of this quota (i.e., what unit of time it
        applies to)."""
        return self.__granularity

    @property
    def fromDate(self) -> datetime.date:
        """The start date (inclusive, in the server's time zone) of the
        current time window of this quota; this will be automatically
        adjusted at the beginning of every unit of time specified by
        the `granularity` property."""
        return self.__fromDate

    @property
    def toDate(self) -> datetime.date:
        """The end date (inclusive, in the server's time zone) of the
        current time window of this quota; this will be automatically
        adjusted at the beginning of every unit of time specified by
        the `granularity` property."""
        return self.__toDate

    @property
    def limit(self) -> int:
        """The limit that this quota imposes."""
        return self.__limit

    @property
    def usage(self) -> int:
        """The current usage (which will be automatically reset at the
        beginning of every unit of time specified by the `granularity`
        property)."""
        return self.__usage

    @property
    def warningNumSent(self) -> int:
        """The highest warning level (typically 1 to 3, or 0 for no
        warning) that the user, role maintainer or API key maintainer
        has been e-mailed about regarding the current usage level; this
        will be automatically reset at the beginning of every unit of
        time specified by the `granularity` property."""
        return self.__warningNumSent

##############################################################################

class QuotaField(enum.StrEnum):
    """An enumeration of the things that a quota can be on.
    """
    N_REQUESTS         = enum.auto()
    DURATION           = enum.auto()
    CPU_SECONDS        = enum.auto()
    N_RESPONSE_BYTES   = enum.auto()
    N_FEATURES         = enum.auto()
    N_POINTS           = enum.auto()
    N_PIXELS           = enum.auto()
    N_NONEMPTY_PIXELS  = enum.auto()
    N_FEATURE_BYTES    = enum.auto()
    N_COVERAGE_BYTES   = enum.auto()
    N_DOWNLOAD_BYTES   = enum.auto()
    N_PROCESSING_UNITS = enum.auto()

##############################################################################

class QuotaGranularity(enum.StrEnum):
    """An enumeration of granularity of a quota (i.e., what unit of time
    it applies to).
    """
    UNBOUNDED    = enum.auto()
    ANNUALLY     = enum.auto()
    SEMIANNUALLY = enum.auto()
    BIMONTHLY    = enum.auto()
    MONTHLY      = enum.auto()
    WEEKLY       = enum.auto()
    DAILY        = enum.auto()

##############################################################################

class QuotaIdentityType(enum.StrEnum):
    """An enumeration of the identity types that a quota can be on.
    """
    USERNAME = enum.auto()
    ROLE     = enum.auto()
    API_KEY  = enum.auto()

##############################################################################

class RequestHistory:
    """A summary of the recent request history.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        periodType = jsonRep.get("periodType")
        self.__periodTypeNoun = periodType.get("noun")
        self.__periodTypeAdjective = periodType.get("adjective")

        self.__periods = []
        for periodJsonRep in jsonRep.get("periods"):
            self.__periods.append(RequestPeriod(periodJsonRep))

        self.__dailyAverages = RequestSummaries(jsonRep.get("dailyAverages"))

    @property
    def periodTypeNoun(self) -> str:
        """The granularity of the time periods, expressed as a noun."""
        return self.__periodTypeNoun

    @property
    def periodTypeAdjective(self) -> str:
        """The granularity of the time periods, expressed as an adjective."""
        return self.__periodTypeAdjective

    @property
    def periods(self) -> list[RequestPeriod]:
        """Summaries per time period, in forward chronological order."""
        return self.__periods

    @property
    def dailyAverages(self) -> RequestSummaries:
        """Daily averages of request activity."""
        return self.__dailyAverages

##############################################################################

class RequestPeriod:
    """A summary of the recent request history for a specific time period.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__fromDate = datetime.date.fromisoformat(jsonRep.get("fromDate"))
        self.__toDate = datetime.date.fromisoformat(jsonRep.get("toDate"))
        self.__summaries = RequestSummaries(jsonRep.get("summaries"))

    @property
    def fromDate(self) -> datetime.date:
        """The start date (inclusive) of the time period."""
        return self.__fromDate

    @property
    def toDate(self) -> datetime.date:
        """The end date (inclusive) of the time period."""
        return self.__toDate

    @property
    def summaries(self) -> RequestSummaries:
        """A summary of the recent request history for this time period."""
        return self.__summaries

##############################################################################

class RequestSummaries:
    """Summaries of requests made and response bytes sent by category.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__coverages = RequestSummary(jsonRep.get("coverages"))
        self.__vectors = RequestSummary(jsonRep.get("vectors"))
        self.__maps = RequestSummary(jsonRep.get("maps"))
        self.__tiles = RequestSummary(jsonRep.get("tiles"))
        self.__offlineDownloads = RequestSummary(
            jsonRep.get("offlineDownloads"))
        self.__other = RequestSummary(jsonRep.get("other"))
        self.__total = RequestSummary(jsonRep.get("total"))

    @property
    def coverages(self) -> RequestSummary:
        """Summary of the coverage data (excluding tile requests)."""
        return self.__coverages

    @property
    def vectors(self) -> RequestSummary:
        """Summary of the vector data (excluding tile requests)."""
        return self.__vectors

    @property
    def maps(self) -> RequestSummary:
        """Summary of the map data (excluding tile requests)."""
        return self.__maps

    @property
    def tiles(self) -> RequestSummary:
        """Summary of the tile data."""
        return self.__tiles

    @property
    def offlineDownloads(self) -> RequestSummary:
        """Summary of the offline downloads."""
        return self.__offlineDownloads

    @property
    def other(self) -> RequestSummary:
        """Summary of all other requests."""
        return self.__other

    @property
    def total(self) -> RequestSummary:
        """Summary of all requests."""
        return self.__total

##############################################################################

class RequestSummary:
    """A summary of requests made and response bytes sent.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__nRequests = jsonRep.get("nRequests")
        self.__nBytes = jsonRep.get("nBytes")

    @property
    def nRequests(self) -> int:
        """The number of requests made."""
        return self.__nRequests

    @property
    def nBytes(self) -> int:
        """The number of response bytes sent."""
        return self.__nBytes

##############################################################################

class Role:
    """A CubeWerx Stratos CwAuth role.

    Roles are a convenient way of assigning tasks to users, allowing
    access to be granted to particular data and/or operations based on
    users' roles rather than having to manage access control rules at a
    per-user level.

    Roles can be assigned to CubeWerx Stratos CwAuth users and OpenID
    Connect users.

    A special built-in "Administrator" role allows full administraton
    access to a Stratos Geospatial Data Server.  This role is
    hardcoded-assigned to the "admin" CwAuth user, but is also
    assignable to other users to grant them full administraton access.
    This role cannot be removed.

    To create a new role, create a new `Role` object (specifying the
    desired role name), set any other desired properties, and call
    Stratos.addOrReplaceRole().

    To change the details of an existing role, fetch the role object
    via Stratos.getRoles() or Stratos.getRole(), update one or more
    properties of that role, and call Stratos.updateRole() to commit
    those changes.

    To remove a role, call Stratos.removeRole().
    """

    def __init__(self, name: str=None, dictionary: dict={}):
        """Create a new `Role` object.

        Args:
            name: The name of the role.  Each role must have a unique name.
                Required unless supplied via the dictionary parameter.
            dictionary: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        if name:
            if not "name" in dictionary: dictionary["name"] = name
        elif not "name" in dictionary:
            raise Exception("name needs to be specified")
        self._dict = dictionary

        # Keep track of the properties that are programmatically changed
        # so that an appropriate patch dictionary can be constructed.
        self.__descriptionChanged = False
        self.__contactChanged = False
        self.__authUsersChanged = False
        self.__oidUsersChanged = False

    @property
    def name(self):
        """The unique name of this role."""
        return self._dict.get("name")

    @property
    def description(self) -> str | None:
        """A brief textual description of this role, or None."""
        return self._dict.get("description")

    @description.setter
    def description(self, value: str | None):
        if value:
            self._dict["description"] = value
        else:
            self._dict.pop("description", None)
        self.__descriptionChanged = True

    @property
    def contactEmail(self) -> str | None:
        """The e-mail address to contact regarding this role, or None."""
        return self._dict.get("contact")

    @contactEmail.setter
    def contactEmail(self, value: str | None):
        if value:
            if not validators.email(value):
                raise ValueError("Invalid emailAddress")
            self._dict["contact"] = value
        else:
            self._dict.pop("contact", None)
        self.__contactChanged = True

    @property
    def isBuiltin(self) -> bool:
        """Is this a non-removable built-in role?"""
        return self._dict.get("builtin", true)

    @property
    def authUsers(self) -> list[str]:
        """The list of CubeWerx Stratos CwAuth user accounts that have
        this role.  These are the usernames only.  To get the full
        `AuthUser` objects (for full names and e-mail addresses, etc.),
        pass this list to Stratos.getAuthUsers().  This list of users
        can be re-specified with a role.authUsers = [...]  assignment.
        However, to add or remove a user to/from the existing list,
        use Role.addAuthUser() or Role.removeAuthUser() rather than
        role.authUsers.append() or role.authUsers.remove()."""
        return self._dict.get("authUsers", [])

    @authUsers.setter
    def authUsers(self, value: list[str]):
        self._dict["authUsers"] = value if value else []
        self.__authUsersChanged = True

    def addAuthUser(self, username: str):
        """Add a CubeWerx Stratos CwAuth user to this role.

        Args:
            username: The username of the CubeWerx Stratos CwAuth user
                account to add this role to.  The specified user must
                exist.  If the user already has this role, this is a
                no-op.
        """
        if username:
            if not self._dict.get("authUsers"): self._dict["authUsers"] = []
            if not username in self._dict["authUsers"]:
                self._dict["authUsers"].append(username)
            self.__authUsersChanged = True

    def removeAuthUser(self, username: str):
        """Remove a CubeWerx Stratos CwAuth user from this role.

        Args:
            username: The username of the CubeWerx Stratos CwAuth user
                account to remove (revoke) this role from.  If the user
                doesn't have this role, this is a no-op.
        """
        if self._dict["authUsers"] and username and \
                username in self._dict["authUsers"]:
            self._dict["authUsers"].remove(username)
            self.__authUsersChanged = True

    @property
    def oidUsers(self) -> list[OidUser]:
        """The list of OpenID Connect user identities that have
        this role.  This list of users can be re-specified with a
        role.oidUsers = [...]  assignment.  However, to add or remove
        a user to/from the existing list, use Role.addOidUser()
        or Role.removeOidUser() rather than role.oidUsers.append()
        or role.oidUsers.remove()."""
        return self._dict.get("oidUsers", [])

    @oidUsers.setter
    def oidUsers(self, value: list[OidUser]):
        self._dict["oidUsers"] = value if value else []
        self.__oidUsersChanged = True

    def addOidUser(self, oidUser: OidUser):
        """Add an OpenID Connect user to this role.

        Args:
            oidUser: the OpenID Connect user identity to add this role
                to.  If the user already has this role, this is a no-op.
        """
        if oidUser:
            if not self._dict.get("oidUsers"): self._dict["oidUsers"] = []
            self._dict["oidUsers"].append(oidUser)
            self.__oidUsersChanged = True

    def removeOidUser(self, oidUser: OidUser):
        """Remove an OpenID Connect user from this role.

        Args:
            oidUser: The OpenID Connect user identity to remove (revoke)
                this role from.  If the user doesn't have this role, this
                is a no-op.
        """
        if self._dict["oidUsers"] and oidUser and \
                oidUser in self._dict["oidUsers"]:
            self._dict["oidUsers"].remove(oidUser)
            self.__oidUsersChanged = True

    @property
    def _patchDict(self) -> dict:
        patch = {}
        if self.__descriptionChanged:
            patch["description"] = self.description
        if self.__contactChanged:
            patch["contact"] = self.contactEmail
        if self.__authUsersChanged:
            patch["authUsers"] = self.authUsers
        if self.__oidUsersChanged:
            patch["oidUsers"] = self.oidUsers
        return patch

##############################################################################

class SourceImage:
    """A source image (called a "scene" in the OGC API) of a coverage layer.

    Do not instantiate directly.  To add source images to a coverage
    layer, call Layer.addSourceImages() or
    SourceImageCollection.addSourceImages().
    """

    def __init__(self, jsonRep: dict, scenesUrl: str, stratos: Stratos):
        """@private"""
        self.__id = jsonRep.get("id")
        if not self.__id:
            raise ValueError("jsonRep missing required 'id' field")

        title = jsonRep.get("title")
        self.__title = str(title) if title else None

        self.__links = jsonRep.get("links", [])
        self.__nominalResM = jsonRep.get("ogc:nominalResM")
        self.__dataCitation = jsonRep.get("ogc:citation")
        self.__hints = SourceImageHints(jsonRep.get("hints", {}))
        self.__isGood = bool(jsonRep.get("isGood", True))
        self.__errorMessage = jsonRep.get("errorMessage")

        self.__wgs84Extent = None
        extentJson = jsonRep.get("extent")
        if extentJson:
            spatialJson = extentJson.get("spatial")
            if spatialJson:
                bboxJson = spatialJson.get("bbox")
                if isinstance(bboxJson, list) and len(bboxJson) > 0:
                    firstBbox = bboxJson[0]
                    if isinstance(firstBbox, list) and len(firstBbox) > 3:
                        self.__wgs84Extent = firstBbox

        self.__sceneUrl = scenesUrl + "/" + quote(self.__id)
        self.__stratos = stratos

    @property
    def id(self) -> str:
        """The ID/name of this source image."""
        return self.__id

    @property
    def title(self) -> str | None:
        """The title of this source image, or None."""
        return self.__title

    @property
    def wgs84Extent(self) -> list | None:
        """The WGS 84 Geographic bounding box of this source image
        ([minLon, minLat, maxLon, maxLat]), or None.  If minLon > maxLon,
        then the bounding box spans the antimeridian."""
        return self.__wgs84Extent

    @property
    def nominalResM(self) -> float | None:
        """The nominal resolution of this source image in metres, or None."""
        return self.__nominalResM

    @property
    def dataCitation(self) -> str | None:
        """A citation for the source of this source image, or None."""
        return self.__dataCitation

    @property
    def isGood(self) -> bool:
        """If false, this source image is unuseable for the reason
        provided by the `errorMessage` property.  Consider adjusting
        its hints or removing it."""
        return self.__isGood

    @property
    def errorMessage(self) -> str | None:
        """An error message describing why the source image is unuseable,
        or None."""
        return self.__errorMessage

    @property
    def hints(self) -> SourceImageHints:
        """Hints to help the Stratos Geospatial Data Server interpret
        this source image.  If these hints are changed
        programmatically, `commitHintChanges` must be called to commit
        these changes to the Stratos Geospatial Data Server."""
        return self.__hints

    def getThumbnailImage(self, maxWidth: int | None = None,
                          maxHeight: int | None = None) -> Image.Image:
        """Return a thumbnail image for this source image, or None if
        no thumbnail image is available for this source image.

        Args:
            maxWidth: The preferred maximum width of the thumbnail
                image, or None to let the server decide.
            maxHeight: The preferred maximum height of the thumbnail
                image, or None to let the server decide.

        Returns:
            A thumbnail image for this source image, or None if
            no thumbnail image is available for this source image.
        """
        # Determine the URL of the thumbnail image.
        thumbnailEndpointUrl = None
        for link in self.__links:
            if link.get("rel") == "thumbnail":
                thumbnailEndpointUrl = link.get("href")
                break

        if not thumbnailEndpointUrl:
            return None

        # Fetch and return the thumbnail image.
        # (Note that we can't simply return the URL of the thumbnail
        # image, because it might require an authorized user to access.)
        params = {}
        if maxWidth and int(maxWidth) > 0:
            params["maxWidth"] = int(maxWidth)
        if maxHeight and int(maxHeight) > 0:
            params["maxHeight"] = int(maxHeight)
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        response = requests.get(thumbnailEndpointUrl,
            headers=requestHeaders, params=params)
        ServerException.raise_for_status(response)
        return Image.open(io.BytesIO(response.content))

    def commitHintChanges(self, updateTiles: bool = False):
        """Commit to the Stratos Geospatial Data Server any changes that
        were programmatically made to the hints of this source image.
        Note that this may change the values of some of the properties
        of the source image, including its ID and whether or not it's
        considered a good source image.

        Args:
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        """
        if self.__hints._changed:
            requestHeaders = {
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            params = {}
            params["updateTiles"] = bool(updateTiles)
            response = requests.patch(self.__sceneUrl, headers=requestHeaders,
                params=params, json=self.__hints._patchDict)
            ServerException.raise_for_status(response)
            self.__hints._clearChangedFlags()

##############################################################################

class SourceImageCollection:
    """A source-image collection (called a "group" in the CubeWerx
    extensions to the OGC API) of a coverage layer.

    Do not instantiate directly.  To add a source-image collection to a
    coverage layer, call Layer.addCollection().
    """

    def __init__(self, jsonRep: dict, groupsUrl: str, stratos: Stratos):
        """@private"""
        self.__initFromJsonRep(jsonRep)
        self.__groupUrl = groupsUrl + "/" + quote(self.__id)
        self.__stratos = stratos

    def __initFromJsonRep(self, jsonRep: dict):
        self.__id = jsonRep.get("id")
        if not self.__id:
            raise ValueError("jsonRep missing required 'id' field")

        titleJson = jsonRep.get("title")
        self.__title = MultilingualString(titleJson) if titleJson else None

        descriptionJson = jsonRep.get("description")
        self.__description = MultilingualString(descriptionJson) \
            if descriptionJson else None

        referenceOnlyPath = jsonRep.get("referenceOnlyPath")
        self.__referenceOnlyPath = str(referenceOnlyPath) \
            if referenceOnlyPath else None

        self.__defaultHints = SourceImageHints(jsonRep.get("defaultHints", {}))

        nSourceImages = jsonRep.get("nScenes")
        self.__nSourceImages = int(nSourceImages) if nSourceImages else 0

        nBad = jsonRep.get("nBad")
        self.__nBad = int(nBad) if nBad else 0

    @property
    def id(self) -> str:
        """The ID/name of this source-image collection."""
        return self.__id

    @property
    def title(self) -> MultilingualString | None:
        """The title of this source-image collection, or None.  Setting
        this (or clearing it by setting it to None) will automatically
        update the server."""
        return self.__title

    @title.setter
    def title(self, title: str | MultilingualString | None):
        if isinstance(title, str):
            title = MultilingualString(title)

        requestHeaders = {}
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        patchDict = { "title": (title._jsonRep if title else None) }
        response = requests.patch(self.__groupUrl,
            headers=requestHeaders, json=patchDict)
        ServerException.raise_for_status(response)
        self.__title = title

    @property
    def description(self) -> MultilingualString | None:
        """A brief textual description of this source-image collection,
        or None.  Setting this (or clearing it by setting it to None)
        will automatically update the server."""
        return self.__description

    @description.setter
    def description(self, description: str | MultilingualString | None):
        if isinstance(description, str):
            description = MultilingualString(description)

        requestHeaders = {}
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        patchDict = { "description":
            (description._jsonRep if description else None) }
        response = requests.patch(self.__groupUrl,
            headers=requestHeaders, json=patchDict)
        ServerException.raise_for_status(response)
        self.__description = description

    @property
    def isReferenceOnly(self) -> bool:
        """If True, this is a reference-only source-image collection.
        Source images can't be added to or removed from such collections
        using this API, and it's assumed that the directory specified by
        the `referenceOnlyPath` parameter is maintained by some other
        means (e.g., direct upload or filesystem copy).  Whenever source
        images are added to, removed from or adjusted in this directory,
        the source-image collection should be rescanned by calling
        `rescan`."""
        return bool(self.__referenceOnlyPath)

    @property
    def referenceOnlyPath(self) -> str | None:
        """The local directory (beginning with a '/'), remote HTTP
        directory (beginning with an 'https://') or remote S3 directory
        (beginning with an 's3://') that contains the source images
        of this reference-only source-image collection, or None if
        this isn't a reference-only source-image collection."""
        return self.__referenceOnlyPath

    @property
    def defaultHints(self) -> SourceImageHints:
        """A set of default hints that are applied to all new source
        images that are added to this collection.  If these hints are
        changed programmatically, `commitDefaultHintChanges` must be
        called to commit these changes to the Stratos Geospatial Data
        Server."""
        return self.__defaultHints

    @property
    def nSourceImages(self) -> int:
        """The number of source images that are in this collection,
        including bad source images."""
        return self.__nSourceImages

    @property
    def nBad(self) -> int:
        """The number of bad source images that are in this collection.
        Bad source images will not be rendered.  A bad source image may
        be fixed by adjusting its hints appropriately and calling
        badSourceImage.commitHintChanges()."""
        return self.__nBad

    def getSourceImages(self, includeGood: bool = True,
                        includeBad: bool = False) -> list[SourceImage]:
        """Return a list of all of the source images in this collection.

        Args:
            includeGood: Whether or not to include good source images.
            includeBad: Whether or not to include bad source images.

        Returns:
            A list of the source images in this collection.
        """
        # TODO: This code is almost identical to Layer.getSourceImages().
        # What's the best way to factor this out?

        # Fetch the .../groups/{groupId}/scenes document.
        scenesUrl = self.__groupUrl + "/scenes"
        requestHeaders = {
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {
            "includeGood": includeGood,
            "includeBad": includeBad,
            "limit": 1000000,
        }
        response = requests.get(scenesUrl, headers=requestHeaders,
            params=params)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Parse the scenes into SourceImage objects.
        sourceImages = []
        scenesJson = responseJson.get("scenes")
        if isinstance(scenesJson, list):
            for sceneJson in scenesJson:
                sourceImage = SourceImage(sceneJson, scenesUrl, self.__stratos)
                if sourceImage: sourceImages.append(sourceImage)

        return sourceImages

    def addSourceImages(self, filePaths: list[str],
                        hints: SourceImageHints = None,
                        updateTiles: bool = False) -> list[SourceImage]:
        """Add one or more source images to this collection.  This can only
        be done if the collection is not `isReferenceOnly`.

        Args:
            filePaths: The fully-qualified local file paths to the source
                image(s) to be added, including any necessary auxilliary
                files.  Alternatively, a ZIP file containing the source
                image(s) to be added can be specified, as long as it meets
                the following requirements: a) it's the only specified
                file, b) it has a '.zip' suffix, and c) it consists only
                of files or of exactly one directory whose contents exist
                only of files.
            hints: Hints to help the Stratos Geospatial Data Server
                interpret the source images, or None.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        Returns:
            A list of the source images that were added.  Note that some
            of the source images may be marked as bad, and should be
            adjusted or removed.
        """
        if self.isReferenceOnly:
            raise CwException("source images cannot be added to "
                              "reference-only collections")

        # TODO: This code is almost identical to Layer.addSourceImages().
        # What's the best way to factor this out?

        nFiles = len(filePaths)
        if nFiles < 1:
            # No source images were specified.  Trivial return.
            return []
        elif nFiles == 1 and filePaths[0].endswith('.zip'):
            # A ZIP file was specified.  Open it.
            zipFile = os.open(filePaths[0], 'rb')
        else:
            # One or more source-image files were specified.  Package
            # them together into a temporary ZIP archive.
            zipFile = tempfile.TemporaryFile(suffix='.zip')
            zipArchive = zipfile.ZipFile(zipFile, "x")
            for filePath in filePaths:
                filename = os.path.basename(filePath)
                if filename:
                    zipArchive.write(filePath, filename)
            zipArchive.close()
            zipFile.seek(0)

        # Make an HTTP POST request to the groups/{groupId}/scenes endpoint.
        scenesUrl = self.__groupUrl + "/scenes"
        requestHeaders = {
            "Accept": "application/json",
            "Content-Type": "application/zip"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        if hints is not None:
             params.update(hints._dict)
        params["updateTiles"] = bool(updateTiles)
        response = requests.post(scenesUrl, headers=requestHeaders,
                                 params=params, data=zipFile)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        # Close (and remove) the temporary ZIP file.
        zipFile.close()

        # Read the resulting SourceImage objects from the response.
        sourceImages = []
        if isinstance(responseJson, list):
            for sceneJson in responseJson:
                sourceImage = SourceImage(sceneJson, scenesUrl, self.__stratos)
                if sourceImage: sourceImages.append(sourceImage)

        # Update the nRegistered and nBad counts.  Rather than re-fetch
        # the group from the sever to get the updated numbers, simply
        # update the counts based on the resulting SourceImage objects.
        self.__nSourceImages += len(sourceImages)
        for sourceImage in sourceImages:
            if not sourceImage.isGood:
                self.__nBad += 1

        # We're done!
        return sourceImages

    def removeSourceImages(self, sourceImages: list[SourceImage|str],
                           updateTiles: bool = False):
        """Remove one or more source images from this collection.  This
        can only be done if the collection is not `isReferenceOnly`.

        Args:
            sourceImages: The source-image objects or IDs to remove.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                `tileUpdateProgress` property.  If possible, further
                manipulation of the data, styles or hints of this layer
                should be avoided until the tile update is complete.
        """
        if self.isReferenceOnly:
            raise CwException("source images cannot remove from "
                              "reference-only collections")

        # Make an HTTP DELETE request to each specified scene.
        # Pass updateTiles=false to all but the last one.
        scenesUrl = self.__groupUrl + "/scenes"
        scenesUrl = self.__collectionUrl + "/scenes"
        nSourceImages = len(sourceImages)
        for i in range(nSourceImages):
            sourceImage = sourceImages[i]
            sceneId = sourceImage.id if isinstance(sourceImage, SourceImage) \
                else sourceImage
            sceneUrl = scenesUrl + "/" + sceneId

            if i < nSourceImages-1:
                params = { "updateTiles": false }
            else:
                params = { "updateTiles": bool(updateTiles) }

            response = requests.delete(sceneUrl,
                headers=self.__stratos.commonRequestHeaders, params=params)
            ServerException.raise_for_status(response)

    def commitDefaultHintChanges(self):
        """Commit to the Stratos Geospatial Data Server any changes
        that were programmatically made to the default hints of this
        source-image collection.
        """
        if self.__defaultHints._changed:
            requestHeaders = {
                "Accept": "application/json"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            jsonPatch = {
                "defaultHints": self.__defaultHints._patchDict
            }
            response = requests.patch(self.__groupUrl, headers=requestHeaders,
                json=jsonPatch)
            ServerException.raise_for_status(response)
            self.__defaultHints._clearChangedFlags()

    def rescan(self):
        """Rescan the source images for this collection.  New source
        images that are found will be registered, source images that
        no longer exist will be unregistered, and an attempt will be
        made to re-register any source images marked as bad.
        Typically only useful for reference-only collections.
        """
        requestHeaders = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        patchDict = { "rescan": True }
        response = requests.patch(self.__groupUrl,
            headers=requestHeaders, json=patchDict)
        ServerException.raise_for_status(response)
        responseJson = response.json()
        self.__initFromJsonRep(response.json())

##############################################################################

class SourceImageHints:
    """Hints to help the Stratos Geospatial Data Server interpret a
    source image.

    To specify hints when adding source images to a layer, create a new
    `SourceImageHints` object, set the relevant properties, and pass this
    object to Layer.addSourceImages() or
    SourceImageCollection.addSourceImages().

    To specify or adjust hints of an existing source image, get the
    `SourceImageHints` object using SourceImage.hints, set or adjust
    the relevant properties, and commit the changes by calling
    SourceImage.commitHintChanges().  Note that this may change the
    values of some of the properties of the source image, including
    its ID and whether or not it's considered a good source image.
    """

    def __init__(self, dictionary: dict={}):
        """Create a new `SourceImageHints` object.

        Args:
            dictionary: A dictionary supplying properties.  Do not specify;
                for internal use only.
        """
        self._dict = dictionary

        # Keep track of the properties that are programmatically changed
        # so that an appropriate patch dictionary can be constructed.
        self.__dataCoordSysChanged = False
        self.__dataCitationChanged = False
        self.__dataTimeChanged = False
        self.__nullColor1Changed = False
        self.__nullColor2Changed = False
        self.__nullFuzzChanged = False
        self.__rasterNBitsChanged = False

    @property
    def _changed(self) -> bool:
        return (self.__dataCoordSysChanged or
            self.__dataCitationChanged or
            self.__dataTimeChanged or
            self.__nullColor1Changed or
            self.__nullColor2Changed or
            self.__nullFuzzChanged or
            self.__rasterNBitsChanged)

    @property
    def dataCoordSys(self) -> str | None:
        """The coordinate system that the data is in."""
        return self._dict.get("dataCoordSys")

    @dataCoordSys.setter
    def dataCoordSys(self, value: str | None):
        if value:
            self._dict["dataCoordSys"] = str(value)
        else:
            self._dict.pop("dataCoordSys", None)
        self.__dataCoordSysChanged = True

    @property
    def dataCitation(self) -> str | None:
        """A citation for the source of the data."""
        return self._dict.get("dataCitation")

    @dataCitation.setter
    def dataCitation(self, value: str | None):
        if value:
            self._dict["dataCitation"] = str(value)
        else:
            self._dict.pop("dataCitation", None)
        self.__dataCitationChanged = True

    @property
    def dataTime(self) -> datetime.datetime | None:
        """The date (and possibly time) that this data was captured."""
        dataTimeStr = self._dict.get("dataTime")
        return datetime.date.fromisoformat(dataTimeStr) \
            if dataTimeStr else None

    @dataTime.setter
    def dataTime(self, value: datetime.datetime | None):
        if value:
            self._dict["dataTime"] = value.isoformat()
        else:
            self._dict.pop("dataTime", None)
        self.__dataTimeChanged = True

    @property
    def nullColor1(self) -> datetime.datetime | None:
        """The color in the source images that represents the NULL color,
        expressed as a hexadecimal red-green-blue color value."""
        return self._dict.get("nullColor1")

    @nullColor1.setter
    def nullColor1(self, value: str | None):
        if value:
            self._dict["nullColor1"] = str(value)
        else:
            self._dict.pop("nullColor1", None)
        self.__nullColor1Changed = True

    @property
    def nullColor2(self) -> datetime.datetime | None:
        """A second color in the source images that represents the NULL
        color, expressed as a hexadecimal red-green-blue color value."""
        return self._dict.get("nullColor2")

    @nullColor2.setter
    def nullColor2(self, value: str | None):
        if value:
            self._dict["nullColor2"] = str(value)
        else:
            self._dict.pop("nullColor2", None)
        self.__nullColor2Changed = True

    @property
    def nullFuzz(self) -> int | None:
        """A fuzz factor to apply when detecting NULL colors (useful for
        processing lossy data); typically in the range of 0-255 for RGB
        or greyscale data."""
        return self._dict.get("nullFuzz")

    @nullFuzz.setter
    def nullFuzz(self, value: int | None):
        if value is not None and int(value) > 0:
            self._dict["nullFuzz"] = int(value)
        else:
            self._dict.pop("nullFuzz", None)
        self.__nullFuzzChanged = True

    @property
    def rasterNBits(self) -> int | None:
        """The number of significant bits per channel in the source data."""
        return self._dict.get("rasterNBits")

    @rasterNBits.setter
    def rasterNBits(self, value: int | None):
        if value is not None and int(value) > 0:
            self._dict["rasterNBits"] = int(value)
        else:
            self._dict.pop("rasterNBits", None)
        self.__rasterNBitsChanged = True

    def clear(self):
        """Remove all hints."""
        if self.dataCoordSys: self.__dataCoordSysChanged = True
        if self.dataCitation: self.__dataCitationChanged = True
        if self.dataTime: self.__dataTimeChanged = True
        if self.nullColor1: self.__nullColor1Changed = True
        if self.nullColor2: self.__nullColor2Changed = True
        if self.nullFuzz: self.__nullFuzzChanged = True
        if self.rasterNBits: self.__rasterNBitsChanged = True
        self._dict.clear()

    @property
    def _patchDict(self) -> dict:
        patch = {}
        if self.__dataCoordSysChanged:
            patch["dataCoordSys"] = self.dataCoordSys
        if self.__dataCitationChanged:
            patch["dataCitation"] = self.dataCitation
        if self.__dataTimeChanged:
            patch["dataTime"] = self.dataTime
        if self.__nullColor1Changed:
            patch["nullColor1"] = self.nullColor1
        if self.__nullColor2Changed:
            patch["nullColor2"] = self.nullColor2
        if self.__nullFuzzChanged:
            patch["nullFuzz"] = self.nullFuzz
        if self.__rasterNBitsChanged:
            patch["rasterNBits"] = self.rasterNBits
        return patch

    def _clearChangedFlags(self):
        self.__dataCoordSysChanged = False
        self.__dataCitationChanged = False
        self.__dataTimeChanged = False
        self.__nullColor1Changed = False
        self.__nullColor2Changed = False
        self.__nullFuzzChanged = False
        self.__rasterNBitsChanged = False

##############################################################################

class SpatialRelation(enum.StrEnum):
    """An enumeration of geometry spatial-relation types.
    """

    EQUALS     = "equals"
    DISJOINT   = "disjoint"
    TOUCHES    = "touches"
    WITHIN     = "within"
    OVERLAPS   = "overlaps"
    CROSSES    = "crosses"
    INTERSECTS = "intersects"
    CONTAINS   = "contains"
    BBOX       = "bbox"

    # soon to be canonical?...
    # EQUALS     = "S_EQUALS"
    # DISJOINT   = "S_DISJOINT"
    # TOUCHES    = "S_TOUCHES"
    # WITHIN     = "S_WITHIN"
    # OVERLAPS   = "S_OVERLAPS"
    # CROSSES    = "S_CROSSES"
    # INTERSECTS = "S_INTERSECTS"
    # CONTAINS   = "S_CONTAINS"
    # BBOX       = "BBOX"

##############################################################################

class Stats:
    """System statistics.
    """

    def __init__(self, jsonRep: dict):
        """@private"""
        self.__nActiveUsers = jsonRep.get("nActiveUsers")
        self.__loadAverage = tuple(jsonRep.get("loadAverage"))
        self.__nCpus = jsonRep.get("nCpus")
        memory = jsonRep.get("memory")
        self.__memoryUsed = memory.get("used") if memory else -1
        self.__memoryTotal = memory.get("total") if memory else -1

    @property
    def nActiveUsers(self) -> list[int]:
        """The number of unique users that have used the product per
        specified time period, for the last specified number of time
        periods, in forward chronological order.  For example, if the
        request was for nPeriods=24 and nSecondsPerPeriod=3600, then
        this list would contain 24 items with the last item indicating
        the number of unique users that have used the product within
        the past hour and the previous item indicating the number of
        unique users that have used the product during the hour before
        that, etc."""
        return self.__nActiveUsers

    @property
    def loadAverage(self) -> tuple[float, float, float]:
        """The current load average of the system over the last 1, 5 and
        15 minutes, respectively.  For a normalized system load, divide
        by the number of CPUs on the system."""
        return self.__loadAverage

    @property
    def nCpus(self) -> float:
        """The number of CPUs on the system."""
        return self.__nCpus

    @property
    def memoryUsed(self) -> int:
        """The number of bytes of physical memory on the system that are
        currently being used."""
        return self.__memoryUsed

    @property
    def memoryTotal(self) -> int:
        """The number of bytes of physical memory on the system."""
        return self.__memoryTotal

##############################################################################

class Style:
    """An available style for a layer.
    """

    def __init__(self, jsonRep: dict, stylesUrl: str, canBeUpdated: bool,
                 stratos: Stratos):
        """@private"""
        self.__id = jsonRep.get("id")

        title = jsonRep.get("title")
        self.__title = str(title) if title else None

        self.__sld11XmlStr = None
        self.__sld11UserStyleXmlStr = None

        self.__styleUrl = stylesUrl + "/" + quote(self.__id)
        self.__canBeUpdated = canBeUpdated
        self.__stratos = stratos

    @property
    def id(self) -> str:
        """The ID/name of this style."""
        return self.__id

    @property
    def title(self) -> str | None:
        """The title of this style, or None."""
        return self.__title

    @property
    def sld11XmlStr(self) -> str:
        """The definition of this style as an SLD 1.1 SymLayerSet XML
        element."""
        if not self.__sld11XmlStr:
            requestHeaders = {
                "Accept": "application/vnd.ogc.sld+xml; version=1.1"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.get(self.ogcApiUrl, headers=requestHeaders)
            ServerException.raise_for_status(response)
            self.__sld11XmlStr = response.text

        return self.__sld11XmlStr

    @property
    def sld11UserStyleXmlStr(self) -> str:
        """The definition of this style as an SLD 1.1 UserStyle XML
        element."""
        if not self.__sld11UserStyleXmlStr:
            requestHeaders = {
                "Accept": "application/vnd.ogc.sld+xml; version=1.1; styleOnly=true"
            }
            requestHeaders.update(self.__stratos.commonRequestHeaders)
            response = requests.get(self.ogcApiUrl, headers=requestHeaders)
            ServerException.raise_for_status(response)
            self.__sld11UserStyleXmlStr = response.text

        return self.__sld11UserStyleXmlStr

    @property
    def canBeUpdated(self) -> bool:
        """Whether or not the definition of this style can be changed."""
        return self.__canBeUpdated

    @property
    def ogcApiUrl(self) -> str:
        """The OGC API URL of this layer-specific style."""
        return self.__styleUrl

    def update(self, sld11UserStyleXmlStr: str, updateTiles: bool = False):
        """Updates the definition of this style.  The style is immediately
        updated on the Stratos Geospatial Data Server.  This can
        only be done if `canBeUpdated`.

        Args:
            sld11UserStyleXmlStr: An SLD 1.1 UserStyle element containing
                the new style definition.  The UserStyle <Name> within this
                definition must match the ID of the style.
            updateTiles: Whether or not the data and map tiles of the
                layer should be updated.  If specified as True, the
                progress of the tile update can be monitored with the
                layer's `tileUpdateProgress` property.  If possible,
                further manipulation of the data, styles or hints of this
                layer should be avoided until the tile update is complete.

        """
        if not self.canBeUpdated:
            raise CwException("this style (%s) can't be updated" % this.id)

        requestHeaders = {
            "Content-Type": "application/vnd.ogc.sld+xml; version=1.1",
            "Accept": "application/json"
        }
        requestHeaders.update(self.__stratos.commonRequestHeaders)
        params = {}
        params["updateTiles"] = bool(updateTiles)
        response = requests.put(self.ogcApiUrl, headers=requestHeaders,
            params=params, data=sld11UserStyleXmlStr)
        ServerException.raise_for_status(response)
        responseJson = response.json()

        self.__id = responseJson.get("id")
        self.__title = responseJson.get("title")
        if not self.__title: self.__title = None
        self.__sld11XmlStr = None
        self.__sld11UserStyleXmlStr = None

##############################################################################

class Watermark:
    """A watermark to apply for map layer rendering.
    """

    def __init__(self, urlOrFilePath: str | None = None,
                 location: WatermarkLocation = "WatermarkLocation.TILED",
                 opacity: float = 1.0):
        """Create a new watermark.

        Args:
            urlOrFilePath: A URL or local file path (absolute or relative
                to the server URL or directory) to an image to use as
                the watermark, or None (but then required to be set via
                the property).  PNG is preferred, but JPEG, GIF and TIFF
                will also work.
            location: Where the watermark should be applied in the
                rendered map.  The only location suitable for tiled maps
                is TILED.
            opacity: The opacity (0...1) of the watermark (subject to the
                opacity of the image itself).
        """
        self.__urlOrFilePath = urlOrFilePath if urlOrFilePath else None
        self.__location = location
        self.__opacity = min(max(float(opacity), 0.0), 1.0)

    @staticmethod
    def _fromJsonRep(jsonRep: dict):
        urlOrFilePath = jsonRep.get("urlOrFilePath")
        try:
            location = WatermarkLocation(jsonRep.get("location", "tiled"))
        except ValueError as e:
            location = WatermarkLocation.TILED # rather than failing
        opacity = min(max(jsonRep.get("opacity", 1.0), 0.0), 1.0)
        return Watermark(urlOrFilePath, location, opacity)

    @property
    def urlOrFilePath(self) -> str | None:
        """A URL or local file path (absolute or relative to the server
        URL or directory) to an image to use as the watermark, or None.
        PNG is preferred, but JPEG, GIF and TIFF will also work."""
        return self.__urlOrFilePath

    @urlOrFilePath.setter
    def urlOrFilePath(self, value: str | None):
        self.__urlOrFilePath = value if value else None

    @property
    def location(self) -> WatermarkLocation:
        """Where the watermark should be applied in the rendered map.
        The only location suitable for tiled maps is TILED."""
        return self.__location

    @location.setter
    def location(self, value: WatermarkLocation):
        self.__location = value if value else WatermarkLocation.TILED

    @property
    def opacity(self) -> float:
        """The opacity (0...1) of the watermark (subject to the
        opacity of the image itself)."""
        return self.__opacity

    @opacity.setter
    def opacity(self, value: float):
        self.__opacity = min(max(float(value), 0.0), 1.0)

    @property
    def _jsonRep(self) -> dict:
        jsonRep = {}
        if self.__urlOrFilePath:
            jsonRep["urlOrFilePath"] = self.__urlOrFilePath
        if self.__location != WatermarkLocation.TILED:
            jsonRep["location"] = str(self.__location)
        if self.__opacity != 1.0:
            jsonRep["opacity"] = self.__opacity
        return jsonRep

    def __repr__(self):
        return repr(self._jsonRep)

##############################################################################

class WatermarkLocation(enum.StrEnum):
    """An enumeration of where watermarks can be applied in rendered maps.
    """

    NOWHERE       = "nowhere"
    TOP_LEFT      = "top left"
    TOP_CENTER    = "top center"
    TOP_RIGHT     = "top right"
    CENTER_LEFT   = "center left"
    CENTER        = "center"
    CENTER_RIGHT  = "center right"
    BOTTOM_LEFT   = "bottom left"
    BOTTOM_CENTER = "bottom center"
    BOTTOM_RIGHT  = "bottom right"
    TILED         = "tiled"

##############################################################################

class CwException(Exception):
    """The base class for all CubeWerx-specific exceptions.
    """
    pass

class LoginException(CwException):
    """The base class for all exceptions related to logging in to a
    CubeWerx Stratos Geospatial Data Server.
    """
    pass

class NotAStratosException(LoginException):
    """Raised when an attempt is made to connect to a URL that doesn't
    appear to be a CubeWerx Stratos Geospatial Data Server.
    """
    def __init__(self):
        """@private"""
        super().__init__("Not a CubeWerx Stratos Geospatial Data Server")

class IncompatibleStratosVersionException(LoginException):
    """Raised when an attempt is made to connect to a CubeWerx Stratos
    Geospatial Data Server whose version number is incompatible with this
    Python package.
    """
    def __init__(self, version: str, requiredVersion: str):
        """@private"""
        parentheticalVersion = ("(%s) " % version) if version else ""
        super().__init__("Version number of CubeWerx Stratos Geospatial "
            "Data Server %sis too low; must be a %s" %
            (parentheticalVersion, requiredVersion))

class NotAnAuthServerException(LoginException):
    """Raised when the specified CubeWerx Stratos Authentication Server
    URL doesn't seem to point to a CubeWerx Stratos Authentication
    Server.
    """
    def __init__(self):
        """@private"""
        super().__init__("Not a CubeWerx Stratos Authentication Server")

class AuthServerVersionTooLowException(LoginException):
    """Raised when an attempt is made to connect to a CubeWerx Stratos
    Authentication Server whose version number is too low.
    """
    def __init__(self, version: str, minVersion: str):
        """@private"""
        parentheticalVersion = ("(%s) " % version) if version else ""
        super().__init__("Version number of CubeWerx Stratos Authentication "
            "Server %sis too low; must be at least %s" %
            (parentheticalVersion, minVersion))

class InvalidCredentialsException(LoginException):
    """Raised when an invalid CubeWerx Stratos username or password is
    provided.
    """
    def __init__(self):
        """@private"""
        super().__init__("Invalid username or password")

class NotAdministratorException(LoginException):
    """Raised when the provided CubeWerx Stratos username and password
    is accepted, but the specified user doesn't have Administrator
    privileges.
    """
    def __init__(self, username: str):
        """@private"""
        super().__init__('User "%s" does not have Administrator privileges' %
            username)

class LoginAttemptsTooFrequentException(LoginException):
    """Raised when login attempts to the specified username are being made
    too frequently.  Wait a few seconds and try again.
    """
    def __init__(self):
        super().__init__("Login attempts are being made too frequently")

class NoMoreSeatsException(LoginException):
    """Raised when no more seats are available for the specified username.
    Not applicable for most servers.
    """
    def __init__(self, username: str):
        """@private"""
        super().__init__('No more seats are available for user "%s"' %
            username)

class ServerException(CwException):
    """Raised when the CubeWerx Stratos Geospatial Data Server returns an
    error.  Provides a detailed error report.
    """
    def __init__(self, httpError: requests.exceptions.HTTPError,
            title: str | None, httpStatus: int, details: list[str],
            moreInfoUrl: str | None):
        """@private"""
        self.__httpError = httpError
        self.__title = title
        self.__httpStatus = httpStatus
        self.__details = details
        self.__moreInfoUrl = moreInfoUrl

    @property
    def httpError(self) -> requests.exceptions.HTTPError:
        """The HTTPError object describing the error response."""
        return self.__httpError

    @property
    def title(self) -> str | None:
        """The title of the error report, or None."""
        return self.__title

    @property
    def httpStatus(self) -> int:
        """The HTTP status code of the error."""
        return self.__httpStatus

    @property
    def details(self) -> list[str]:
        """An array of strings describing the error, from most general
        to most specific."""
        return self.__details

    @property
    def moreInfoUrl(self) -> str | None:
        """A URL that provides more information about the error and the
        request that triggered it, or None."""
        return self.__moreInfoUrl

    def __str__(self):
        exceptionText = str(self.httpError)
        for detail in self.details:
            exceptionText += ("\nDetail: %s" % detail)
        if self.moreInfoUrl:
            exceptionText += ('\nSee "%s" for more information' %
                              self.moreInfoUrl)
        return exceptionText

    @staticmethod
    def raise_for_status(response: requests.Response):
        """@private"""
        httpError = None
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            httpError = e

        if httpError:
            contentType = response.headers['Content-Type']
            if contentType == "application/problem+json":
                responseJson = response.json()
                title = responseJson.get("title")
                httpStatus = responseJson.get("status")
                if not httpStatus: httpStatus = response.status_code
                details = []
                detailsObjs = responseJson.get("details")
                if detailsObjs:
                    for detailObj in detailsObjs:
                        detail = detailObj.get("description")
                        if detail: details.append(detail)
                else:
                    detail = responseJson.get("detail")
                    if detail: details.append(detail)
                instanceUrl = responseJson.get("instance")

                raise ServerException(httpError, title, httpStatus,
                    details, instanceUrl)
            else:
                raise httpError

