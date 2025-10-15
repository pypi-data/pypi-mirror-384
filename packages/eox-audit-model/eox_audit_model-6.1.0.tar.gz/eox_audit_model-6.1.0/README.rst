===================
Edunext Audit Model
===================

|Maintainance Badge| |Test Badge| |PyPI Badge|

.. |Maintainance Badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
   :alt: Maintainance Status
.. |Test Badge| image:: https://img.shields.io/github/actions/workflow/status/edunext/eox-audit-model/.github%2Fworkflows%2Ftests.yml?label=Test
   :alt: GitHub Actions Workflow Test Status
.. |PyPI Badge| image:: https://img.shields.io/pypi/v/eox-audit-model?label=PyPI
   :alt: PyPI - Version
   
Eox-audit-model is a Django application designed to provide an audit model for tracking and logging changes within the Open edX platform.
This plugin saves information in the database about executed methods, creating a detailed audit trail of various operations. Developed as part of
the Edunext Open edX Extensions (EOX), **eox-audit-model** assists administrators and developers in maintaining comprehensive monitoring and ensuring
better oversight of the platform's activities.

Features
========

- **Detailed Audit Logging**: Capture comprehensive logs of method executions, including parameters, results, and any generated logs.
- **Automatic Traceback Capture**: Automatically log traceback information if an exception occurs during method execution.
- **User Tracking**: Record the user who initiated the method, providing accountability and traceability.
- **Flexible Logging Mechanisms**: Log actions either by directly calling a method or using a decorator for convenience.
- **Customizable Notes**: Add custom notes to logs for additional context and information.
- **Comprehensive Monitoring**: Maintain an extensive audit trail for better monitoring and oversight of platform activities.

Installation
============

1. Install eox-audit-model in Tutor with `OPENEDX_EXTRA_PIP_REQUIREMENTS`` setting in the `config.yml`:

   .. code-block:: yml
      
      OPENEDX_EXTRA_PIP_REQUIREMENTS:
         - eox-audit-model=={{version}}

2. Add eox_audit_model to `INSTALLED_APPS``, you can create a `Tutor plugin <https://docs.tutor.edly.io/tutorials/plugin.html>`_, e.g.:

   .. code-block:: yml
      
      from tutor import hooks

      hooks.Filters.ENV_PATCHES.add_item(
         (
            "openedx-lms-common-settings",
            "settings.INSTALLED_APPS.append('eox_audit_model.apps.EoxAuditModelConfig')"
         )
      )     

3. Save the configuration with ``tutor config save``.

4. Build the image and launch your platform with ``tutor local launch``.

Compatibility notes
-------------------

+------------------+---------------+
| Open edX Release | Version       |
+==================+===============+
| Juniper          | >=0.2, <0.4   |
+------------------+---------------+
| Koa              | >=0.4, <=0.7  |
+------------------+---------------+
| Lilac            | >=0.4, <=0.7  |
+------------------+---------------+
| Maple            | >=0.7, <1.0   |
+------------------+---------------+
| Nutmeg           | >=1.0, <5.0   |
+------------------+---------------+
| Olive            | >=2.0, <5.0   |
+------------------+---------------+
| Palm             | >=3.0, <5.0   |
+------------------+---------------+
| Quince           | >=4.0, <6.0   |
+------------------+---------------+
| Redwood          | >=4.2.0       |
+------------------+---------------+
| Sumac            | >=5.1.0       |
+------------------+---------------+
| Teak             | >=6.0.0       |
+------------------+---------------+
+------------------+---------------+
| Ulmo             | >=6.1.0       |
+------------------+---------------+

Usage
=====

Eox-audit-model can be used to audit any execution of a method or function. This will create a database record with the following information:

- **Status**: If the process was successful or not.
- **Action**: The given string to identify the process.
- **Timestamp**: The execute date.
- **Method name**: Method or function name.
- **Captured log**: Logs generated in the execution.
- **Traceback log**: If there is an exception, this will contain the traceback.
- **Site**: Current site.
- **Performer**: The user who started the method; depends on the *request.user*.
- **Input**: The values used to execute the method.
- **Output**: The value returned by the method.
- **Ip**: Current IP.

There are two primary ways to use the plugin:

Direct Method Call
------------------

You can log an action directly by importing the model and calling the `execute_action` method. This method requires several parameters to log the information:

- `action`: A string describing the action, e.g., `'Add view info'`.
- `method`: The method being executed.
- `parameters`: A dictionary containing positional arguments (`args`) and keyword arguments (`kwargs`).
- `notes`: An optional list of dictionaries for storing custom information.

Example:

.. code-block:: python

  from eox_audit_model.models import AuditModel

  def any_method(parameter1, parameter2, parameter3):
    """Do something"""
    return 'Success'

  def audit_process():
    """Execute audit process"""
    action = "This is a simple action"
    parameters = {
      "args": (2, 6),
      "kwargs": {"parameter3": 9},
    }

    expected_value = AuditModel.execute_action(action, any_method, parameters)
    ...

Using the Decorator
-------------------

The plugin also provides a decorator that can be used to log method executions automatically. The decorator
handles calling the `execute_action` method behind the scenes and saves the information for you.

Example:

.. code-block:: python

  from eox_audit_model.decorators import audit_method

  @audit_method(action="This is a simple action")
  def any_method(parameter1, parameter2, parameter3):
    """Do something"""
    return 'Success'

  def audit_process():
    """Execute audit process"""
    expected_value = any_method(3, 6, 9)
    ...

License
=======

This software is licensed under the terms of the AGPLv3. See the LICENSE file for details.
