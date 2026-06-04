from dataclasses import dataclass, field


@dataclass
class ScanResult:
    project_name: str
    project_path: str
    files: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class AuditResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixed_fields: list[str] = field(default_factory=list)


@dataclass
class ProjectInventory:
    project_name: str
    project_path: str
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    dependencies: dict[str, object] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    scripts: list[dict[str, object]] = field(default_factory=list)
    documentation: dict[str, object] = field(default_factory=dict)
    audit: dict[str, object] = field(default_factory=dict)
