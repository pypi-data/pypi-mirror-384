# Polarion REST API Client

This project provides an **auto-generated Python client** for the Polarion REST API.  
It consumes the upstream OpenAPI JSON, applies a few deterministic fixes, validates the result, and generates importable Python code.

- **Generator:** [`openapi-python-client`](https://github.com/openapi-generators/openapi-python-client)  
- **Manager:** [`pdm`](https://pdm.fming.dev/latest/)  
- **Target package (generated):** `src/polarion_rest_client/openapi`
- **High-level wrappers:** will live under `src/polarion_rest_client/`

---

## 📂 Project Structure

```text
.
├── codegen/                              # OpenAPI specs + generation config
│   ├── polarion-openapi.json             # upstream Polarion REST spec (input)
│   ├── polarion-openapi-clean.json       # cleaned spec (derived; usually gitignored)
│   └── client-config.yaml                # openapi-python-client config (package_name, etc.)
├── scripts/                              # helper scripts
│   ├── clean_rest_spec.py                # applies Polarion-specific fixes to the spec
│   ├── rest_json_validator.py            # JSON/OpenAPI validation
│   ├── regenerate_polarion_rest_client.sh# end-to-end: clean → validate → generate → copy (no reformatting)
│   └── set_version.py                    # helper to set package version
├── src/
│   └── polarion_rest_client/             # (future) high-level helpers wrapping autogen package
│       └── openapi/                      # auto-generated client (committed)
├── tests/                                # tests for high-level code (and smoke for autogen)
├── pyproject.toml                        # PDM/PEP 621 metadata
└── README.md
```

---

## ✅ Requirements

- Python **3.9+**
- [PDM](https://pdm.fming.dev/latest/) installed (`pipx install pdm` recommended)

> We do **not** require global Node/npm. Generation is done via `openapi-python-client` (a Python package).

---

## ⚙️ Setup

```bash
# clone and enter the repo
git clone https://gitlab.com/elimesika-group/polarion-rest-client.git

# create & populate the PDM venv (runtime + dev deps)
pdm install --dev
```

---

## 🔧 Regeneration Workflow

> The script runs everything for you: **clean → validate → generate → copy**.

1) Place / update the upstream spec at:
```
codegen/polarion-openapi.json
```

2) Run the pipeline:
```bash
pdm run regenerate-client
```

What happens:
- `clean_rest_spec.py` applies deterministic fixes:
  - normalize `application/octet-stream` uploads to `string/binary`
  - expand vendor `4XX-5XX` responses into concrete 4xx/5xx entries
  - add missing `items` for certain array schemas in `jobsSingle*Response`
  - relax nullability for specific error-source fields
  - expand reference-only component schemas (e.g., `{"$ref": ...}`) into `allOf` so the generator can model them
- `rest_json_validator.py` validates JSON syntax and OpenAPI structure
- `openapi-python-client` generates the client into `.build/rest-client`
- The generated package is copied into `src/polarion_rest_client/openapi`

3) Quick import sanity check:
```bash
python - <<'PY'
import sys; sys.path.insert(0, "autogen")
import polarion_rest_client.openapi as pkg
print("import ok:", pkg.__name__)
PY
```

---

## 📦 Using the Generated Client

### Client session creation and document retrieval


#### Environment variables

export POLARION_URL="" # Link to Polarion server REST API endpoint
export POLARION_PROJECT="..." # Project name
export POLARION_USER="..." # Polarion user name
export POLARION_PASSWORD=""
export POLARION_TOKEN="..." # Polarion token
export POLARION_VERIFY_SSL={true or false}


##### Variables used in tests to prevent improper usage of production environments

export POLARION_TEST_URL="" # Link to Polarion staging or test server REST API endpoint
export POLARION_TEST_PROJECT="..." # Project name for testing
export POLARION_TEST_DOC_CREATE_OK={0|1} # Enable/Disable document creation
export POLARION_TEST_DOCUMENT_NAME= # Test document name
export POLARION_TEST_DOC_TABLE_EXPECTED_COLS= # A comma separated list of table column names to match in test doc.


	import polarion_rest_client as prc
	from prc.openapi.api.documents.get_document import sync as get_document

	pc = prc.PolarionClient(**prc.get_env_vars())

	doc = get_document(
	    client=pc.gen,
	    project_id="my-project",
	    space_id="my-space",
	    document_name="my-document-name",
	)


> Endpoint modules and function names are generated from the spec; refer to `polarion_rest_client/openapi/api/` for the available calls.

---

## 🔖 Versioning

- **Package version format:** `XX.YY.ZZ` where:
  - `XX.YY` = Polarion server version (e.g., `25.06`)
  - `ZZ`     = client patch (e.g., `01`, `02`, …)
- **PEP 440 note:** PyPI displays `25.06.01` as `25.6.1`. Tag your releases with the original `v25.06.01` for clarity; the build will normalize for PyPI automatically.

Use the helper to set the version in `pyproject.toml`:
```bash
pdm run python scripts/set_version.py 25.06.01
```

---

## 🧪 Tests

```bash
pdm run pytest
```

---

## 🧩 Custom Templates (optional)

You can override `openapi-python-client` Jinja templates to tweak emitted code (naming, default headers, timeouts, docstrings, etc.).

- Place overrides under:
```
codegen/custom_templates/
```
- Use the **same relative paths** as the upstream templates.
- The regeneration script automatically passes `--custom-template-path` when the folder exists.

To discover the upstream templates path:
```bash
python - <<'PY'
import importlib.resources as r, openapi_python_client as opc
print((r.files(opc) / "templates").as_posix())
PY
```

Copy only the files you want to override; the rest fall back to defaults.

---


> Keep `src/polarion_rest_client/openapi/**` **committed** so consumers get the client without needing the generator.

---

## 🤝 Contributing

We welcome contributions!

1) Create a feature branch:
```bash
git checkout -b feature/my-feature
```

2) Run the full pipeline before committing:
```bash
pdm run pre_build
```

3) Run tests:
```bash
pdm run pytest
```

4) Commit only **necessary** changes (avoid manual edits to generated files).  
5) Open a Merge Request / Pull Request with:
   - a clear description
   - references to issues
   - test evidence when applicable

**Code style:** Python idiomatic; scripts should be modular with clear docstrings.  
```bash
flake8 . --exclude ./venv  --max-line-length=120
```
**Commits:** try to follow [Conventional Commits](https://www.conventionalcommits.org/).

## 🚢 Releases & Publishing

This package uses a versioning scheme **XX.YY.ZZ**, where **XX.YY** matches the Polarion server line (e.g., `25.06`) and **ZZ** is a  client patch (e.g., `01`). PyPI will display the **PEP 440–normalized** form (e.g., `25.06.01` → `25.6.1`). Keep Git tags human-friendly (`v25.06.01`) and the package metadata normalized.

---

### Quick Release Checklist

1. Update `CHANGELOG.md`.
2. Regenerate client:
       `pdm run regenerate-client`
3. Prepare packaging (copy autogen → src):
       `pdm run pre_build`
4. Build:
       `pdm build`
5. Tag:
       `git tag -a vXX.YY.ZZ-rcx -m "Polarion XX.YY, patch ZZ RC x"`
6. Push branch + tag:
       `git push -u origin <branch> && git push origin vXX.YY.ZZ-rcx`
7. TestPyPI (dry run):
       `pdm publish -r testpypi --username __token__ --password "$TESTPYPI_TOKEN"`
       then install & test from TestPyPI (see below).
8. `git tag -a vXX.YY.ZZ -m "Polarion XX.YY, patch ZZ"`
9. PyPI (real release):
       `pdm publish --username __token__ --password "$PYPI_TOKEN"`
       then install & test from PyPI (see below).
10. Push branch + tag:
       `git push -u origin <branch> && git push origin vXX.YY.ZZ`

> If TestPyPI/PyPI rejects the upload as a **duplicate file**, bump the patch version (e.g., `25.06.02`) using `pdm run python scripts/set_version.py 25.06.02`, rebuild, and retry.

---

### 1) Accounts & API Tokens (one-time setup)

**TestPyPI** (safe sandbox):
- Create an account: <https://test.pypi.org/account/register/>
- (Recommended) Enable 2FA in *Account settings → Two-factor Authentication*.
- Create an **API token** with **Entire account** scope (required for the first upload).
- Export the token in your shell:

        export TESTPYPI_TOKEN='pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'


**PyPI** (the real index):
- Create an account: <https://pypi.org/account/register/>
- (Recommended) Enable 2FA.
- Check if your distribution name is available: <https://pypi.org/project/polarion-rest-client/>
  - If taken, change `[project].name` in `pyproject.toml` to a unique name (only the **distribution** name changes; import packages stay the same).
- Create a **PyPI API token** (use **Entire account** for the very first upload), then export:

        export PYPI_TOKEN='pypi-YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

---

### 2) Build Fresh Artifacts

- Regenerate from the OpenAPI spec (clean → validate → generate):

        pdm run regenerate-client

- Copy generated client into `src/` for packaging:

        pdm run pre_build

- Build sdist + wheel:

        pdm build
        ls -l dist/

Sanity: you should see a wheel like `dist/polarion_rest_client-25.6.1-py3-none-any.whl`.

---

### 3) Dry-Run Publish to TestPyPI

- Upload:

        pdm publish -r testpypi --username __token__ --password "$TESTPYPI_TOKEN"

- Verify by installing from TestPyPI in a clean venv (falls back to PyPI for dependencies):

        python -m venv /tmp/poltest && source /tmp/poltest/bin/activate
        pip install --upgrade pip
        pip install -i https://test.pypi.org/simple/ polarion-rest-client==25.6.1-rc1 --extra-index-url https://pypi.org/simple
        python - <<'PY'
        import polarion_rest_client as hl, polarion_rest_client.openapi as gen
        print("TestPyPI imports OK:", gen.__name__, hl.__name__)
        PY
        deactivate

**Common errors**
- “File already exists” / 400 → bump patch version with `scripts/set_version.py`, rebuild, re-publish.
- 403 “user `__token__` isn’t allowed to upload” → first upload requires an **Entire account** token.
- Name conflict → change the distribution name in `pyproject.toml`, rebuild, retry.

---

### 4) Publish to PyPI

- Upload:

        pdm publish --username __token__ --password "$PYPI_TOKEN"

- Verify from PyPI:

        python -m venv /tmp/polprod && source /tmp/polprod/bin/activate
        pip install --upgrade pip
        pip install polarion-rest-client==25.6.1
        python - <<'PY'
        import polarion_rest_client as hl, polarion_rest_client.openapi as gen
        print("PyPI imports OK:", gen.__name__, hl.__name__)
        PY
        deactivate

**After your first PyPI release**
- Create a **project-scoped** token (scoped to your distribution name) and replace the wide token.
- Revoke the original “Entire account” token for least privilege.

---

### 5) Tag & Push

- Commit, tag, and push:

        git commit -m "chore(release): set version XX.YY.ZZ"
        git tag -a vXX.YY.ZZ -m "Polarion XX.YY, patch ZZ"
        git push -u origin <your-branch>
        git push origin vXX.YY.ZZ

> The above steps 1-5 are automated via the project pipeline when you push a tag

---

### Notes

- Package metadata uses PEP 440 normalized versions (e.g., `25.6.1`). Keep Git tags and CHANGELOG using `XX.YY.ZZ`.
- Never commit tokens; pass them via environment variables (`TESTPYPI_TOKEN`, `PYPI_TOKEN`).
- If you see packaging issues, rebuild clean:

        rm -rf dist && pdm run pre_build && pdm build


---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.

