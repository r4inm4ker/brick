from brick.base import Generic, RigBuilder
from brick.constants import BuildStatus


class BuildError(Exception):
    pass


class BuilderBlock(Generic):
    fixedAttrs = (('type', (str, 'RigBuilder')),
                  ('blueprint', (str, ''))
    )

    def _execute(self):
        locals().update(self.runTimeAttrs)

        blueprintName = self.attrs.get('blueprint')

        builder = RigBuilder.loadBlueprint(blueprintName)

        builder.fastForward()

        for block in builder.blocks:
            if block.buildStatus == BuildStatus.fail:
                raise BuildError("error in one or more building blocks.")
