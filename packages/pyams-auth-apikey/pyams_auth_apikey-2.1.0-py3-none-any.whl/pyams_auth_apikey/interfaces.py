#
# Copyright (c) 2015-2019 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_auth_apikey.interfaces module

"""

from zope.container.constraints import contains
from zope.container.interfaces import IContainer
from zope.interface import Attribute, Interface, Invalid, invariant
from zope.schema import Bool, BytesLine, Datetime, TextLine

from pyams_security.interfaces.plugin import IAuthenticationPlugin, ICredentialsPlugin, IDirectoryPlugin
from pyams_security.schema import PrincipalField
from pyams_utils.schema import TextLineListField

__docformat__ = 'restructuredtext'

from pyams_auth_apikey import _


APIKEY_CONFIGURATION_KEY = 'pyams_auth_apikey.configuration'
"""Main API key configuration key"""

APIKEY_PLUGIN_LABEL = _("API keys authentication plug-in")
"""API keys plugin label"""

APIKEY_PREFIX = 'apikey'
"""API key plugin prefix"""

APIKEY_SALT = 'PyAMS'
"""Default key encoding salt"""


class IAPIKey(Interface):
    """Base API key interface"""

    name = TextLine(title=_("Key name"),
                    description=_("This name must be unique between all API keys; if empty, a random name will be "
                                  "used as name"),
                    required=False)

    key = TextLine(title=_("API key"),
                   description=_("This API key will never be displayed again, just copy it and keep it safe!"),
                   required=False)

    hash = BytesLine(title=_("API key hash"),
                     description=_("This is a hash of the API key and can't be modified"),
                     required=True,
                     readonly=True)

    enabled = Bool(title=_("Enabled key?"),
                   description=_("Select 'no' to disable the key temporarily"),
                   required=True,
                   default=True)

    label = TextLine(title=_("Key label"),
                     description=_("This label will be used to identify the key"),
                     required=False)

    principal_id = PrincipalField(title=_("Associated principal"),
                                  description=_("If defined, this will identify the principal which will be used when "
                                                "a request will be authenticated with this API key"),
                                  required=False)

    @invariant
    def check_principal_id(self):
        """Check principal ID"""
        if self.principal_id and (self.principal_id.startswith(f'{APIKEY_PREFIX}:')):
            raise Invalid(_("Selected principal can't be another API key!"))

    def get_principal(self, request=None):
        """Get principal matching the API key"""

    activation_date = Datetime(title=_("Activation date"),
                               description=_("This key will be enabled only after this date"),
                               required=False)

    expiration_date = Datetime(title=_("Expiration date"),
                               description=_("This key will not be enabled after this date"),
                               required=True)

    restrict_referrers = Bool(title=_("Restrict referrers"),
                              description=_("If this option is enabled, only selected referrers will be enabled"),
                              required=True,
                              default=False)

    allowed_referrers = TextLineListField(title=_("Allowed referrers"),
                                          description=_("Only selected referrers will be allowed to use this API key"),
                                          required=False)

    allowed_as_request_param = Bool(title=_("Allowed as request param"),
                                    description=_("If 'yes', this API key can be sent as a request URL parameter "
                                                  "instead of an HTTP request header only"),
                                    required=True,
                                    default=False)
    
    request_param_name = TextLine(title=_("Request param name"),
                                  description=_("Name of the request parameter used to send this API key"),
                                  required=False,
                                  default='x-api-key')

    active = Attribute("Key activity checker")


class IAPIKeyConfiguration(IContainer):
    """API keys plug-in configuration interface"""

    contains(IAPIKey)

    enabled = Bool(title=_("Enabled API key authentication?"),
                   description=_("Enable login via API keys"),
                   required=False,
                   default=False)

    http_header = TextLine(title=_("HTTP header"),
                           description=_("Name of the HTTP header used to provide the API key"),
                           required=True,
                           default='X-API-Key')

    by_hash = Attribute("API keys mapping by key hash")
    by_principal = Attribute("API keys mapping by principal ID")

    def get_apikey(self, request):
        """Extract API key from provided request"""

    def find_active_key(self, request):
        """Get active API key with given ID"""


class IAPIKeyPlugin(ICredentialsPlugin, IAuthenticationPlugin, IDirectoryPlugin):
    """API keys authentication module"""

    configuration = Attribute("API keys configuration")
    enabled = Attribute("Enable API keys authentication?")
