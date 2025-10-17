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

IMailboxMgmt_VERSION = "5.4.2629"


class IMailboxMgmt(BaseEndpoint):
    def __init__(self, apiKey, url, domainUid):
        self.url = url
        self.apiKey = apiKey
        self.base = url + '/mgmt/mailbox/{domainUid}'
        self.domainUid_ = domainUid
        self.base = self.base.replace('{domainUid}', domainUid)

    def addIndexToRing(self, numericIndex):
        postUri = "/{numericIndex}/_add_index"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{numericIndex}", numericIndex)
        queryParams = {}

        response = requests.put(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def consolidateDomain(self):
        postUri = "/_consolidate"
        __data__ = None
        __encoded__ = None
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def consolidateMailbox(self, mailboxUid):
        postUri = "/{mailboxUid}/_consolidate"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{mailboxUid}", mailboxUid)
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def deleteIndexFromRing(self, numericIndex):
        postUri = "/{numericIndex}/_remove_index"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{numericIndex}", numericIndex)
        queryParams = {}

        response = requests.delete(self.base + postUri, params=queryParams, verify=False, headers={
                                   'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def getLiteStats(self):
        postUri = "/liteStats"
        __data__ = None
        __encoded__ = None
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.mailbox.api.SimpleShardStats import SimpleShardStats
        from netbluemind.mailbox.api.SimpleShardStats import __SimpleShardStatsSerDer__
        return self.handleResult__(serder.ListSerDer(__SimpleShardStatsSerDer__()), response)

    def getShardsStats(self):
        postUri = "/shardsStats"
        __data__ = None
        __encoded__ = None
        queryParams = {}

        response = requests.get(self.base + postUri, params=queryParams, verify=False, headers={
                                'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.mailbox.api.ShardStats import ShardStats
        from netbluemind.mailbox.api.ShardStats import __ShardStatsSerDer__
        return self.handleResult__(serder.ListSerDer(__ShardStatsSerDer__()), response)

    def moveIndex(self, mailboxUid, index, deleteSource):
        postUri = "/{mailboxUid}/_move_index"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{mailboxUid}", mailboxUid)
        queryParams = {'index': index, 'deleteSource': deleteSource}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def resetMailbox(self, mailboxUid):
        postUri = "/{mailboxUid}/_reset"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{mailboxUid}", mailboxUid)
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)

    def respawnMailbox(self, mailboxUid):
        postUri = "/{mailboxUid}/_respawn"
        __data__ = None
        __encoded__ = None
        postUri = postUri.replace("{mailboxUid}", mailboxUid)
        queryParams = {}

        response = requests.post(self.base + postUri, params=queryParams, verify=False, headers={
                                 'X-BM-ApiKey': self.apiKey, 'Accept': 'application/json', 'X-BM-ClientVersion': IMailboxMgmt_VERSION}, data=__encoded__)
        from netbluemind.core.task.api.TaskRef import TaskRef
        from netbluemind.core.task.api.TaskRef import __TaskRefSerDer__
        return self.handleResult__(__TaskRefSerDer__(), response)
