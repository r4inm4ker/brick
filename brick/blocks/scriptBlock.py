from brick.attrtype import Script
from brick.base import Generic


class ScriptBlock(Generic):
    ui_order = 010
    ui_icon_name = "python_script.svg"
    fixedAttrs = (('func', (Script, '')),)

    def _execute(self):
        locals().update(self.runTimeAttrs)

        oldLocals = {}
        for key, val in locals().iteritems():
            oldLocals[key] = val

        func = self.runTimeAttrs.get('func')

        if not func:
            return

        exec func

        addedLocals = {}

        for key, val in locals().iteritems():
            if key not in oldLocals:
                addedLocals[key] = val

        for key, val in addedLocals.iteritems():
            setattr(self, key, val)
