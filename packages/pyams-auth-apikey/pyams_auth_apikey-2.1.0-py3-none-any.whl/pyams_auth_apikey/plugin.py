#
# Copyright (c) 2015-2023 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_auth_apikey.plugin module

This is the main security plugin module used for API keys authentication.
"""

from datetime import datetime, timezone
from functools import partial, wraps

from BTrees.OOBTree import OOBTree
from ZODB.POSException import ConnectionStateError
from persistent import Persistent
from zope.container.contained import Contained
from zope.container.folder import Folder
from zope.password.interfaces import IPasswordManager
from zope.schema.fieldproperty import FieldProperty
from zope.traversing.interfaces import ITraversable

from pyams_auth_apikey.interfaces import APIKEY_CONFIGURATION_KEY, APIKEY_PREFIX, APIKEY_SALT, IAPIKey, \
    IAPIKeyConfiguration, IAPIKeyPlugin
from pyams_security.credential import Credentials
from pyams_security.interfaces import ISecurityManager
from pyams_security.interfaces.names import PRINCIPAL_ID_FORMATTER
from pyams_security.interfaces.plugin import IAuthenticationPlugin, ICredentialsPlugin, IDirectoryPlugin
from pyams_security.principal import PrincipalInfo
from pyams_security.utility import get_principal
from pyams_utils.adapter import ContextAdapter, adapter_config, get_annotation_adapter
from pyams_utils.factory import factory_config
from pyams_utils.property import ClassPropertyType, classproperty
from pyams_utils.registry import get_pyramid_registry, query_utility, utility_config
from pyams_utils.request import query_request
from pyams_utils.timezone import tztime
from pyams_utils.zodb import volatile_property


__docformat__ = 'restructuredtext'

from pyams_auth_apikey import LOGGER, _


@factory_config(IAPIKey)
class APIKey(Persistent, Contained):
    """API key persistent class"""

    name = FieldProperty(IAPIKey['name'])
    hash = FieldProperty(IAPIKey['hash'])
    _enabled = FieldProperty(IAPIKey['enabled'])
    label = FieldProperty(IAPIKey['label'])
    _principal_id = FieldProperty(IAPIKey['principal_id'])
    _activation_date = FieldProperty(IAPIKey['activation_date'])
    _expiration_date = FieldProperty(IAPIKey['expiration_date'])
    restrict_referrers = FieldProperty(IAPIKey['restrict_referrers'])
    allowed_referrers = FieldProperty(IAPIKey['allowed_referrers'])
    allowed_as_request_param = FieldProperty(IAPIKey['allowed_as_request_param'])
    request_param_name = FieldProperty(IAPIKey['request_param_name'])

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def key(self):
        """API key getter"""
        return None

    @key.setter
    def key(self, value):
        """API key setter, only stores hash"""
        registry = get_pyramid_registry()
        encoder = registry.getUtility(IPasswordManager, name='PBKDF2')
        self.hash = encoder.encodePassword(value, salt=APIKEY_SALT)[8:]

    @property
    def enabled(self):
        """Enabled field getter"""
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """Enabled field setter"""
        if value != self._enabled:
            self._enabled = value
            del self.active

    @property
    def principal_id(self):
        """Principal ID getter"""
        return self._principal_id

    @principal_id.setter
    def principal_id(self, value):
        """Principal ID setter"""
        plugin = self.__parent__
        if plugin is not None:
            plugin.update_key(self, self._principal_id, value)
        self._principal_id = value

    @property
    def activation_date(self):
        """Activation date field getter"""
        return self._activation_date

    @activation_date.setter
    def activation_date(self, value):
        """Activation date field setter"""
        if value != self._activation_date:
            self._activation_date = value
            del self.active

    @property
    def expiration_date(self):
        """Expiration date field getter"""
        return self._expiration_date

    @expiration_date.setter
    def expiration_date(self, value):
        """Expiration date field setter"""
        if value != self._expiration_date:
            self._expiration_date = value
            del self.active

    @volatile_property
    def active(self):
        """Key activity checker"""
        if not self.enabled:
            return False
        now = tztime(datetime.now(timezone.utc))
        if self.activation_date and (self.activation_date > now):
            return False
        if self.expiration_date and (self.expiration_date < now):
            return False
        return True

    def get_principal(self, request=None, allow_redirect=True):
        """Get principal matching this API key"""
        if not self.active:
            return None
        if request is None:
            request = query_request()
        if self.restrict_referrers:
            origin = request.headers.get('Origin', request.host_url)
            if not ((origin == request.host_url) or (origin in self.allowed_referrers or ())):
                return None
        if self.principal_id and allow_redirect:
            return get_principal(request, self.principal_id)
        translate = request.localizer.translate
        return PrincipalInfo(id=PRINCIPAL_ID_FORMATTER.format(prefix=APIKEY_PREFIX, login=self.name),
                             title=translate(_("API key: {}")).format(self.label))


def check_enabled(func=None, *, default=None):
    """Decorator to check for enabled plugin"""
    if func is None:
        return partial(check_enabled, default=default)

    @wraps(func)
    def wrapper(plugin, *args, **kwargs):
        if not plugin.enabled:
            return default() if default is not None else None
        return func(plugin, *args, **kwargs)
    return wrapper


def check_prefix(func=None, *, default=None):
    """Decorator to check for principal ID prefix"""
    if func is None:
        return partial(check_prefix, default=default)

    @wraps(func)
    def wrapper(plugin, principal_id, *args, **kwargs):
        if not principal_id.startswith(f'{APIKEY_PREFIX}:'):
            return default() if default is not None else None
        return func(plugin, principal_id, *args, **kwargs)
    return wrapper


@factory_config(IAPIKeyConfiguration)
class APIKeyConfiguration(Folder):
    """API keys container folder"""

    enabled = FieldProperty(IAPIKeyConfiguration['enabled'])
    http_header = FieldProperty(IAPIKeyConfiguration['http_header'])

    by_hash = None
    by_principal = None

    def _newContainerData(self):
        """Create new container data"""
        data = super()._newContainerData()
        self.by_hash = OOBTree()
        self.by_principal = OOBTree()
        return data

    def __setitem__(self, key, value):
        """Store new API key"""
        super().__setitem__(key, value)
        self.by_hash[value.hash] = value
        if value.principal_id:
            self.by_principal.setdefault(value.principal_id, []).append(value)

    def __delitem__(self, key):
        """Del API key"""
        apikey = self.get(key)
        if apikey is not None:
            del self.by_hash[apikey.hash]
            if apikey.principal_id:
                keys = self.by_principal.get(apikey.principal_id)
                if apikey in keys:
                    keys.remove(apikey)
                if keys:
                    self.by_principal[apikey.principal_id] = keys
                else:
                    del self.by_principal[apikey.principal_id]
        super().__delitem__(key)

    def get_active_keys(self):
        """Iterator over active keys"""
        yield from filter(lambda x: x.active, self.values())

    def update_key(self, apikey, old_principal_id, new_principal_id):
        """Update key"""
        keys = self.by_principal.get(old_principal_id)
        if keys:
            if apikey in keys:
                keys.remove(apikey)
            if keys:
                self.by_principal[old_principal_id] = keys
            else:
                del self.by_principal[old_principal_id]
        if new_principal_id:
            self.by_principal.setdefault(new_principal_id, []).append(apikey)

    @check_enabled
    def get_apikey_header(self, request):
        """Extract API key from request header"""
        return request.headers.get(self.http_header)

    @staticmethod
    def get_key_hash(key):
        """Convert key to it's hash"""
        registry = get_pyramid_registry()
        encoder = registry.getUtility(IPasswordManager, name='PBKDF2')
        return encoder.encodePassword(key, salt=APIKEY_SALT)[8:]

    @check_enabled
    def find_active_key(self, key):
        """Find API key matching provided key"""
        hash = self.get_key_hash(key)
        apikey = self.by_hash.get(hash)
        if (apikey is None) or (not apikey.active):
            return None
        LOGGER.debug("  > Found API key: %s", apikey.name)
        return apikey

    def extract_credentials(self, request):
        """Extract credentials from request"""
        header = self.get_apikey_header(request)
        if header is None:
            for apikey in self.get_active_keys():
                if apikey.allowed_as_request_param:
                    header = request.params.get(apikey.request_param_name)
                    if header is not None:
                        break
            else:
                return None
        apikey = self.find_active_key(header)
        if apikey is None:
            return None
        return Credentials(APIKEY_PREFIX, f'{APIKEY_PREFIX}:{apikey.name}')

    @check_enabled
    def authenticate(self, credentials, request):
        """Authenticate provided credentials against active API keys"""
        prefix, name = credentials.id.split(':', 1)
        if prefix != APIKEY_PREFIX:
            return None
        apikey = self.get(name)
        if (apikey is None) or (not apikey.active):
            return None
        principal = apikey.get_principal(request)
        if principal is not None:
            return principal.id
        return None

    @check_enabled
    @check_prefix
    def get_principal(self, principal_id, info=True):
        """Returns real principal matching given ID, or None"""
        prefix, name = principal_id.split(':', 1)
        apikey = self.get(name)
        if apikey is None:
            return None
        if info:
            return apikey.get_principal()
        return apikey

    @check_enabled(default=set)
    @check_prefix(default=set)
    def get_all_principals(self, principal_id):
        """Returns all principals matching given principal ID"""
        result = set()
        prefix, name = principal_id.split(':', 1)
        apikey = self.get(name)
        if (apikey is not None) and apikey.active:
            result.add(principal_id)
            principal = apikey.get_principal()
            if principal is not None:
                result.add(principal.id)
        return result

    @check_enabled
    def find_principals(self, query, exact_match=False):
        """Find principals matching given query"""
        if not query:
            return
        query = query.lower()
        for apikey in self.values():
            if not apikey.active:
                continue
            for attr in (apikey.name, apikey.label):
                if not attr:
                    continue
                if (exact_match and query == attr.lower()) or \
                        (not exact_match and query in attr.lower()):
                    yield apikey.get_principal(allow_redirect=False)
                    break


@adapter_config(required=ISecurityManager,
                provides=IAPIKeyConfiguration)
def security_manager_apikey_configuration(context):
    """Security manager API keys configuration"""
    return get_annotation_adapter(context, APIKEY_CONFIGURATION_KEY, IAPIKeyConfiguration,
                                  name='++apikey-config++')


@adapter_config(name='apikey-config',
                required=ISecurityManager,
                provides=ITraversable)
class SecurityManagerAPIKeyConfigurationTraverser(ContextAdapter):
    """Security manager API key configuration traverser"""

    def traverse(self, name, furtherpath=None):  # pylint: disable=unused-argument
        """Traverse to API key configuration"""
        return IAPIKeyConfiguration(self.context)


@utility_config(provides=IAPIKeyPlugin)
@utility_config(name='apikey', provides=ICredentialsPlugin)
@utility_config(name='apikey', provides=IAuthenticationPlugin)
@utility_config(name='apikey', provides=IDirectoryPlugin)
class APIKeyPlugin(metaclass=ClassPropertyType):
    """API keys plug-in"""

    prefix = APIKEY_PREFIX
    title = _("API keys authentication")

    @classproperty
    def configuration(cls):  # pylint: disable=no-self-argument,no-self-use
        """API keys configuration getter"""
        try:
            sm = query_utility(ISecurityManager)  # pylint: disable=invalid-name
            if sm is not None:
                return IAPIKeyConfiguration(sm)
        except ConnectionStateError:
            return None
        return None

    @classproperty
    def enabled(cls):  # pylint: disable=no-self-argument,no-self-use
        """Check if API keys authentication is enabled"""
        configuration = cls.configuration
        try:
            return configuration.enabled if (configuration is not None) else False
        except ConnectionStateError:
            return False

    def extract_credentials(self, request, **kwargs):  # pylint: disable=unused-argument
        """Extract credentials from HTTP header"""
        configuration = self.configuration
        if configuration is None:
            return None
        return configuration.extract_credentials(request)

    def authenticate(self, credentials, request):
        """Authenticate provided credentials"""
        if credentials.prefix != self.prefix:
            return None
        configuration = self.configuration
        if configuration is None:
            return None
        return configuration.authenticate(credentials, request)

    def get_principal(self, principal_id, info=True):
        """Returns real principal matching given ID, or None"""
        configuration = self.configuration
        if configuration is None:
            return None
        return configuration.get_principal(principal_id, info)

    def get_all_principals(self, principal_id):
        """Returns all principals matching given principal ID"""
        configuration = self.configuration
        if configuration is None:
            return set()
        return configuration.get_all_principals(principal_id) or set()

    def find_principals(self, query, exact_match=False):
        """Find principals matching given query"""
        configuration = self.configuration
        if configuration is None:
            return
        yield from configuration.find_principals(query, exact_match) or set()
