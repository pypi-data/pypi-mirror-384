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

"""PyAMS_auth_apikey.zmi.container module

This module defines components which are used to manage API keys containers.
"""

from pyramid.decorator import reify
from pyramid.view import view_config

from pyams_auth_apikey.interfaces import IAPIKeyConfiguration
from pyams_auth_apikey.zmi.interfaces import IAPIKeyContainerTable, IAPIKeyConfigurationMenu
from pyams_layer.interfaces import IPyAMSLayer
from pyams_pagelet.pagelet import pagelet_config
from pyams_security.interfaces import ISecurityManager
from pyams_security.interfaces.base import MANAGE_SECURITY_PERMISSION
from pyams_table.column import GetAttrColumn
from pyams_table.interfaces import IColumn, IValues
from pyams_utils.adapter import ContextRequestViewAdapter, adapter_config
from pyams_utils.date import format_datetime
from pyams_utils.factory import factory_config
from pyams_utils.url import absolute_url
from pyams_viewlet.viewlet import viewlet_config
from pyams_zmi.helper.container import delete_container_element, switch_element_attribute
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.table import AttributeSwitcherColumn, I18nColumnMixin, Table, TableAdminView, TrashColumn
from pyams_zmi.zmi.viewlet.menu import NavigationMenuItem


__docformat__ = 'restructuredtext'

from pyams_auth_apikey import _


@viewlet_config(name='apikey-container.menu',
                context=ISecurityManager, layer=IAdminLayer,
                manager=IAPIKeyConfigurationMenu, weight=10,
                permission=MANAGE_SECURITY_PERMISSION)
class APIKeyContainerMenu(NavigationMenuItem):
    """API keys container menu"""

    label = _("API keys")
    href = '#apikey-container.html'


@factory_config(IAPIKeyContainerTable)
class APIKeyContainerTable(Table):
    """API key container table"""

    display_if_empty = True

    @reify
    def data_attributes(self):
        attributes = super().data_attributes
        configuration = IAPIKeyConfiguration(self.context)
        attributes['table'].update({
            'data-ams-order': '1,asc',
            'data-ams-location': absolute_url(configuration, self.request)
        })
        return attributes


@adapter_config(required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IValues)
class APIKeyContainerTableValues(ContextRequestViewAdapter):
    """API keys container table values adapter"""

    @property
    def values(self):
        """Table values getter"""
        yield from IAPIKeyConfiguration(self.context).values()


@adapter_config(name='enabled',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyEnabledSwitcherColumn(AttributeSwitcherColumn):
    """API key enabled column"""

    hint = _("Click icon to enable or disable this API key")

    attribute_name = 'enabled'
    attribute_switcher = 'switch-enabled-key.json'

    icon_on_class = 'fas fa-shop-lock'
    icon_off_class = 'fas fa-shop-slash text-danger'

    weight = 10


@view_config(name='switch-enabled-key.json',
             context=IAPIKeyConfiguration, request_type=IPyAMSLayer,
             renderer='json', xhr=True)
def switch_enabled_key(request):
    """Switch enabled API key"""
    return switch_element_attribute(request)


@adapter_config(name='name',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyNameColumn(I18nColumnMixin, GetAttrColumn):
    """API key container name column"""

    i18n_header = _("Name")
    attr_name = 'name'

    weight = 20


@adapter_config(name='label',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyLabelColumn(I18nColumnMixin, GetAttrColumn):
    """API key container label column"""

    i18n_header = _("Label")
    attr_name = 'label'

    weight = 30

    def get_value(self, obj):
        """Value getter"""
        return super().get_value(obj) or '--'


@adapter_config(name='principal',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyPrincipalColumn(I18nColumnMixin, GetAttrColumn):
    """API key container principal column"""

    i18n_header = _("Principal")

    weight = 40

    def get_value(self, obj):
        """Value getter"""
        principal = obj.get_principal(self.request)
        return principal.title if principal is not None else '--'


@adapter_config(name='activation_date',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyActivationDateColumn(I18nColumnMixin, GetAttrColumn):
    """API key container activation date column"""

    i18n_header = _("Activation date")
    attr_name = 'activation_date'

    weight = 50

    def get_value(self, obj):
        """Activation date getter"""
        activation_date = super().get_value(obj)
        return format_datetime(activation_date)


@adapter_config(name='expiration_date',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyExpirationDateColumn(I18nColumnMixin, GetAttrColumn):
    """API key container expiration date column"""

    i18n_header = _("Expiration date")
    attr_name = 'expiration_date'

    weight = 60

    def get_value(self, obj):
        """Expiration date getter"""
        expiration_date = super().get_value(obj)
        return format_datetime(expiration_date)


@adapter_config(name='trash',
                required=(ISecurityManager, IAdminLayer, APIKeyContainerTable),
                provides=IColumn)
class APIKeyTrashColumn(TrashColumn):
    """API key container trash column"""


@view_config(name='delete-element.json',
             context=IAPIKeyConfiguration, request_type=IPyAMSLayer,
             permission=MANAGE_SECURITY_PERMISSION, renderer='json', xhr=True)
def delete_apikey(request):
    """API key delete view"""
    return delete_container_element(request)


@pagelet_config(name='apikey-container.html',
                context=ISecurityManager, layer=IPyAMSLayer,
                permission=MANAGE_SECURITY_PERMISSION, xhr=True)
class APIKeyContainerView(TableAdminView):
    """API key container view"""

    table_label = _("API keys")
    table_class = IAPIKeyContainerTable
