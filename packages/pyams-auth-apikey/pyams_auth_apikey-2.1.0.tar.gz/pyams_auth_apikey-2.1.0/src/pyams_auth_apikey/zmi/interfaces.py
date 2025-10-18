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

"""PyAMS_auth_apikey.zmi.interfaces module

This module defines interfaces used by management interface.
"""

from zope.interface import Interface


__docformat__ = 'restructuredtext'


class IAPIKeyConfigurationMenu(Interface):
    """API key configuration menu marker interface"""


class IAPIKeyContainerTable(Interface):
    """API key configuration table marker interface"""
