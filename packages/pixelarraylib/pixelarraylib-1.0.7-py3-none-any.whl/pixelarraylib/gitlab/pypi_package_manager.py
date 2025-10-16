import requests
from typing import List, Optional


class GitLabPyPIPackageManager:
    def __init__(self, project_id: str, token: str, api_version: str = "v4"):
        self.gitlab_url = "https://gitlab.com"
        self.project_id = project_id
        self.token = token
        self.api_version = api_version
        self.base_url = f"{self.gitlab_url}/api/{api_version}/projects/{project_id}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _find_package_id(self, package_name: str, package_version: str) -> str:
        url = f"{self.base_url}/packages"
        params = {
            "package_type": "pypi",
            "package_name": package_name,
            "package_version": package_version,
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            for package in response.json():
                if (
                    package["name"] == package_name
                    and package["version"] == package_version
                ):
                    return package["id"]
        return None

    def list_packages(self) -> List[str]:
        url = f"{self.base_url}/packages"
        params = {"package_type": "pypi"}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def list_package_versions(self, package_name: str) -> List[str]:
        url = f"{self.base_url}/packages"
        params = {"package_type": "pypi", "package_name": package_name}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return [version["version"] for version in response.json()]
        else:
            return []

    def delete_package(self, package_name: str, package_version: str):
        package_id = self._find_package_id(package_name, package_version)
        if package_id is None:
            raise ValueError(f"Package {package_name} {package_version} not found")
        url = f"{self.base_url}/packages/{package_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 200:
            return True
        else:
            return False
