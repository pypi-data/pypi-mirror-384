import os
import json
from setuptools import setup, find_namespace_packages
from dataclasses import dataclass


OGD_TARGET_PROJECT = os.environ.get(
    "OGD_TARGET_PROJECT",
    default="main",
)


@dataclass(frozen=True, slots=True)
class OGDProject:
    name: str
    codebase_path: str
    configs_path: str
    spec_path: str
    readme_path: str

    @classmethod
    def project_names(cls) -> list[str]:
        return [
            proj for proj in os.listdir(os.path.join("src", "configs"))
            if os.path.isdir(os.path.join("src", "configs", proj))
        ]

    @classmethod
    def projects(cls) -> dict[str, "OGDProject"]:
        return {
            proj: cls(
                name=proj,
                codebase_path=os.path.join("src", proj),
                configs_path=os.path.join("src", "configs", proj),
                spec_path=os.path.join("src", "configs", proj, "spec.json"),
                readme_path=os.path.join("src", "configs", proj, "README.md"),
            )
            for proj in cls.project_names()
        }

    @property
    def readme(self) -> str:
        with open(self.readme_path, "r") as file:
            return file.read()
        
    @property
    def spec(self) -> dict:
        with open(self.spec_path, "r") as file:
            return json.load(file)
    
    @property
    def package_name(self) -> str:
        return self.spec.get("name", f"fred-ogd-{self.name}")

    @property
    def version_filepath(self) -> str:
        return os.path.join(
            self.codebase_path,
            "fred",
            "ogd", 
            "" if self.name == "main" else self.name,
            "version"
        )

    @property
    def version(self) -> str:
        with open(self.version_filepath, "r") as file:
            return file.read().strip()

    @property
    def major_version(self) -> int:
        major, *_ = self.version.split(".")
        return int(major)
    @property
    def requirements(self) -> list[str]:
        return self.spec.get("requirements", [])


ogd_projects = OGDProject.projects()

if OGD_TARGET_PROJECT not in ogd_projects.keys():
    raise ValueError(
        f"OGD_PROJECT '{OGD_TARGET_PROJECT}' is not valid. Available projects: {ogd_projects.keys()}"
    )

ogd_project = ogd_projects[OGD_TARGET_PROJECT]


setup(
    name=ogd_project.package_name,
    version=ogd_project.version,
    description=f"FRED-OGD: {ogd_project.name.upper()}",
    long_description=ogd_project.readme,
    long_description_content_type='text/markdown',
    url="https://ogd.fred.fahera.mx",
    author="Fahera Research, Education, and Development",
    author_email="fred@fahera.mx",
    packages=find_namespace_packages(where=ogd_project.codebase_path),
    package_dir={
        "": ogd_project.codebase_path
    },
    package_data={
        "": [
            ogd_project.version_filepath,
            "**/*.json",
            "**/*.yaml",
        ]
    },
    install_requires=ogd_project.requirements,
    extras_require={
        "standalone": [
            f"fred-ogd<={ogd_projects['main'].major_version + 1}.0.0" 
        ]
    } if OGD_TARGET_PROJECT != "main" else {
        key: [f"{proj.package_name}<={proj.major_version + 1}.0.0"]
        for key, proj in ogd_projects.items()
        if key != "main"
    },
    include_package_data=True,
    entry_points={
        "console_scripts": ogd_project.spec.get("console_scripts", []),
    },
    # Python version should be aligned to the latest databricks LTS runtime at the moment.
    # For more info: https://docs.databricks.com/aws/en/release-notes/runtime/ 
    # Reference: Databricks Runtime 16.4 LTS Using Python 3.12.3
    python_requires=">=3.12",
)
