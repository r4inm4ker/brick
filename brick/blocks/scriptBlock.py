from brick import attr_type
from brick.base import Generic, Custom


class ScriptBlock(Generic):
    ui_order = 010
    ui_icon_name = "python_script.svg"
    fixedAttrs = (('script', (attr_type.Script, '')),)

    def _execute(self):
        locals().update(self.runTimeAttrs)

        oldLocals = {}
        for key, val in locals().iteritems():
            oldLocals[key] = val

        func = self.runTimeAttrs.get('script')

        if not func:
            return

        exec func

        addedLocals = {}

        for key, val in locals().iteritems():
            if key not in oldLocals:
                addedLocals[key] = val

        for key, val in addedLocals.iteritems():
            setattr(self, key, val)


# from brick.lib import classproperty
class TestScriptBlock(Custom):
    ui_order=510
    ui_icon_name = "python_script.svg"
    fixedAttrs = (('script', (attr_type.Script, '')),)

    def _execute(self):
        locals().update(self.runTimeAttrs)

        oldLocals = {}
        for key, val in locals().iteritems():
            oldLocals[key] = val

        func = self.runTimeAttrs.get('script')

        func = 'print "RUN {}"'.format(self.name)

        if not func:
            return

        exec func

        addedLocals = {}

        for key, val in locals().iteritems():
            if key not in oldLocals:
                addedLocals[key] = val

        for key, val in addedLocals.iteritems():
            setattr(self, key, val)

    # @classproperty
    # def fixedAttrs(cls):
    #     return (('func', (Script, 'print "{name}"'.format(cls.name))),)