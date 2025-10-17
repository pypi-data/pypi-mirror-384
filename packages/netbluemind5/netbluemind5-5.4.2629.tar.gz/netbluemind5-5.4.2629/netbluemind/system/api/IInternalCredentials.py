#
#  BEGIN LICENSE
#  Copyright (c) Blue Mind SAS, 2012-2016
#
#  This file is part of BlueMind. BlueMind is a messaging and collaborative
#  solution.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of either the GNU Affero General Public License as
#  published by the Free Software Foundation (version 3 of the License).
#
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  See LICENSE.txt
#  END LICENSE
#
import requests
import json
from netbluemind.python import serder
from netbluemind.python.client import BaseEndpoint

IInternalCredentials_VERSION = "5.4.2629"


class IInternalCredentials(BaseEndpoint):
    def __init__(self, apiKey, url, domainUid):
        self.url = url
        self.apiKey = apiKey
        self.base = url + '/credentials/{domainUid}'
        self.domainUid_ = domainUid
        self.base = self.base.replace('{domainUid}', domainUid)

    def addUserCredential(self, userUid, credential):
        postUri = "/user/{userUid}"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{userUid}", userUid)
        from netbluemind.system.api.Credential import Credential
        from netbluemind.system.api.Credential import __CredentialSerDer__
        __data__ = __CredentialSerDer__().encode(credential)
        __encoded__ = json.dumps(__data__)
        queryParams = {}

        response = requests.put(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        return self.handleResult__(None, response)

    def addUserCredentials(self, userUid, credentials):
        postUri = "/user/{userUid}/_credentials"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{userUid}", userUid)
        from netbluemind.system.api.Credential import Credential
        from netbluemind.system.api.Credential import __CredentialSerDer__
        __data__ = serder.ListSerDer(
            __CredentialSerDer__()).encode(credentials)
        __encoded__ = json.dumps(__data__)
        queryParams = {}

        response = requests.put(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        return self.handleResult__(None, response)

    def getDomainCredentialById(self, credentialId):
        postUri = "/{credentialId}"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{credentialId}", credentialId)
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        return self.handleResult__(serder.STRING, response)

    def getObfuscatedUserCredentials(self, userUid):
        postUri = "/user/{userUid}"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{userUid}", userUid)
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        from netbluemind.system.api.Credential import Credential
        from netbluemind.system.api.Credential import __CredentialSerDer__
        from netbluemind.core.api.ListResult import ListResult
        from netbluemind.core.api.ListResult import __ListResultSerDer__
        return self.handleResult__(__ListResultSerDer__(__CredentialSerDer__()), response)

    def getUserCredentials(self, userUid):
        postUri = "/user/{userUid}/plain"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{userUid}", userUid)
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        from netbluemind.system.api.Credential import Credential
        from netbluemind.system.api.Credential import __CredentialSerDer__
        return self.handleResult__(serder.ListSerDer(__CredentialSerDer__()), response)

    def removeUserCredential(self, userUid, credentialId):
        postUri = "/user/{userUid}/{credentialId}"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{userUid}", userUid)
        postUri = postUri.replace("{credentialId}", credentialId)
        queryParams = {}

        response = requests.delete(self.base + postUri, params=queryParams, verify=False, headers={
                                   'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IInternalCredentials_VERSION}, data=__encoded__)
        return self.handleResult__(None, response)
