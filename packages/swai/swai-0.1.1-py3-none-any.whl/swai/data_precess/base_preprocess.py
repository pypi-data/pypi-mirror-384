from os.path import isdir
import zipfile
import os
from pathlib import Path

class BasePreprocess:
    def process(self):
        raise NotImplementedError("Subclasses must implement this method")

    def pack(self, data_path):
        if os.path.isdir(data_path):
            data_dir = data_path
            data_path = Path(data_dir)
            if not data_path.exists():
                raise ValueError(f"Data directory {data_dir} does not exist")
            
            zip_path = data_path.parent / f"{data_path.name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Store files with relative path to data_dir
                        arcname = os.path.relpath(file_path, data_dir)
                        zipf.write(file_path, arcname)
        else:
            
            data_path = Path(data_path)
            if not data_path.exists():
                raise ValueError(f"Data directory {data_path} does not exist")
            
            zip_path = data_path.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                arcname = data_path.name
                zipf.write(data_path, arcname)
            
        return str(zip_path)