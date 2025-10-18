======================
PyAMS API keys package
======================

.. contents::


What is PyAMS?
==============

PyAMS (Pyramid Application Management Suite) is a small suite of packages written for applications
and content management with the Pyramid framework.

**PyAMS** is actually mainly used to manage web sites through content management applications (CMS,
see PyAMS_content package), but many features are generic and can be used inside any kind of web
application.

All PyAMS documentation is available on `ReadTheDocs <https://pyams.readthedocs.io>`_; source code
is available on `Gitlab <https://gitlab.com/pyams>`_ and pushed to `Github
<https://github.com/py-ams>`_. Doctests are available in the *doctests* source folder.


What is PyAMS API keys?
=======================

PyAMS API keys is an extension module which can be used to allow API keys as authentication
credentials.

Each defined API key is seen as a classic *principal* to which you can grant roles as usual.
An API key can be defined with an expiration date, and can be revoked or deleted at any time
by an administrator.

An API key can also be bound to a specific principal; in this case, using this API key will
be equivalent to being connected with the matching principal credentials.

At first, API keys can only be provided using a specific HTTP header which can be configured
for all keys; maybe other authentication modes will be provided in future versions.
