import sys

try:
    from newapi import ALL_APIS  # noqa: F401
except ImportError:
    sys.path.insert(0, "I:/core/bots/new/newapi_bot")
    from newapi import ALL_APIS  # noqa: F401
