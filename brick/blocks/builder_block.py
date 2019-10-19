from brick.base import Generic, GenericBuilder
from brick.constants import BuildStatus

from brick import attr_type

class BuildError(Exception):
    pass


class BuilderBlock(Generic):
    ui_order = 020
    ui_icon_name = "generic_block.png"
    fixedAttrs = (
        ('blueprint', (attr_type.Path, '')),
    )


    def _execute(self):
        locals().update(self.runTimeAttrs)

        attrType, blueprintName = self.attrs.get('blueprint')

        builder = GenericBuilder.loadBlueprint(blueprintName)

        builder.fastForward()

        for block in builder.blocks:
            if block.buildStatus == BuildStatus.fail:
                raise BuildError("error in one or more building blocks.")
