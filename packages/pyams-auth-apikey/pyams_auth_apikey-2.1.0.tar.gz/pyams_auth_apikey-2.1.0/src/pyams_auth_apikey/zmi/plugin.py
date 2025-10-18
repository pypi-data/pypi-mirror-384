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

"""PyAMS_auth_apikey.zmi.plugin module

This modules defines main API keys configuration management components.
"""

from zope.interface import Interface

from pyams_auth_apikey.interfaces import IAPIKeyConfiguration
from pyams_auth_apikey.zmi.interfaces import IAPIKeyConfigurationMenu
from pyams_form.ajax import ajax_form_config
from pyams_form.field import Fields
from pyams_form.interfaces.form import IGroup
from pyams_layer.interfaces import IPyAMSLayer
from pyams_security.interfaces import ISecurityManager
from pyams_security.interfaces.base import MANAGE_SECURITY_PERMISSION
from pyams_security_views.zmi import ISecurityMenu
from pyams_utils.adapter import adapter_config
from pyams_utils.registry import get_utility
from pyams_viewlet.manager import viewletmanager_config
from pyams_zmi.form import AdminEditForm, FormGroupChecker
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.zmi.viewlet.menu import NavigationMenuItem


__docformat__ = 'restructuredtext'

from pyams_auth_apikey import _


@viewletmanager_config(name='apikey-configuration.menu',
                       context=ISecurityManager, layer=IAdminLayer,
                       manager=ISecurityMenu, weight=17,
                       provides=IAPIKeyConfigurationMenu,
                       permission=MANAGE_SECURITY_PERMISSION)
class APIKeyConfigurationMenu(NavigationMenuItem):
    """API keys configuration menu"""

    label = _("API keys configuration")
    href = '#apikey-configuration.html'


@ajax_form_config(name='apikey-configuration.html',
                  context=ISecurityManager, layer=IPyAMSLayer,
                  permission=MANAGE_SECURITY_PERMISSION)
class APIKeyConfigurationEditForm(AdminEditForm):
    """API keys configuration edit form"""

    title = _("API keys configuration")

    fields = Fields(Interface)

    def get_content(self):
        """Content getter"""
        return get_utility(ISecurityManager)


@adapter_config(name='apikey-configuration',
                required=(ISecurityManager, IAdminLayer, APIKeyConfigurationEditForm),
                provides=IGroup)
class APIKeyConfigurationGroup(FormGroupChecker):
    """API keys configuration group"""

    fields = Fields(IAPIKeyConfiguration)
