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

IExternalSystem_VERSION = "5.4.2629"


class IExternalSystem(BaseEndpoint):
    def __init__(self, apiKey, url):
        self.url = url
        self.apiKey = apiKey
        self.base = url + '/system/external'

    def getExternalSystem(self, systemIdentifier):
        postUri = "/{systemIdentifier}"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{systemIdentifier}", systemIdentifier)
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IExternalSystem_VERSION}, data=__encoded__)
        from netbluemind.system.api.ExternalSystem import ExternalSystem
        from netbluemind.system.api.ExternalSystem import __ExternalSystemSerDer__
        return self.handleResult__(__ExternalSystemSerDer__(), response)

    def getExternalSystems(self):
        postUri = ""
        __data__ = None
        __encoded__ = None
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IExternalSystem_VERSION}, data=__encoded__)
        from netbluemind.system.api.ExternalSystem import ExternalSystem
        from netbluemind.system.api.ExternalSystem import __ExternalSystemSerDer__
        return self.handleResult__(serder.ListSerDer(__ExternalSystemSerDer__()), response)

    def getExternalSystemsByAuthKind(self, authKinds):
        postUri = "/_by_authkind"
        __data__ = None
        __encoded__ = None
        from netbluemind.system.api.ExternalSystemAuthKind import ExternalSystemAuthKind
        from netbluemind.system.api.ExternalSystemAuthKind import __ExternalSystemAuthKindSerDer__
        __data__ = serder.SetSerDer(
            __ExternalSystemAuthKindSerDer__()).encode(authKinds)
        __encoded__ = json.dumps(__data__)
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IExternalSystem_VERSION}, data=__encoded__)
        from netbluemind.system.api.ExternalSystem import ExternalSystem
        from netbluemind.system.api.ExternalSystem import __ExternalSystemSerDer__
        return self.handleResult__(serder.ListSerDer(__ExternalSystemSerDer__()), response)

    def getLogo(self, systemIdentifier):
        postUri = "/{systemIdentifier}/_logo"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{systemIdentifier}", systemIdentifier)
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IExternalSystem_VERSION}, data=__encoded__)
        return self.handleResult__(serder.ByteArraySerDer, response)

    def testConnection(self, systemIdentifier, account):
        postUri = "/{systemIdentifier}/_test_connection"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{systemIdentifier}", systemIdentifier)
        from netbluemind.user.api.UserAccount import UserAccount
        from netbluemind.user.api.UserAccount import __UserAccountSerDer__
        __data__ = __UserAccountSerDer__().encode(account)
        __encoded__ = json.dumps(__data__)
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IExternalSystem_VERSION}, data=__encoded__)
        from netbluemind.system.api.ConnectionTestStatus import ConnectionTestStatus
        from netbluemind.system.api.ConnectionTestStatus import __ConnectionTestStatusSerDer__
        return self.handleResult__(__ConnectionTestStatusSerDer__(), response)
