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
from netbluemind.python import serder


class Credential:
    def __init__(self):
        self.id = None
        self.type = None
        self.label = None
        self.created = None
        self.secret = None
        self.credential = None
        pass


class __CredentialSerDer__:
    def __init__(self):
        pass

    def parse(self, value):
        if (value == None):
            return None
        instance = Credential()

        self.parseInternal(value, instance)
        return instance

    def parseInternal(self, value, instance):
        idValue = value['id']
        instance.id = serder.STRING.parse(idValue)
        typeValue = value['type']
        instance.type = serder.STRING.parse(typeValue)
        labelValue = value['label']
        instance.label = serder.STRING.parse(labelValue)
        createdValue = value['created']
        instance.created = serder.LONG.parse(createdValue)
        secretValue = value['secret']
        instance.secret = serder.STRING.parse(secretValue)
        credentialValue = value['credential']
        instance.credential = serder.STRING.parse(credentialValue)
        return instance

    def encode(self, value):
        if (value == None):
            return None
        instance = dict()
        self.encodeInternal(value, instance)
        return instance

    def encodeInternal(self, value, instance):

        idValue = value.id
        instance["id"] = serder.STRING.encode(idValue)
        typeValue = value.type
        instance["type"] = serder.STRING.encode(typeValue)
        labelValue = value.label
        instance["label"] = serder.STRING.encode(labelValue)
        createdValue = value.created
        instance["created"] = serder.LONG.encode(createdValue)
        secretValue = value.secret
        instance["secret"] = serder.STRING.encode(secretValue)
        credentialValue = value.credential
        instance["credential"] = serder.STRING.encode(credentialValue)
        return instance
