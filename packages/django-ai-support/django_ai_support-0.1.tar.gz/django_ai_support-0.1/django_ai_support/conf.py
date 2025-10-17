from django.conf import settings

from .settings import update_model_with_tools

def append_tools(*tools):
    """
    Append the list of tools to the settings and update your model to use these tools.
    """

    for tool in tools:
        settings.AI_SUPPORT_SETTINGS["TOOLS"].append(tool)
    update_model_with_tools()


def remove_tools(*tools):
    """
    Remove the list of tools from the settings and update your model to use these tools.
    """

    for tool in tools:
        settings.AI_SUPPORT_SETTINGS["TOOLS"].remove(tool)

    update_model_with_tools()

