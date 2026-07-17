import os
import json
import shutil

class ExtensionManager:
    def __init__(self, ide):
        self.ide = ide
        self.marketplace = "Marketplace/extensions"
        self.installed = "Extensions"
        os.makedirs(self.marketplace, exist_ok=True)
        os.makedirs(self.installed, exist_ok=True)
    def get_extensions(self):
        result = []
        for folder in os.listdir(self.marketplace):
            path = os.path.join(
                self.marketplace,
                folder
            )
            if os.path.isdir(path):

                info_file = os.path.join(
                    path,
                    "extension.json"
                )
                if os.path.exists(info_file):

                    with open(info_file) as f:
                        result.append(
                            json.load(f)
                        )
        return result
    def install(self, name):
        source = os.path.join(
            self.marketplace,
            name
        )
        destination = os.path.join(
            self.installed,
            name
        )
        if os.path.exists(destination):
            return False
        shutil.copytree(
            source,
            destination
        )
        return True
    def uninstall(self, name):
        path = os.path.join(
            self.installed,
            name
        )
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
    return False