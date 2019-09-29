from os.path import expanduser
from lib.path import Path
from collections import OrderedDict
import json

from brick.base import log


class Settings(object):
    Last_Opened_Dir = 'last_opened_directory'
    Recent_Files = 'recent_files'
    Max_Files_Length = 15


def getSettingsDir():
    homeDir = Path(expanduser("~"))

    settingsDir = homeDir / ".brick"

    if not settingsDir.exists():
        settingsDir.mkdir()

    return settingsDir


def getHistoryFile():
    return getSettingsDir() / "history.json"


def writeHistoryFile(data):
    historyFile = getHistoryFile()
    try:
        json.dumps(data)

    except:
        log.warn("error when trying to serialize data: {}".format(data))

    else:
        with open(historyFile, "w") as fd:
            json.dump(data, fd, indent=4)

        log.info("updating setting file: {}".format(historyFile))


def getHistoryData():
    data = {}
    historyFile = getHistoryFile()
    if historyFile.exists():
        with open(historyFile, "r") as fd:
            data = json.load(fd, object_pairs_hook=OrderedDict)

    for idx, filePath in enumerate(data.get(Settings.Recent_Files, [])):
        data[Settings.Recent_Files][idx] = Path(filePath).normcase()

    return data


def getRecentBlueprint():
    data = getHistoryData()

    recentFiles = data.get(Settings.Recent_Files, [])

    return recentFiles


def getLastOpenedDir():
    data = getHistoryData()

    lastDir = data.get(Settings.Last_Opened_Dir, None)

    return lastDir


def addRecentBlueprint(filePath):
    filePath = Path(filePath).normcase()
    data = getHistoryData()

    files = [Path(each) for each in data.get(Settings.Recent_Files, [])]
    if not files:
        data[Settings.Recent_Files] = []

    index = -1
    for idx, each in enumerate(files):
        if str(filePath) == str(each):
            index = idx
            break

    if index >= 0:
        data[Settings.Recent_Files].pop(index)

    data[Settings.Recent_Files].append(str(filePath.normcase()))

    if len(data[Settings.Recent_Files]) > Settings.Max_Files_Length:
        data[Settings.Recent_Files] = data[Settings.Recent_Files][1:]

    writeHistoryFile(data)
