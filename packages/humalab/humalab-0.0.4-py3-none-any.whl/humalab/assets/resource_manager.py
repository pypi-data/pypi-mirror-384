from humalab.assets.files.resource_file import ResourceFile
from humalab.humalab_config import HumalabConfig
from humalab.humalab_api_client import HumaLabApiClient
from humalab.assets.files.urdf_file import URDFFile
import os
from typing import Any


class ResourceManager:
    def __init__(self,
                 api_key: str | None = None,
                 host: str | None = None,
                 timeout: float | None = None):
        self._humalab_config = HumalabConfig()
        self._base_url = host or self._humalab_config.base_url
        self._api_key = api_key or self._humalab_config.api_key
        self._timeout = timeout or self._humalab_config.timeout

        self._api_client = HumaLabApiClient(base_url=self._base_url,
                                      api_key=self._api_key,
                                      timeout=self._timeout)
        
    def _asset_dir(self, name: str, version: int) -> str:
        return os.path.join(self._humalab_config.workspace_path, "assets", name, f"{version}")
    
    def _create_asset_dir(self, name: str, version: int) -> bool:
        asset_dir = self._asset_dir(name, version)
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir, exist_ok=True)
            return True
        return False

    def download(self,
                 name: str, 
                 version: int | None=None) -> Any:
        resource = self._api_client.get_resource(name=name, version=version)
        file_content = self._api_client.download_resource(name="lerobot")
        filename = os.path.basename(resource['resource_url'])
        filename = os.path.join(self._asset_dir(name, resource["version"]), filename)
        if self._create_asset_dir(name, resource["version"]):
            with open(filename, "wb") as f:
                f.write(file_content)
        
        if resource["resource_type"].lower() == "urdf":
            return URDFFile(name=resource["name"],
                            version=resource["version"],
                            description=resource.get("description"),
                            filename=filename,
                            urdf_filename=resource.get("filename"),
                            created_at=resource.get("created_at"))

        return ResourceFile(name=name, 
                            version=resource["version"], 
                            filename=filename,
                            resource_type=resource["resource_type"],
                            description=resource.get("description"),
                            created_at=resource.get("created_at"))