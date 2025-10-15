from datetime import datetime
import os
import glob
from humalab.assets.files.resource_file import ResourceFile
from humalab.assets.archive import extract_archive


class URDFFile(ResourceFile):
    def __init__(self, 
                 name: str, 
                 version: int,
                 filename: str,
                 urdf_filename: str | None = None,
                 description: str | None = None,
                 created_at: datetime | None = None,):
        super().__init__(name=name, 
                         version=version,
                         description=description,
                         filename=filename,
                         resource_type="URDF", 
                         created_at=created_at)
        self._urdf_base_filename = urdf_filename
        self._urdf_filename, self._root_path = self._extract()
        self._urdf_filename = os.path.join(self._urdf_filename, self._urdf_filename)
        
    def _extract(self):
        working_path = os.path.dirname(self._filename)
        if not os.path.exists(working_path):
            _, ext = os.path.splitext(self._filename)
            ext = ext.lstrip('.')  # Remove leading dot
            if ext.lower() != "urdf":
                extract_archive(self._filename, working_path)
                try:
                    os.remove(self._filename)
                except Exception as e:
                    print(f"Error removing saved file {self._filename}: {e}")
        local_filename = self.search_resource_file(self._urdf_base_filename, working_path)
        if local_filename is None:
            raise ValueError(f"Resource filename {self._urdf_base_filename} not found in {working_path}")
        return local_filename, working_path

    def search_resource_file(self, resource_filename: str | None, working_path: str) -> str | None:
        found_filename = None
        if resource_filename:
            search_path = os.path.join(working_path, "**")
            search_pattern = os.path.join(search_path, resource_filename)
            files = glob.glob(search_pattern, recursive=True)
            if len(files) > 0:
                found_filename = files[0]
        
        if found_filename is None:
            ext = "urdf"
            search_pattern = os.path.join(working_path, "**", f"*.{ext}")
            files = glob.glob(search_pattern, recursive=True)
            if len(files) > 0:
                found_filename = files[0]
        return found_filename

    @property
    def urdf_filename(self) -> str | None:
        return self._urdf_filename
    
    @property
    def root_path(self) -> str:
        return self._root_path
