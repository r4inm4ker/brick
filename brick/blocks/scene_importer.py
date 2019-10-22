from brick.base import Custom

class MayaSceneImporter(Custom):
    ui_order = 30
    ui_icon_name = "import.png"
    fixedAttrs = (('sceneFile', (str, '')),)

    def _execute(self):
        locals().update(self.runTimeAttrs)

        sceneFile = self.attrs.get('sceneFile')

        # getting runTimeAttrs
        options = self.runTimeAttrs.get("options", None)

        import maya.cmds as mc
        mc.file(sceneFile, i=1)

        self.results = None


