# Model directory build regression — 2026-11-26
Signature: RuntimeError: MODEL_DIRECTORY card count mismatch in scripts/enrich_model_directory.py.
The raw attribute-name regex also matched the CSS selector, counting 136 entries for 135 models.
Count only article/li start tags bearing the entry attribute; keep the 135-entry and photo-card invariants.
A second CI failure came from models-100.html declaring its legacy URL canonical while the committed sitemap excluded it. Align the source alias canonical with models-135.html, as already intended by the generated alias.
Regression: tests/test_model_directory_regression.py renders all 135 fixture pages with mixed photo/text entries and the original CSS selector; checks the legacy canonical. Dedicated model-directory-regression.yml runs on every push and PR. Existing predeploy gate still checks content/sitemap reproducibility and public-file security.
Do not retry the same failed SHA or bypass either invariant.
