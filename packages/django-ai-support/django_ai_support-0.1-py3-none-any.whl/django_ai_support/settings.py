from django.conf import settings
from django.test.signals import setting_changed

from rest_framework.settings import APISettings


USER_SETTINGS = getattr(settings, "AI_SUPPORT_SETTINGS", None)

DEFAULTS = {
    "TOOLS": [],
    "SYSTEM_PROMPT": "You are the supporter of a bookstore website.",
    "LLM_MODEL": None,
}


api_settings = APISettings(USER_SETTINGS, DEFAULTS)

raw_model = api_settings.LLM_MODEL

if not api_settings.LLM_MODEL:
    raise ValueError("LLM_MODEL can not be None")


def update_model_with_tools():
    """
    If the length of TOOLS is greater than 0, update the LLM model with bind tools.
    Otherwise, use raw_model
    """

    if settings.AI_SUPPORT_SETTINGS["TOOLS"]: 
        api_settings.LLM_MODEL = raw_model.bind_tools(api_settings.TOOLS)
    else:
        api_settings.LLM_MODEL = raw_model


if api_settings.TOOLS:
    update_model_with_tools()


def reload_api_settings(*args, **kwargs):
    global api_settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting == "AI_SUPPORT_SETTINGS":
        api_settings = APISettings(value, DEFAULTS)


setting_changed.connect(reload_api_settings)

