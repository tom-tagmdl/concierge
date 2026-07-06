from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

PANEL_FILE = ROOT / "custom_components" / "concierge" / "frontend" / "panel.js"
TESTS_FILE = ROOT / "tests" / "test_services.py"
GUARDRAILS_DOC = ROOT / "docs" / "development" / "architecture-guardrails.md"
EXCEPTIONS_DOC = ROOT / "docs" / "development" / "architecture-exceptions.md"


def _failures() -> list[str]:
    failures: list[str] = []

    if not PANEL_FILE.exists():
        failures.append(f"Missing panel file: {PANEL_FILE}")
    else:
        panel_text = PANEL_FILE.read_text(encoding="utf-8")
        if 'class="cg-modal-backdrop"' in panel_text:
            failures.append(
                "Custom dialog wrapper detected in panel.js (cg-modal-backdrop). Use ha-dialog for modal flows."
            )
        if 'callService("tts", "get_voices"' in panel_text or "callService('tts', 'get_voices'" in panel_text:
            failures.append(
                "Frontend TTS provider discovery detected in panel.js. Use backend-projected provider metadata instead of direct tts.get_voices calls."
            )

    if not TESTS_FILE.exists():
        failures.append(f"Missing tests file: {TESTS_FILE}")
    else:
        tests_text = TESTS_FILE.read_text(encoding="utf-8")
        required_tests = [
            "test_voice_enrollment_lifecycle_services_round_trip",
        ]
        for test_name in required_tests:
            if test_name not in tests_text:
                failures.append(f"Required architecture regression test missing: {test_name}")

    if not GUARDRAILS_DOC.exists():
        failures.append(f"Missing architecture guardrails doc: {GUARDRAILS_DOC}")

    if not EXCEPTIONS_DOC.exists():
        failures.append(f"Missing architecture exceptions register: {EXCEPTIONS_DOC}")

    return failures


def main() -> int:
    failures = _failures()
    if not failures:
        print("Architecture guardrails validated.")
        return 0

    print("Architecture guardrail validation failed:")
    for item in failures:
        print(f"- {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
