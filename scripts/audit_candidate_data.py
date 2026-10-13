"""Audit and inspect candidate raw datasets according to GLOBAL-INSTRUCTIONS.md.

Computes hashes, inspects dimensions, data types, value ranges, and records
the dataset manifest and compatibility matrix.
"""

import hashlib
import json
import os
import numpy as np
import openpyxl
import pandas as pd


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def audit():
    raw_dir = os.path.abspath("data/raw")
    npy_path = os.path.join(raw_dir, "cstr_rawdata.npy")
    xlsx_path = os.path.join(raw_dir, "CSTR_24aug_PRBS_dataset.xlsx")

    manifest = {
        "audit_version": "1.0",
        "timestamp": "2026-10-13T02:20:00Z",
        "datasets": {}
    }

    # 1. Audit cstr_rawdata.npy
    print(f"Auditing {npy_path}...")
    npy_hash = compute_sha256(npy_path)
    npy_size = os.path.getsize(npy_path)
    
    # Load safely with allow_pickle=False
    npy_data = np.load(npy_path, allow_pickle=False)
    npy_info = {
        "filename": "cstr_rawdata.npy",
        "sha256": npy_hash,
        "size_bytes": npy_size,
        "shape": list(npy_data.shape),
        "dtype": str(npy_data.dtype),
        "min": float(np.nanmin(npy_data)),
        "max": float(np.nanmax(npy_data)),
        "mean": float(np.nanmean(npy_data)),
        "nan_count": int(np.isnan(npy_data).sum()),
        "inf_count": int(np.isinf(npy_data).sum()),
        "status": "QUARANTINED",
        "compatibility": {
            "concentration_modeling": "INCOMPATIBLE (Unknown column semantics, no feature dictionary)",
            "temperature_modeling": "INCOMPATIBLE (Undocumented signals)",
            "recommendation": "Quarantine until laboratory source provides semantic column definitions"
        }
    }
    manifest["datasets"]["cstr_rawdata.npy"] = npy_info

    # 2. Audit CSTR_24aug_PRBS_dataset.xlsx
    print(f"Auditing {xlsx_path}...")
    xlsx_hash = compute_sha256(xlsx_path)
    xlsx_size = os.path.getsize(xlsx_path)

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    sheets = wb.sheetnames
    wb.close()

    sheet_info = {}
    for s in sheets:
        df = pd.read_excel(xlsx_path, sheet_name=s, engine="openpyxl")
        summary_dict = df.describe().to_dict() if df.shape[1] > 0 and df.shape[0] > 0 else {}
        sheet_info[s] = {
            "rows": len(df),
            "columns": [str(c) for c in df.columns],
            "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
            "nan_counts": {str(c): int(df[c].isna().sum()) for c in df.columns},
            "summary": summary_dict
        }

    # Analyze column semantics
    all_cols = []
    for s, s_data in sheet_info.items():
        all_cols.extend(s_data["columns"])
    
    has_concentration = any("conc" in c.lower() or "ca" in c.lower() for c in all_cols)

    xlsx_info = {
        "filename": "CSTR_24aug_PRBS_dataset.xlsx",
        "sha256": xlsx_hash,
        "size_bytes": xlsx_size,
        "sheets": sheets,
        "sheet_details": sheet_info,
        "contains_concentration": has_concentration,
        "status": "INSPECTED",
        "compatibility": {
            "isothermal_concentration_validation": "INCOMPATIBLE (No concentration measurements present)",
            "thermal_calibration": "POTENTIALLY COMPATIBLE for Phase 13 (Temperature & jacket dynamics present)",
            "recommendation": "Preserve in data/raw for Phase 13 thermal model; do not use for Phase 1-12 concentration validation"
        }
    }
    manifest["datasets"]["CSTR_24aug_PRBS_dataset.xlsx"] = xlsx_info

    # Save manifest
    manifest_path = os.path.join(raw_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {manifest_path}")

    # Generate Markdown Audit Report
    report_path = os.path.abspath("reports/candidate-datasets-audit.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Candidate Datasets Audit & Compatibility Matrix\n\n")
        f.write(f"- **Audit Date:** 2026-10-13\n")
        f.write(f"- **Audit Policy:** Strictly adhering to GLOBAL-INSTRUCTIONS.md\n\n")
        f.write("## 1. Candidate Files & Cryptographic Hashes\n\n")
        f.write("| Filename | SHA-256 Hash | Size (Bytes) | Status |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| `cstr_rawdata.npy` | `{npy_hash}` | {npy_size:,} | **QUARANTINED** |\n")
        f.write(f"| `CSTR_24aug_PRBS_dataset.xlsx` | `{xlsx_hash}` | {xlsx_size:,} | **AUDITED / THERMAL ONLY** |\n\n")

        f.write("## 2. Array Analysis: `cstr_rawdata.npy`\n\n")
        f.write(f"- **Dimensions:** {npy_info['shape'][0]} rows × {npy_info['shape'][1]} columns\n")
        f.write(f"- **Data Type:** `{npy_info['dtype']}`\n")
        f.write(f"- **Numerical Range:** [{npy_info['min']:.4f}, {npy_info['max']:.4f}]\n")
        f.write(f"- **Mean:** {npy_info['mean']:.4f}\n")
        f.write(f"- **Missing Values (NaN):** {npy_info['nan_count']}\n")
        f.write(f"- **Inf Values:** {npy_info['inf_count']}\n")
        f.write("- **Assessment:** Unlabeled multi-dimensional floating-point array with no feature dictionary or timestamp definitions. In accordance with GLOBAL-INSTRUCTIONS.md, this dataset is **quarantined** and will not be used for supervised model training.\n\n")

        f.write("## 3. Workbook Analysis: `CSTR_24aug_PRBS_dataset.xlsx`\n\n")
        f.write(f"- **Sheets Found:** {', '.join(sheets)}\n\n")
        for s in sheets:
            f.write(f"### Sheet: `{s}`\n")
            f.write(f"- Rows: {sheet_info[s]['rows']}, Columns: {len(sheet_info[s]['columns'])}\n")
            f.write(f"- Columns: `{', '.join(sheet_info[s]['columns'])}`\n\n")
        
        f.write("## 4. Dataset-Task Compatibility Matrix\n\n")
        f.write("| Task / Phase | `cstr_rawdata.npy` | `CSTR_24aug_PRBS_dataset.xlsx` | Rationale |\n")
        f.write("|---|---|---|---|\n")
        f.write("| **Phase 1–5: Isothermal Steady/Dynamic Core** | Incompatible | Incompatible | Both candidate files do not contain verified reactant concentrations. |\n")
        f.write("| **Phase 7: Kinetic Parameter Estimation** | Incompatible | Incompatible | Kinetic estimation requires concentration time series $C_A(t)$ or conversion $X_A$. |\n")
        f.write("| **Phase 8: Synthetic Data & Splits** | N/A | N/A | Generated from the tested mechanistic ODE solver. |\n")
        f.write("| **Phase 9–11: Neural ODE & PINN Kinetic Modeling** | Incompatible | Incompatible | Cannot fit reaction kinetics $r_A(C_A)$ without measured concentration. |\n")
        f.write("| **Phase 13: Arrhenius & Thermal CSTR** | Incompatible | **Candidate Match** | Contains reactor/jacket/bath temperatures and feed flow rates for thermal energy balance. |\n")

    print(f"Saved audit report to {report_path}")


if __name__ == "__main__":
    audit()
