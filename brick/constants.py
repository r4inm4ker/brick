import os


class BuildStatus(object):
    nothing = 0
    success = 1
    fail = 2
    next = 3
    end = 4


BLUEPRINT_EXTENSION = '.bpt'

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
