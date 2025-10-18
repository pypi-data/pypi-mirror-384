"""Export formats for atlo run results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class ResultExporter:
    """Exports run results in various formats."""

    @staticmethod
    def export_json(manifest: Dict[str, Any], output_path: Path) -> None:
        """Export results as JSON.

        Args:
            manifest: Run manifest dict
            output_path: Path to save JSON file
        """
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)

    @staticmethod
    def export_junit(manifest: Dict[str, Any], output_path: Path) -> None:
        """Export results as JUnit XML.

        Args:
            manifest: Run manifest dict
            output_path: Path to save XML file
        """
        import xml.etree.ElementTree as ET

        # Create test suite
        total_tests = len(manifest["results"])
        failures = sum(1 for r in manifest["results"] if r["status"] == "failed")
        duration = manifest["total_duration"]

        testsuite = ET.Element(
            "testsuite",
            name="atlo-terraform-plan",
            tests=str(total_tests),
            failures=str(failures),
            time=str(duration),
            timestamp=manifest["timestamp"],
        )

        # Add test cases
        for result in manifest["results"]:
            testcase = ET.SubElement(
                testsuite,
                "testcase",
                name=result["project_name"],
                classname=result["project_dir"],
                time=str(result["duration"]),
            )

            # Add changes as properties
            properties = ET.SubElement(testcase, "properties")
            if result.get("adds") is not None:
                prop = ET.SubElement(properties, "property", name="adds")
                prop.text = str(result["adds"])
            if result.get("changes") is not None:
                prop = ET.SubElement(properties, "property", name="changes")
                prop.text = str(result["changes"])
            if result.get("destroys") is not None:
                prop = ET.SubElement(properties, "property", name="destroys")
                prop.text = str(result["destroys"])

            # Add failure info
            if result["status"] == "failed":
                failure = ET.SubElement(
                    testcase, "failure", message=result.get("error_message", "Plan failed")
                )
                failure.text = result.get("error_message", "Plan failed")

            # Add system-out with changes summary
            if result.get("changes_summary"):
                system_out = ET.SubElement(testcase, "system-out")
                system_out.text = result["changes_summary"]

        # Write to file
        tree = ET.ElementTree(testsuite)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def export_markdown(manifest: Dict[str, Any], output_path: Path) -> None:
        """Export results as Markdown.

        Args:
            manifest: Run manifest dict
            output_path: Path to save Markdown file
        """
        lines = []

        # Header
        lines.append("# Atlo Terraform Plan Results")
        lines.append("")
        timestamp = datetime.fromisoformat(manifest["timestamp"])
        lines.append(f"**Run Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Workflow:** {manifest['workflow']}")
        lines.append(f"**Duration:** {manifest['total_duration']:.1f}s")
        lines.append("")

        # Summary
        success_count = sum(1 for r in manifest["results"] if r["status"] == "success")
        failed_count = sum(1 for r in manifest["results"] if r["status"] == "failed")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- ✅ **Successful:** {success_count}")
        lines.append(f"- ❌ **Failed:** {failed_count}")
        lines.append("")

        # Total changes
        total_adds = sum(r.get("adds", 0) or 0 for r in manifest["results"])
        total_changes = sum(r.get("changes", 0) or 0 for r in manifest["results"])
        total_destroys = sum(r.get("destroys", 0) or 0 for r in manifest["results"])

        if total_adds or total_changes or total_destroys:
            lines.append("### Total Changes")
            lines.append("")
            if total_adds:
                lines.append(f"- 🟢 **To Add:** {total_adds}")
            if total_changes:
                lines.append(f"- 🟡 **To Change:** {total_changes}")
            if total_destroys:
                lines.append(f"- 🔴 **To Destroy:** {total_destroys}")
            lines.append("")

        # Results table
        lines.append("## Project Results")
        lines.append("")
        lines.append("| Project | Status | Duration | Changes |")
        lines.append("|---------|--------|----------|---------|")

        for result in manifest["results"]:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            status = f"{status_emoji} {result['status'].title()}"
            duration = f"{result['duration']:.1f}s"
            changes = result.get("changes_summary") or "-"

            lines.append(f"| {result['project_name']} | {status} | {duration} | {changes} |")

        lines.append("")

        # Failed projects detail
        failed_results = [r for r in manifest["results"] if r["status"] == "failed"]
        if failed_results:
            lines.append("## Failed Projects")
            lines.append("")
            for result in failed_results:
                lines.append(f"### {result['project_name']}")
                lines.append("")
                lines.append(f"**Directory:** `{result['project_dir']}`")
                lines.append(f"**Error:** {result.get('error_message', 'Unknown error')}")
                lines.append(f"**Log:** `{result['log_file']}`")
                lines.append("")

        # Write to file
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

    @staticmethod
    def export_github_actions(manifest: Dict[str, Any], output_path: Path) -> None:
        """Export results as GitHub Actions step summary format.

        Args:
            manifest: Run manifest dict
            output_path: Path to save summary file
        """
        lines = []

        # Header
        lines.append("# 🚀 Atlo Terraform Plan Results")
        lines.append("")

        # Summary
        success_count = sum(1 for r in manifest["results"] if r["status"] == "success")
        failed_count = sum(1 for r in manifest["results"] if r["status"] == "failed")
        timestamp = datetime.fromisoformat(manifest["timestamp"])

        lines.append("## 📊 Summary")
        lines.append("")
        lines.append(f"- **Workflow:** `{manifest['workflow']}`")
        lines.append(f"- **Duration:** {manifest['total_duration']:.1f}s")
        lines.append(f"- **Timestamp:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(f"**Results:** ✅ {success_count} successful, ❌ {failed_count} failed")
        lines.append("")

        # Total changes
        total_adds = sum(r.get("adds", 0) or 0 for r in manifest["results"])
        total_changes = sum(r.get("changes", 0) or 0 for r in manifest["results"])
        total_destroys = sum(r.get("destroys", 0) or 0 for r in manifest["results"])

        if total_adds or total_changes or total_destroys:
            lines.append("## 📝 Total Infrastructure Changes")
            lines.append("")
            lines.append("```")
            if total_adds:
                lines.append(f"+ {total_adds} resources to add")
            if total_changes:
                lines.append(f"~ {total_changes} resources to change")
            if total_destroys:
                lines.append(f"- {total_destroys} resources to destroy")
            lines.append("```")
            lines.append("")

        # Results table
        lines.append("## 📋 Project Details")
        lines.append("")
        lines.append("| Status | Project | Changes | Duration |")
        lines.append("|:------:|---------|---------|----------|")

        for result in manifest["results"]:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            changes = result.get("changes_summary") or "-"
            duration = f"{result['duration']:.1f}s"

            lines.append(
                f"| {status_emoji} | `{result['project_name']}` | {changes} | {duration} |"
            )

        lines.append("")

        # Failed projects
        failed_results = [r for r in manifest["results"] if r["status"] == "failed"]
        if failed_results:
            lines.append("## ❌ Failed Projects")
            lines.append("")
            for result in failed_results:
                lines.append(f"### {result['project_name']}")
                lines.append("")
                lines.append(f"**Directory:** `{result['project_dir']}`")
                lines.append("")
                lines.append("```")
                lines.append(result.get("error_message", "Unknown error"))
                lines.append("```")
                lines.append("")
                lines.append(f"📄 **Log file:** `{result['log_file']}`")
                lines.append("")

        # Write to file
        with open(output_path, "w") as f:
            f.write("\n".join(lines))
