# Gongxu-Lens · SupplyLens (供需透镜) v0

**Author and maintainer: [Aisiweiyang](https://github.com/Aisiweiyang)**

An open-source project exploring recycled-material matching, procurement plans, and scenario-based net emission accounting.

**v0 is under active maintenance. The latest code update, dated 2026-10-30, improves input reliability.**
Further updates will be irregular as features, documentation, and usability improve.
Feedback, suggestions, and contributions are welcome.

[简体中文](README.md) | English

![SupplyLens demo](docs/e2e-shots/site-1440.png)

## Latest update · 2026-10-30

- **Explicit demand selection**: use `--demand-id` when the file contains multiple demands; unknown IDs fail immediately.
- **Stop on invalid local inputs**: incomplete files or structural errors require correction, avoiding accidental use of fictional demo data.
- **Shared CSV validation**: the CLI and workbench share structure checks, support UTF-8 BOM, and reject duplicate or empty headers, missing columns, inconsistent row widths, and malformed quotes.
- **Complete supply template**: transport distance, freight inclusion, yield, and evidence fields are available for verified inputs.

This update focuses on input and import reliability. Algorithms, accounting conventions, and frozen numerical results for valid inputs remain unchanged. See the [changelog](CHANGELOG.md).

## About

SupplyLens explores whether available recycled-material batches can meet procurement requirements, and how to combine them while understanding costs, transport, missing evidence, and environmental trade-offs.

The current demo uses recycled PP pellets to replace virgin PP in non-food-contact industrial packaging and reusable containers. Demand, supply, and factor inputs produce screening results, alternative plans, reports, and decision passports.

The project uses Python 3.12+, PyYAML, and OR-Tools, with local offline computation and a SQLite-backed pilot workbench.

## Features

- Supply screening: comparable / pending evidence / rejected; missing evidence never silently passes.
- Procurement plans: compare cost, net emission avoidance, and supply concentration, with disruption checks.
- Scenario accounting: inspect calculation inputs, factor ranges, and deterministic sensitivity checks.
- Multi-demand matching: generate suggestions and export matching sheets.
- Pilot workbench: manage demand, supply, evidence, reservations, and delivery feedback, with roles, auditing, and backup/restore.
- Outputs: reports, an offline dashboard, and JSON decision passports.

## Quick start

Install Python 3.12+, download or clone the repository, and open a terminal in the project directory.

```bash
git clone https://github.com/Aisiweiyang/Gongxu-Lens.git
cd Gongxu-Lens
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py --industry 再生PP --data-mode demo
.\.venv\Scripts\python.exe serve.py --port 8765
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --industry 再生PP --data-mode demo
.venv/bin/python serve.py --port 8765
```

Open `http://127.0.0.1:8765/` in your browser.
For the pilot workbench, replace `serve.py` in the last command with `pilot/start_pilot.py`. The first visit initializes the administrator account; there is no default password. Run the demo and workbench separately.

## Data and verification

Built-in demo data is fictional. To use your own data:

1. Create `data/input/` and copy `material_supply.csv` and `material_demand.csv` from [templates/](templates/), keeping their filenames and headers.
2. Replace the example rows with verified supply, demand, and evidence records. Fill fields such as `distance_km`, `price_includes_freight`, and `yield_pct` from actual inputs.
3. Run with `--data-mode local`. For multiple demand records, select one with `--demand-id`; replace `YOUR_DEMAND_ID` below with an actual ID from your file.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe run.py --industry 再生PP --data-mode local --demand-id YOUR_DEMAND_ID
```

Linux/macOS:

```bash
.venv/bin/python run.py --industry 再生PP --data-mode local --demand-id YOUR_DEMAND_ID
```

| Data mode | Behavior |
|---|---|
| `demo` | Uses built-in fictional data for demonstrations. |
| `local` | Reads both local CSV files; missing files, structural errors, or an unknown demand ID stop the run. |
| `auto` (default) | Prefers local CSV; uses demo data only when both files are absent and no demand ID is specified. |

Use UTF-8 CSV (BOM supported), non-empty unique column names, and the same number of cells as header columns; quote cells containing commas. Workbench previews and committed imports share these checks. Batches with structural errors are not written to the database.
Missing prices, distances, or factors are flagged rather than replaced with zero. Each CLI run analyzes one demand; shared-pool matching across multiple demands is available through the workbench.

Using the virtual environment's Python, install `requirements-test.txt` and run `scripts/check_project.py` for automated tests and independent verification.
The recorded verification for the 2026-10-30 code update reports **303 tests and 63 subtests passing with no skips** on Linux Python 3.14, plus independent exhaustive checks for one demo case and six randomized cases. The newly added cases were also verified on Windows Python 3.12; see the [changelog](CHANGELOG.md).
See [CONTRIBUTING.md](CONTRIBUTING.md) for reproduction steps and platform limits, and the [initial acceptance report](docs/开源准备验收-20261008.md) for historical results.

## Documentation and maintenance

See the [documentation index](docs/INDEX.md) for methods and deployment notes, and the [changelog](CHANGELOG.md) for updates.
**v0 is the first public version.** References to `v10`–`v27.1` are internal iteration numbers from before open sourcing; algorithm and schema versions are separate.
Updates and maintenance will be irregular, with no fixed schedule. Repository records describe actual changes. Documentation is primarily in Chinese.

## Scope

This version is for exploration, demos, and pilot validation. Demo data and assumed factors must not be used for real procurement decisions. Emission figures are scenario estimates, not measured reductions or carbon offsets.
Real use requires verified inputs, test reports, factors, and commercial terms. Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Acknowledgements

Thank you to **秦仲远 (Qin Zhongyuan)** and **杨笑墨 (Yang Xiaomo)** for their assistance with the project.

## License

The project uses the [MIT license](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for third-party licenses.
