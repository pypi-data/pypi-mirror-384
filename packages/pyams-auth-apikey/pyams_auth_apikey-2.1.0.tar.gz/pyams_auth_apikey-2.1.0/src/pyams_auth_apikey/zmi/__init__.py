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

"""PyAMS_auth_apikey.zmi module

This module defines management components which are used to handle API keys.
"""

import hashlib
import hmac
import random
import sys
from datetime import datetime, timedelta, timezone

from pyramid.events import subscriber
from zope.interface import Interface, Invalid

from pyams_auth_apikey.interfaces import IAPIKey, IAPIKeyConfiguration
from pyams_auth_apikey.zmi.interfaces import IAPIKeyContainerTable
from pyams_form.ajax import ajax_form_config
from pyams_form.field import Fields
from pyams_form.interfaces import DISPLAY_MODE
from pyams_form.interfaces.form import IAJAXFormRenderer, IDataExtractedEvent, IGroup
from pyams_layer.interfaces import IPyAMSLayer
from pyams_security.interfaces import ISecurityManager, IViewContextPermissionChecker
from pyams_security.interfaces.base import MANAGE_SECURITY_PERMISSION
from pyams_skin.interfaces.view import IModalAddForm, IModalEditForm
from pyams_skin.interfaces.viewlet import IFormHeaderViewletManager
from pyams_skin.viewlet.actions import ContextAddAction
from pyams_skin.viewlet.help import AlertMessage
from pyams_skin.widget.text import TextCopyFieldWidget
from pyams_utils.adapter import ContextAdapter, ContextRequestViewAdapter, adapter_config
from pyams_utils.interfaces import ICacheKeyValue
from pyams_utils.registry import get_utility
from pyams_utils.timezone import tztime
from pyams_utils.url import absolute_url
from pyams_viewlet.viewlet import viewlet_config
from pyams_zmi.form import AdminModalAddForm, AdminModalEditForm, FormGroupChecker
from pyams_zmi.helper.event import get_json_table_row_add_callback, get_json_table_row_refresh_callback
from pyams_zmi.interfaces import IAdminLayer, TITLE_SPAN_BREAK
from pyams_zmi.interfaces.form import IFormTitle
from pyams_zmi.interfaces.table import ITableElementEditor
from pyams_zmi.interfaces.viewlet import IToolbarViewletManager
from pyams_zmi.table import TableElementEditor
from pyams_zmi.utils import get_object_label


__docformat__ = 'restructuredtext'

from pyams_auth_apikey import _


@viewlet_config(name='add-apikey.action',
                context=ISecurityManager, layer=IAdminLayer, view=IAPIKeyContainerTable,
                manager=IToolbarViewletManager, weight=10,
                permission=MANAGE_SECURITY_PERMISSION)
class APIKeyAddAction(ContextAddAction):
    """API key add action"""

    label = _("Add API key")
    href = 'add-apikey.html'

    def get_href(self):
        configuration = IAPIKeyConfiguration(self.context)
        return absolute_url(configuration, self.request, self.href)


@ajax_form_config(name='add-apikey.html',
                  context=IAPIKeyConfiguration, layer=IPyAMSLayer,
                  permission=MANAGE_SECURITY_PERMISSION)
class APIKeyAddForm(AdminModalAddForm):
    """API key add form"""

    subtitle = _("New API key")
    legend = _("New API key properties")

    fields = Fields(IAPIKey).omit('hash', 'enabled', 'restrict_referrers', 'allowed_referrers',
                                  'allowed_as_request_param', 'request_param_name')
    fields['key'].widget_factory = TextCopyFieldWidget

    content_factory = IAPIKey

    def update_widgets(self, prefix=None):
        super().update_widgets(prefix)
        key = self.widgets.get('key')
        if key is not None:
            secret = ''.join((hex(random.randint(0, sys.maxsize))[2:]
                              for i in range(4)))
            seed1 = '-'.join((hex(random.randint(0, sys.maxsize))[2:]
                              for i in range(4)))
            seed2 = '-'.join((hex(random.randint(0, sys.maxsize))[2:]
                              for i in range(4)))
            secret = hmac.new(secret.encode(), seed1.encode(), digestmod=hashlib.sha512)
            secret.update(seed2.encode())
            key.value = secret.hexdigest()
            key.readonly = 'readonly'
        expiration_date = self.widgets.get('expiration_date')
        if expiration_date is not None:
            now = tztime(datetime.now(timezone.utc))
            expiration_date.value = now + timedelta(days=365)

    def update_content(self, obj, data):
        """Update new content properties"""
        changes = super().update_content(obj, data)
        if not obj.name:
            obj.name = ICacheKeyValue(obj)
        return changes

    def add(self, obj):
        """Add API key to container"""
        self.context[obj.name] = obj


@adapter_config(required=(IAPIKeyConfiguration, IAdminLayer, IModalAddForm),
                provides=IFormTitle)
def apikey_add_form_title(context, request, form):
    """API key add form title getter"""
    translate = request.localizer.translate
    manager = get_utility(ISecurityManager)
    return TITLE_SPAN_BREAK.format(
        get_object_label(manager, request, form),
        translate(_("Plug-in: API keys authentication")))


@adapter_config(name='referrers.group',
                required=(IAPIKeyConfiguration, IAdminLayer, APIKeyAddForm),
                provides=IGroup)
class APIKeyAddFormReferrersGroup(FormGroupChecker):
    """API key add form referrers group"""

    fields = Fields(IAPIKey).select('restrict_referrers', 'allowed_referrers')
    weight = 10


@adapter_config(name='request-param.group',
                required=(IAPIKeyConfiguration, IAdminLayer, APIKeyAddForm),
                provides=IGroup)
class APIKeyAddFormRequestParamsGroup(FormGroupChecker):
    """API key add form request params group"""

    fields = Fields(IAPIKey).select('allowed_as_request_param', 'request_param_name')
    weight = 20


@viewlet_config(name='add-api-key.header',
                context=IAPIKeyConfiguration, layer=IAdminLayer, view=APIKeyAddForm,
                manager=IFormHeaderViewletManager, weight=1)
class APIKeyAddFormHelp(AlertMessage):
    """API key add form help"""

    _message = _("WARNING: the API key won't be displayed after it's creation!\n"
                 "You must copy it NOW and keep it safe!!")
    message_renderer = 'text'

    status = 'danger'
    icon_class = 'fas fa-radiation'


@subscriber(IDataExtractedEvent, form_selector=APIKeyAddForm)
def handle_apikey_add_form_data(event):
    """Handle new API key data"""
    data = event.data
    name = data.get('name')
    if name and (name in event.form.context):
        event.form.widgets.errors += (Invalid(_("This key name is already used!")),)


@adapter_config(required=(IAPIKeyConfiguration, IAdminLayer, APIKeyAddForm),
                provides=IAJAXFormRenderer)
class APIKeyAddFormRenderer(ContextRequestViewAdapter):
    """API key add form renderer"""

    def render(self, changes):
        """JSON form renderer"""
        if not changes:
            return None
        sm = get_utility(ISecurityManager)
        return {
            'callbacks': [
                get_json_table_row_add_callback(sm, self.request,
                                                IAPIKeyContainerTable, changes)
            ]
        }


@adapter_config(required=(IAPIKey, IAdminLayer, Interface),
                provides=ITableElementEditor)
class APIKeyElementEditor(TableElementEditor):
    """API key table element editor"""


@adapter_config(required=IAPIKey,
                provides=IViewContextPermissionChecker)
class APIKeyPermissionChecker(ContextAdapter):
    """API key permission checker"""

    edit_permission = MANAGE_SECURITY_PERMISSION


@ajax_form_config(name='properties.html',
                  context=IAPIKey, layer=IPyAMSLayer,
                  permission=MANAGE_SECURITY_PERMISSION)
class APIKeyPropertiesEditForm(AdminModalEditForm):
    """API key properties edit form"""

    @property
    def subtitle(self):
        translate = self.request.localizer.translate
        return translate(_("API key: {}")).format(self.context.label)

    legend = _("API key properties")

    fields = Fields(IAPIKey).omit('key', 'enabled', 'restrict_referrers', 'allowed_referrers',
                                  'allowed_as_request_param', 'request_param_name')

    def update_widgets(self, prefix=None):
        """Widgets update"""
        super().update_widgets(prefix)
        name = self.widgets.get('name')
        if name is not None:
            name.mode = DISPLAY_MODE


@adapter_config(required=(IAPIKey, IAdminLayer, IModalEditForm),
                provides=IFormTitle)
def apikey_edit_form_title(context, request, form):
    """API key add form title getter"""
    translate = request.localizer.translate
    manager = get_utility(ISecurityManager)
    return TITLE_SPAN_BREAK.format(
        get_object_label(manager, request, form),
        translate(_("Plug-in: API keys authentication")))


@adapter_config(name='referrers.group',
                required=(IAPIKey, IAdminLayer, APIKeyPropertiesEditForm),
                provides=IGroup)
class APIKeyPropertiesEditFormReferrersGroup(FormGroupChecker):
    """API key properties edit form referrers group"""

    fields = Fields(IAPIKey).select('restrict_referrers', 'allowed_referrers')
    weight = 10


@adapter_config(name='request-param.group',
                required=(IAPIKey, IAdminLayer, APIKeyPropertiesEditForm),
                provides=IGroup)
class APIKeyPropertiesEditFormRequestParamsGroup(FormGroupChecker):
    """API key properties edit form request params group"""

    fields = Fields(IAPIKey).select('allowed_as_request_param', 'request_param_name')
    weight = 20


@adapter_config(required=(IAPIKey, IAdminLayer, APIKeyPropertiesEditForm),
                provides=IAJAXFormRenderer)
class APIKeyPropertiesEditFormRenderer(ContextRequestViewAdapter):
    """API key properties edit form renderer"""

    def render(self, changes):
        """JSON form renderer"""
        if not changes:
            return None
        sm = get_utility(ISecurityManager)
        return {
            'status': 'success',
            'message': self.request.localizer.translate(self.view.success_message),
            'callbacks': [
                get_json_table_row_refresh_callback(sm, self.request,
                                                    IAPIKeyContainerTable, self.context)
            ]
        }
