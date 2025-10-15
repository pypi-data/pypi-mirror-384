from pathlib import Path

from ilbuilder_cli.command import *


def add(app):
    def add_build():
        app.add_command("build")
        app.set_sub_main_func('build', build)

        app.add_sub_argument('build', 'name', nargs='?')
        app.add_sub_argument('build', '--script', "-s")

    def add_clean():
        app.add_command("clean")
        app.set_sub_main_func('clean', lambda _: IlBuilderTool.clean())

    def add_cwd():
        app.add_command("cwd")
        app.set_sub_main_func('cwd', lambda _: print(f"{Path.cwd()} | {Path.absolute(Path('.'))}"))

    add_build()
    add_clean()
    add_cwd()
