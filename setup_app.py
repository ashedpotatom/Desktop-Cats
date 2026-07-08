from pathlib import Path
import os

from setuptools import setup


APP_NAME = os.environ.get("APP_NAME", "Desktop Cats")
BUNDLE_ID = os.environ.get("BUNDLE_ID", "com.example.desktopcats")
VERSION = os.environ.get("APP_VERSION", "1.0.0")


def collect_data_files(root):
    root_path = Path(root)
    return [
        (str(path.parent), [str(path)])
        for path in root_path.rglob("*")
        if path.is_file()
    ]


DATA_FILES = collect_data_files("Assets") + [
    ("", ["README.md", "ASSET_CREDITS.md"]),
]

OPTIONS = {
    "argv_emulation": False,
    "packages": ["pygame"],
    "includes": ["AppKit", "Foundation", "Quartz"],
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": os.environ.get("BUILD_NUMBER", "1"),
        "LSMinimumSystemVersion": os.environ.get("MIN_MACOS_VERSION", "12.0"),
        "LSUIElement": True,
        "NSHumanReadableCopyright": os.environ.get(
            "APP_COPYRIGHT",
            "Copyright © 2026",
        ),
        "NSHighResolutionCapable": True,
    },
}


setup(
    app=["main.py"],
    name=APP_NAME,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
