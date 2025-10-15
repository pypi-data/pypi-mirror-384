from ambient_package_update.metadata.author import PackageAuthor
from ambient_package_update.metadata.constants import (
    DEV_DEPENDENCIES,
    LICENSE_MIT,
    SUPPORTED_DJANGO_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)
from ambient_package_update.metadata.executables import ScriptExecutable
from ambient_package_update.metadata.maintainer import PackageMaintainer
from ambient_package_update.metadata.package import PackageMetadata
from ambient_package_update.metadata.readme import ReadmeContent
from ambient_package_update.metadata.ruff_ignored_inspection import RuffIgnoredInspection

METADATA = PackageMetadata(
    package_name="boa-restrictor",
    github_package_group="ambient-innovation",
    authors=[
        PackageAuthor(
            name="Ambient Digital",
            email="hello@ambient.digital",
        ),
    ],
    maintainer=PackageMaintainer(name="Ambient Digital", url="https://ambient.digital/", email="hello@ambient.digital"),
    licenser="Ambient Innovation: GmbH",
    license=LICENSE_MIT,
    license_year=2024,
    development_status="4 - Beta",
    has_migrations=False,
    claim="A custom Python and Django linter from Ambient",
    readme_content=ReadmeContent(uses_internationalisation=False),
    main_branch="main",
    tests_require_django=False,
    dependencies=[f"Django>={SUPPORTED_DJANGO_VERSIONS[0]}", 'tomli; python_version < "3.11"'],
    supported_django_versions=SUPPORTED_DJANGO_VERSIONS,
    supported_python_versions=SUPPORTED_PYTHON_VERSIONS,
    optional_dependencies={
        "dev": [
            *DEV_DEPENDENCIES,
        ],
    },
    ruff_ignore_list=[
        RuffIgnoredInspection(key="TD002", comment="Missing issue link on the line following this TODO"),
        RuffIgnoredInspection(key="TD003", comment="Missing issue link on the line following this TODO"),
        RuffIgnoredInspection(key="PERF401", comment="Use `list.extend` to create a transformed list"),
    ],
    script_executables=[ScriptExecutable(name="boa-restrictor", import_path="boa_restrictor.cli.main:main")],
)
