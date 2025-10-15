===========
EOX Tagging
===========
|Maintainance Badge| |Test Badge| |PyPI Badge|

.. |Maintainance Badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
   :alt: Maintainance Status
.. |Test Badge| image:: https://img.shields.io/github/actions/workflow/status/edunext/eox-tagging/.github%2Fworkflows%2Ftests.yml?label=Test
   :alt: GitHub Actions Workflow Test Status
.. |PyPI Badge| image:: https://img.shields.io/pypi/v/eox-tagging?label=PyPI
   :alt: PyPI - Version

Eox-tagging is an `openedx plugin`_, part of the Edunext Open edX Extensions (aka EOX), that adds the capability
to tag `edx-platform`_ objects. These tags can be used to categorize, include extra information, and so on.

Installation
============

#. Add this plugin in your Tutor ``config.yml`` with the ``OPENEDX_EXTRA_PIP_REQUIREMENTS`` setting.

   .. code-block:: yaml
      
      OPENEDX_EXTRA_PIP_REQUIREMENTS:
         - eox-tagging=={{version}}
         
#. Save the configuration with ``tutor config save``.
#. Build the image and launch your platform with ``tutor local launch``.

Compatibility Notes
--------------------

+------------------+---------------+
| Open edX Release | Version       |
+==================+===============+
| Ironwood         | < 0.9 < 3.0   |
+------------------+---------------+
| Juniper          | >= 0.9 < 3.0  |
+------------------+---------------+
| Koa              | >= 2.2 < 5.0  |
+------------------+---------------+
| Lilac            | >= 2.2 < 5.0  |
+------------------+---------------+
| Maple            | >= 4.0 < 6.0  |
+------------------+---------------+
| Nutmeg           | >= 5.0 < 6.0  |
+------------------+---------------+
| Olive            | >= 5.0 < 6.0  |
+------------------+---------------+
| Palm             | >= 6.0 < 8.0  |
+------------------+---------------+
| Quince           | >= 7.0 < 9.0  |
+------------------+---------------+
| Redwood          | >= 7.2.0      |
+------------------+---------------+
| Sumac            | >= 9.0.0      |
+------------------+---------------+
| Teak             | >= 9.1.0      |
+------------------+---------------+
| Ulmo             | >= 9.3.0      |
+------------------+---------------+

The plugin is configured for the latest release (Teak). The following changes in the plugin settings should be applied to be used for previous releases.
Those settings can be changed in `eox_tagging/settings/common.py`` or, for example, in the instance configurations.


🚨 If the release you are looking for is not listed, please note:

- If the Open edX release is compatible with the current eox-tagging version (see `Compatibility Notes <https://github.com/eduNEXT/eox-tagging?tab=readme-ov-file#compatibility-notes>`_), the default configuration is sufficient.
- If incompatible, you can refer to the README from the relevant version tag for configuration details (e.g., `v5.1.0 README <https://github.com/eduNEXT/eox-tagging/blob/v5.1.0/README.rst>`_).

Usage
======

See the `How to section <https://github.com/eduNEXT/eox-tagging/tree/master/docs/how_to>`_ for detailed guidance on model, configurations and API usage.

Important notes:
----------------

* All the comparisons with string objects are case insensitive.
* If a tag owner is not defined, then it is assumed to be the site.

Examples
--------

**Example 1:**

.. code-block:: JSON

        {
            "validate_tag_value": {
                "in": [
                    "example_tag_value",
                    "example_tag_value_1"
                ]
            },
            "validate_access": {
                "equals": "PRIVATE"
            },
            "validate_target_object": "OpaqueKeyProxyModel",
            "owner_object": "User",
            "tag_type": "tag_by_example"
        }

This means that:

* Tag value must be in the array
* The field access must be equal to `private`
* The target type must be equal to `CourseOverview`
* The owner type must be equal to `User`
* Tag_type must be equal to `tag_by_example`

**Example 2:**

.. code-block:: JSON

        {
            "validate_tag_value": {
                "exist": true
            },
            "validate_access": "Public",
            "validate_target_object": "User",
            "tag_type": "tag_by_edunext"
        }

This means that:

* The tag value must exist, it can take any value.
* The field access must be equal to `public`.
* The target type must be equal to `User`.
* Tag type must be equal to tag_by_edunext.

**Example 3:**

.. code-block:: JSON

        {
            "validate_tag_value": "tag_value",
            "validate_access": {
                "in": [
                    "Private",
                    "Public"
                ]
            },
            "validate_target_object": "CourseEnrollment",
            "tag_type": "tag_by_edunext",
            "validate_activation_date": {
                "exist": true,
                "in": [
                    "Dec 04 2020 10:30:40",
                    "Oct 19 2020 10:30:40"
                ]
            }
        }

This means that:

* The tag value must be equal to tag_value.
* The field access can be `private` or `public`.
* The target type must be equal to `CourseEnrollment`
* Tag type must be equal to tag_by_edunext.
* The tag activation date must exist between the values defined in the array. This means, value_1 <= activation_date <= value_2.
  The array must be sorted or a validation error will be raised.

Tagging REST API
================

Get a list of tags
------------------

**Request**

``curl -H 'Accept: application/json' -H "Authorization: Bearer AUTHENTICATION_TOKEN" http://BASE_URL_SITE/eox-tagging/api/v1/tags/``

**Response**

.. code-block:: JSON

        {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "meta": {
                        "created_at": "2020-07-10T13:25:54.057846Z",
                        "target_id": 2,
                        "target_type": "User",
                        "inactivated_at": null,
                        "owner_type": "User",
                        "owner_id": 7
                    },
                    "key": "55a20579-ce8e-4f0b-830e-78fe79adac46",
                    "tag_value": "tag_value",
                    "tag_type": "tag_by_edunext",
                    "access": "PUBLIC",
                    "activation_date": "2020-12-04T15:20:30Z",
                    "expiration_date": null,
                    "status": "ACTIVE"
                },
                {
                    "meta": {
                        "created_at": "2020-07-10T13:33:44.277374Z",
                        "target_id": 2,
                        "target_type": "User",
                        "inactivated_at": null,
                        "owner_type": "Site",
                        "owner_id": 1
                    },
                    "key": "2bec10f5-a9e0-4e42-9c24-f9643bb13537",
                    "tag_value": "tag_value",
                    "tag_type": "tag_by_edunext",
                    "access": "PUBLIC",
                    "activation_date": "2020-12-04T15:20:30Z",
                    "expiration_date": null,
                    "status": "ACTIVE"
                },
            ]
        }

Create tag
----------

**Request**

``curl -H 'Accept: application/json' -H "Authorization: Bearer AUTHENTICATION_TOKEN" --data TAG_DATA http://BASE_URL_SITE/eox-tagging/api/v1/tags/``

Where TAG_DATA:

.. code-block:: JSON

        {
            "tag_type": "tag_by_edunext",
            "tag_value": "tag_value",
            "target_type": "user",
            "target_id": "edx",
            "access": "public",
            "owner_type": "user",
            "activation_date": "2020-12-04 10:20:30"
        }


**Response**:

``Status 201 Created``

.. code-block:: JSON

        {
            "meta": {
                "created_at": "2020-07-10T13:25:54.057846Z",
                "target_id": 2,
                "target_type": "User",
                "inactivated_at": null,
                "owner_type": "User",
                "owner_id": 7
            },
            "key": "55a20579-ce8e-4f0b-830e-78fe79adac46",
            "tag_value": "tag_value",
            "tag_type": "tag_by_edunext",
            "access": "PUBLIC",
            "activation_date": "2020-12-04T10:20:30-05:00",
            "expiration_date": null,
            "status": "ACTIVE"
        }

Delete tag
----------

**Request**

``curl -X DELETE  http://BASE_URL_SITE/eox-tagging/api/v1/tags/EXISTING_KEY_TAG/``

**Response**

``Status 204 No Content``


Filters example usage:
----------------------

``/eox_tagging/api/v1/tags/?target_type=MODEL_TYPE``

``/eox_tagging/api/v1/tags/?course_id=COURSE_ID``

``/eox_tagging/api/v1/tags/?username=USERNAME``

``/eox_tagging/api/v1/tags/?access=ACCESS_TYPE``

``/eox_tagging/api/v1/tags/?enrollments=COURSE_ID``

Auditing Django views
=====================

The majority of views in eox-tagging use an auditing decorator, defined in our custom library called `eox-audit-model`_,
that helps save relevant information about non-idempotent operations. By default, this functionality is turned off, to enable it, install eox-audit-model. 

Check your auditing records in *Django sysadmin > DJANGO EDUNEXT AUDIT MODEL*.

For more information, check the eox-audit-model documentation.

.. _openedx plugin: https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/plugins
.. _edx-platform: https://github.com/openedx/edx-platform/
.. _eox-audit-model: https://github.com/eduNEXT/eox-audit-model/

How to Contribute
=================

Contributions are welcome! See our `CONTRIBUTING`_ file for more
information – it also contains guidelines for how to maintain high code
quality, which will make your contribution more likely to be accepted.

.. _CONTRIBUTING: https://github.com/eduNEXT/eox-tagging/blob/master/CONTRIBUTING.rst


License
=======

This project is licensed under the AGPL-3.0 License. See the LICENSE file for details.
