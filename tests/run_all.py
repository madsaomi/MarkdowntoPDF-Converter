import os
import sys
import subprocess

"""Run all tests. Supports both custom runner and pytest.

Usage:
    python tests/run_all.py          # custom runner (verbose)
    python -m pytest tests/ -q       # pytest (compact)
"""

test_dir = os.path.dirname(os.path.abspath(__file__))
test_files = [
    "test_parser.py",
    "test_linter.py",
    "test_translations.py",
    "test_core.py",
    "test_ai_assistant.py",
    "test_wikilinks.py",
    "test_template_vars.py",
    "test_pptx_parser.py",
    "test_weasyprint_resolver.py",
    "test_watermark_css.py",
    "test_renderer_watermark_css.py",
    "test_renderers.py",
    "test_reveal_exporter.py",
    "test_multi_export.py",
    "test_plugin_system.py",
    "test_github_sync.py",
    "test_pdf_encrypt.py",
    "test_gui_stubs.py",
    "test_dependency_sync.py",
    "test_core_fixes_007.py",
    "test_stub_wiring_008.py",
    "test_release_config.py",
    "test_decomposition_010.py",
    "test_dialogs_package_011.py",
    "test_decomposition_012.py",
    "test_mixins_behavior_012.py",
    "test_mixins_behavior_012b.py",
    "test_mixins_behavior_012c.py",
    "test_no_dangling_globals.py",
    "test_workers_render_013.py",
    "test_translator.py",
    "test_gui_translator.py",
    "test_highlighter.py",
    "test_wikilinks_behavior.py",
    "test_file_manager.py",
    "test_editor_commands.py",
    "test_preview_manager.py",
    "test_templates_data.py",
    "test_dialogs_versions.py",
    "test_dialogs_common.py",
    "test_dialogs_analysis.py",
    "test_excalidraw_canvas.py",
    "test_dialogs_github_plugin.py",
    "test_calendar_view.py",
    "test_about_dialog.py",
]

passed = 0
failed = 0

for tf in test_files:
    path = os.path.join(test_dir, tf)
    print(f"\n{'='*60}")
    print(f"Running: {tf}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True, text=True, cwd=os.path.dirname(test_dir)
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode == 0:
        passed += 1
        print(f"  RESULT: PASS")
    else:
        failed += 1
        print(f"  RESULT: FAIL (exit code {result.returncode})")

print(f"\n{'='*60}")
print(f"SUMMARY: {passed} passed, {failed} failed, {len(test_files)} total")
print(f"   Also: python -m pytest tests/ -q")
print(f"{'='*60}")
sys.exit(0 if failed == 0 else 1)
