from ilbuilder_cli.build import IlBuilderTool


def build(args):
    name = getattr(args, "name", None)

    if name:
        script = getattr(args, "script", None)
        b = IlBuilderTool(name, script)
        b.build()

    b = IlBuilderTool.from_data()
    b.build()
