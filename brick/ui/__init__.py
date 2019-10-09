from brick.lib.path import Path
import brick

icon_dir = Path(brick.__file__).dirname() / "ui" / "icons"

from qqt import IconManager
IconManager.addDir(icon_dir)
