from brick.base import Generic

class MayaSceneImporter(Generic):
    ui_order = 030
    fixedAttrs = (('sceneFile', (str, '')),)

    def _execute(self):
        locals().update(self.runTimeAttrs)

        sceneFile = self.attrs.get('sceneFile')

        # getting runTimeAttrs
        options = self.runTimeAttrs.get("options", None)

        import maya.cmds as mc
        mc.file(sceneFile, i=1)

        self.results = None


