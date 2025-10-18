======================
PyAMS API keys package
======================

Introduction
------------

This package is composed of a set of utility functions, usable into any Pyramid application.

    >>> from pyramid.testing import setUp, tearDown, DummyRequest
    >>> config = setUp(hook_zca=True)
    >>> config.registry.settings['zodbconn.uri'] = 'memory://'

    >>> from pyramid_zodbconn import includeme as include_zodbconn
    >>> include_zodbconn(config)
    >>> from cornice import includeme as include_cornice
    >>> include_cornice(config)
    >>> from pyams_utils import includeme as include_utils
    >>> include_utils(config)
    >>> from pyams_site import includeme as include_site
    >>> include_site(config)
    >>> from pyams_security import includeme as include_security
    >>> include_security(config)
    >>> from pyams_skin import includeme as include_skin
    >>> include_skin(config)
    >>> from pyams_zmi import includeme as include_zmi
    >>> include_zmi(config)
    >>> from pyams_form import includeme as include_form
    >>> include_form(config)
    >>> from pyams_auth_apikey import includeme as include_auth_apikey
    >>> include_auth_apikey(config)

    >>> from pyams_site.generations import upgrade_site
    >>> request = DummyRequest()
    >>> app = upgrade_site(request)
    Upgrading PyAMS timezone to generation 1...
    Upgrading PyAMS security to generation 2...


Enabling API keys plug-in
-------------------------

Let's start by enabling API keys authentication:

    >>> from pyams_utils.registry import set_local_registry, get_utility

    >>> from pyams_security.interfaces import ISecurityManager
    >>> from pyams_auth_apikey.interfaces import IAPIKeyPlugin, IAPIKeyConfiguration

    >>> set_local_registry(app.getSiteManager())
    >>> sm = get_utility(ISecurityManager)

    >>> plugin = get_utility(IAPIKeyPlugin)
    >>> plugin
    <pyams_auth_apikey.plugin.APIKeyPlugin object at 0x...>

    >>> plugin in sm.credentials_plugins
    True
    >>> plugin in sm.authentication_plugins
    True

    >>> plugin.enabled
    False

    >>> configuration = plugin.configuration
    >>> configuration
    <pyams_auth_apikey.plugin.APIKeyConfiguration object at 0x...>
    >>> configuration.http_header
    'X-API-Key'

    >>> configuration.enabled = True
    >>> plugin.enabled
    True


Creating a first API key
------------------------

    >>> from pyams_utils.factory import get_object_factory
    >>> from pyams_auth_apikey.interfaces import IAPIKey

    >>> factory = get_object_factory(IAPIKey)
    >>> factory
    <pyams_utils.factory.register_factory.<locals>.Temp object at 0x...>

    >>> apikey = factory(name='test1', key='my-api-key', label="Test key")
    >>> apikey.hash
    b'...'

We can't get an API key after it's creation:

    >>> apikey.key is None
    True

    >>> configuration[apikey.name] = apikey
    >>> list(configuration.keys())
    ['test1']
    >>> dict(configuration.by_hash)
    {b'...': <pyams_auth_apikey.plugin.APIKey object at 0x...>}
    >>> dict(configuration.by_principal)
    {}

    >>> apikey.principal_id = 'system:admin'
    >>> dict(configuration.by_principal)
    {'system:admin': [<pyams_auth_apikey.plugin.APIKey object at 0x...>]}

    >>> apikey.principal_id = 'system:admin2'
    >>> dict(configuration.by_principal)
    {'system:admin2': [<pyams_auth_apikey.plugin.APIKey object at 0x...>]}

    >>> apikey.principal_id = None
    >>> dict(configuration.by_principal)
    {}

We can also assign principal ID on creation:

    >>> apikey2 = factory(name='test2', key='another-api-key', label="Test key 2", principal_id='system:admin')
    >>> configuration[apikey2.name] = apikey2
    >>> dict(configuration.by_principal)
    {'system:admin': [<pyams_auth_apikey.plugin.APIKey object at 0x...>]}

    >>> del configuration[apikey2.name]
    >>> dict(configuration.by_principal)
    {}


Setting API key activation and expiration
-----------------------------------------

You can set an expiration and an activation date on each key:

    >>> from datetime import datetime, timedelta
    >>> from pyams_utils.timezone import tztime

    >>> apikey.active
    True

    >>> now = tztime(datetime.utcnow())
    >>> apikey.activation_date = now + timedelta(days=1)
    >>> apikey.active
    False

    >>> apikey.activation_date = None
    >>> apikey.expiration_date = now - timedelta(days=1)
    >>> apikey.active
    False

The expiration date is mandatory if set:

    >>> apikey.expiration_date = None
    Traceback (most recent call last):
    ...
    zope.schema._bootstrapinterfaces.RequiredMissing: expiration_date

    >>> apikey.expiration_date = now + timedelta(days=365)
    >>> apikey.active
    True


Extracting credentials and authenticating
-----------------------------------------

    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True

    >>> from pyramid.threadlocal import manager

    >>> request = DummyRequest(headers={'X-API-Key': 'my-api-key'})
    >>> manager.push({'request': request, 'registry': config.registry})
    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'apikey'
    >>> creds.id
    'apikey:test1'

    >>> principal_id = plugin.authenticate(creds, request)
    >>> principal_id is None
    False
    >>> principal_id
    'apikey:test1'

We can try to associate an API key with a principal; but this requires a Beaker cache:

    >>> from beaker.cache import CacheManager, cache_regions
    >>> cache = CacheManager(**{'cache.type': 'memory'})
    >>> cache_regions.update({'short': {'type': 'memory', 'expire': 0}})
    >>> cache_regions.update({'long': {'type': 'memory', 'expire': 0}})

    >>> apikey.principal_id = 'system:admin'
    >>> principal_id = plugin.authenticate(creds, request)
    >>> principal_id
    'system:admin'


Providing API keys as request params
------------------------------------

API keys are normally provided via an HTTP header, called 'X-API-Key' by default.
By exception, you can allow an API key to be provided via a request parameter:

    >>> apikey.allowed_as_request_param = True

    >>> request = DummyRequest(params={'x-api-key': 'my-api-key'})
    >>> manager.push({'request': request, 'registry': config.registry})
    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'apikey'
    >>> creds.id
    'apikey:test1'

    >>> apikey.allowed_as_request_param = False


Getting principals
------------------

API keys plugin can only retrieve principals which are not associated with another principal:

    >>> request = DummyRequest(headers={'X-API-Key': 'my-api-key'})

    >>> principal = plugin.get_principal(principal_id)
    >>> principal is None
    True

    >>> apikey.principal_id = None
    >>> principal_id = plugin.authenticate(creds, request)
    >>> principal_id
    'apikey:test1'

    >>> principal = plugin.get_principal(principal_id)
    >>> principal
    <pyams_security.principal.PrincipalInfo object at 0x...>
    >>> principal.id
    'apikey:test1'
    >>> principal.title
    'API key: Test key'

    >>> principal_key = plugin.get_principal(principal_id, info=False)
    >>> principal_key
    <pyams_auth_apikey.plugin.APIKey object at 0x...>
    >>> principal_key is apikey
    True

    >>> plugin.get_all_principals(principal_id)
    {'apikey:test1'}

Let's update principal ID:

    >>> apikey.principal_id = 'system:admin'
    >>> sorted(plugin.get_all_principals(principal_id))
    ['apikey:test1', 'system:admin']


Searching principals
--------------------

    >>> list(plugin.find_principals('key'))
    [<pyams_security.principal.PrincipalInfo object at 0x...>]
    >>> [info.id for info in plugin.find_principals('key')]
    ['apikey:test1']
    >>> [info.id for info in plugin.find_principals('key', exact_match=True)]
    []
    >>> [info.id for info in plugin.find_principals('Test key', exact_match=True)]
    ['apikey:test1']


Disabled configuration
----------------------

All methods return a null value if configuration or key is disabled, including credentials
extraction:

    >>> apikey.enabled = False
    >>> apikey.active
    False

    >>> plugin.extract_credentials(request) is None
    True
    >>> plugin.authenticate(creds, request) is None
    True
    >>> plugin.get_principal(principal_id) is None
    True
    >>> plugin.get_all_principals(principal_id)
    set()
    >>> list(plugin.find_principals('key'))
    []

    >>> apikey.enabled = True
    >>> apikey.active
    True

    >>> configuration.enabled = False

    >>> plugin.extract_credentials(request) is None
    True
    >>> plugin.authenticate(creds, request) is None
    True
    >>> plugin.get_principal(principal_id) is None
    True
    >>> plugin.get_all_principals(principal_id)
    set()
    >>> list(plugin.find_principals('key'))
    []


Tests cleanup:

    >>> tearDown()
