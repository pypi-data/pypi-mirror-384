"""
This module contains tests for the backends of the edxapp_wrapper.
"""


# pylint: disable=import-outside-toplevel,unused-import
def test_current_settings_code_imports():
    """
    Running this imports means that our backends import the right signature
    """
    import eox_tagging.edxapp_wrappers.backends.bearer_authentication_i_v1
    import eox_tagging.edxapp_wrappers.backends.course_overview_i_v1
    import eox_tagging.edxapp_wrappers.backends.enrollment_l_v1
