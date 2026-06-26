"""File-based capability loader: SKILL.md directories and plugin YAML descriptors."""

from __future__ import annotations

import os

import yaml

from regnexe.plugin.descriptor import CapabilityDescriptor
from regnexe.plugin.enums import CapabilityType


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter enclosed in --- delimiters from markdown."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        fm = {}
    body = content[end + 4:].strip()
    return fm, body


class FileCapabilityLoader:
    """Walks a directory tree and returns CapabilityDescriptors.

    Recognised files:
    - ``SKILL.md``   → CapabilityType.SKILL (reads frontmatter for metadata)
    - ``plugin.yaml`` / ``plugin.yml`` → CapabilityType.MCP_TOOL batch descriptors
    """

    def load_directory(self, directory: str) -> list[CapabilityDescriptor]:
        descriptors: list[CapabilityDescriptor] = []
        for root, _, files in os.walk(directory):
            for fname in sorted(files):
                path = os.path.join(root, fname)
                if fname == "SKILL.md":
                    desc = self._load_skill_md(path)
                    if desc:
                        descriptors.append(desc)
                elif fname in ("plugin.yaml", "plugin.yml"):
                    descriptors.extend(self._load_plugin_yaml(path))
        return descriptors

    def _load_skill_md(self, path: str) -> CapabilityDescriptor | None:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        fm, body = _parse_frontmatter(content)
        if not fm.get("name"):
            return None
        skill_dir = os.path.dirname(path)
        plugin_id = fm.get("plugin_id", os.path.basename(skill_dir))
        capability_id = fm.get("capability_id", f"{plugin_id}.skill")
        allowed_tools = fm.get("allowed_tools") or []
        return CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=plugin_id,
            type=CapabilityType.SKILL,
            name=fm["name"],
            description=fm.get("description", ""),
            tags=fm.get("tags", []),
            skill_path=skill_dir,
            system_prompt=body or None,
            model_kwargs={"allowed_tools": allowed_tools} if allowed_tools else None,
        )

    def _load_plugin_yaml(self, path: str) -> list[CapabilityDescriptor]:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "capabilities" not in data:
            return []
        plugin_id = data.get("plugin_id", "unknown")
        result: list[CapabilityDescriptor] = []
        for cap in data.get("capabilities", []):
            try:
                cap_type = CapabilityType(cap.get("type", "mcp_tool"))
            except ValueError:
                continue
            name = cap.get("name", "")
            result.append(CapabilityDescriptor(
                capability_id=cap.get("capability_id", f"{plugin_id}.{name}"),
                plugin_id=plugin_id,
                type=cap_type,
                name=name,
                description=cap.get("description", ""),
                tags=cap.get("tags", []),
            ))
        return result
