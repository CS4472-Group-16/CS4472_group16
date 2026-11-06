"""Summarize real Surefire and JaCoCo XML; missing results are infrastructure errors."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
reports = sorted((ROOT / "target/surefire-reports").glob("TEST-*.xml"))
if not reports:
    raise SystemExit("No Surefire XML: tests were not executed.")
tests = failures = errors = skipped = 0
for path in reports:
    suite = ET.parse(path).getroot()
    tests += int(suite.get("tests", 0))
    failures += int(suite.get("failures", 0))
    errors += int(suite.get("errors", 0))
    skipped += int(suite.get("skipped", 0))
if tests == 0:
    raise SystemExit("Zero tests executed.")
lines = ["<!-- assignment1-coverage -->", "### Test execution and JaCoCo coverage", "",
         f"Executed: **{tests}**; failures: **{failures}**; errors: **{errors}**; skipped: **{skipped}**.",
         "", "Coverage is informational; it is not a grading threshold.", "",
         "| Metric | Covered | Total | Coverage |", "|---|---:|---:|---:|"]
coverage = ROOT / "target/site/jacoco/jacoco.xml"
if coverage.exists():
    for counter in ET.parse(coverage).getroot().findall("counter"):
        covered = int(counter.get("covered"))
        total = covered + int(counter.get("missed"))
        percent = f"{100 * covered / total:.2f}%" if total else "N/A"
        lines.append(f"| {counter.get('type')} | {covered} | {total} | {percent} |")
else:
    lines.append("| Report unavailable | — | — | — |")
lines += ["", "Download the `test-results-and-coverage` workflow artifact for the XML and HTML reports.", ""]
(ROOT / "target/ci-report.md").write_text("\n".join(lines))
print(f"Executed {tests} tests: {failures} failures, {errors} errors, {skipped} skipped.")
