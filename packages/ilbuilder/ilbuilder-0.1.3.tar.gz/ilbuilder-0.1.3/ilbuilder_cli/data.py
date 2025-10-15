from ilbuilder.data import IlBuilderData


class PackageData(IlBuilderData):
    FILENAME = "ilbuilder-package.json"

    PROPERTY = {
        "name": {
            "type": "str",
            "generate": True,
            "default": "$name"
        },
        "venv": {
            "type": "str",
            "generate": True,
            "default": ".venv"
        },
        "version": {
            "type": "str",
            "generate": True,
            "default": ""
        },
        "main": {
            "type": "str",
            "generate": True,
            "default": "run.py"
        },
        "console": {
            "generate": True,
            "default": False,
        },
        "auto_run": {},
        "icon": {},
        "onefile": {},
        "assets": {},
        "in_assets": {},
        "exclude_commands": {},
    }
