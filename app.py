import json
from datetime import date
from dateutil.parser import parse as parse_date
from flask import Flask, render_template, request, redirect, url_for, flash

import db

app = Flask(__name__)
app.secret_key = "excelra-repo-scout-dev"

BU_OPTIONS = [
    "Chemistry Services",
    "ClinPharma Services",
    "Bioinformatics Services",
    "Scientific Products",
    "Cross-BU",
]

ASSET_TYPES = ["Dataset", "Model", "Pipeline", "Library", "App/UI", "Benchmark", "Ontology", "Paper/Reference"]
LICENSE_FLAGS = ["Green", "Yellow", "Red"]

DEFAULT_USE_CASES = [
    "ADMET / Property prediction",
    "Bioactivity curation",
    "Target identification",
    "Target-disease evidence",
    "Virtual screening / Docking",
    "Retrosynthesis / Reaction prediction",
    "Biomedical NLP / NER",
    "RAG / Search",
    "Knowledge graph",
    "Benchmarking",
    "Data standardization",
    "Clinical trials / RWD",
    "PK/PD",
]


def seed_if_empty():
    db.init_db()
    if db.count_assets() > 0:
        return
    with open("seed_assets.json", "r", encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
        it.setdefault("secondary_bus", [])
        it.setdefault("use_cases", [])
        it.setdefault("license_notes", "")
        it.setdefault("owner", "")
        it.setdefault("notes", "")
        it.setdefault("excelra_leverage", "")
        it.setdefault("last_validated_on", date.today().isoformat())
        it.setdefault("readiness_score", 3)
        it.setdefault("engineering_score", 3)
        it.setdefault("maintenance_score", 3)
        db.insert_asset(it)


def contains(haystack: str, needle: str) -> bool:
    return needle.lower() in (haystack or "").lower()


def normalize_date_str(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    try:
        dt = parse_date(s, dayfirst=False, yearfirst=True)
        return dt.date().isoformat()
    except Exception:
        return s


def validate_payload(p):
    if not p["name"] or not p["url"] or not p["short_summary"]:
        return "Name, URL, and Short summary are required."
    if p["primary_bu"] not in BU_OPTIONS:
        return "Primary BU is invalid."
    if p["asset_type"] not in ASSET_TYPES:
        return "Asset type is invalid."
    if p["license_flag"] not in LICENSE_FLAGS:
        return "License flag is invalid."
    for k in ["readiness_score", "engineering_score", "maintenance_score"]:
        try:
            s = int(p[k])
        except Exception:
            return f"{k} must be a number between 0 and 5."
        if s < 0 or s > 5:
            return f"{k} must be between 0 and 5."
    return None


@app.route("/")
def index():
    seed_if_empty()
    assets = db.list_assets()

    q = request.args.get("q", "").strip()
    primary_bu = request.args.get("primary_bu", "").strip()
    asset_type = request.args.get("asset_type", "").strip()
    license_flag = request.args.get("license_flag", "").strip()
    use_case = request.args.get("use_case", "").strip()
    min_ready = int(request.args.get("min_ready", "0") or 0)

    items = assets[:]

    if q:
        def match(r):
            blob = " ".join(
                [
                    r.get("name", ""),
                    r.get("short_summary", ""),
                    r.get("url", ""),
                    r.get("primary_bu", ""),
                    " ".join(r.get("secondary_bus", []) or []),
                    " ".join(r.get("use_cases", []) or []),
                    r.get("excelra_leverage", ""),
                    r.get("notes", ""),
                ]
            )
            return contains(blob, q)
        items = [r for r in items if match(r)]

    if primary_bu:
        items = [r for r in items if r.get("primary_bu") == primary_bu]

    if asset_type:
        items = [r for r in items if r.get("asset_type") == asset_type]

    if license_flag:
        items = [r for r in items if r.get("license_flag") == license_flag]

    items = [r for r in items if int(r.get("readiness_score", 0)) >= min_ready]

    if use_case:
        def has_uc(r):
            for u in (r.get("use_cases", []) or []):
                if contains(u, use_case):
                    return True
            return False
        items = [r for r in items if has_uc(r)]

    items.sort(
        key=lambda r: (
            int(r.get("readiness_score", 0)),
            int(r.get("engineering_score", 0)),
            int(r.get("maintenance_score", 0)),
        ),
        reverse=True,
    )

    return render_template(
        "index.html",
        items=items,
        BU_OPTIONS=BU_OPTIONS,
        ASSET_TYPES=ASSET_TYPES,
        LICENSE_FLAGS=LICENSE_FLAGS,
        DEFAULT_USE_CASES=DEFAULT_USE_CASES,
        filters=dict(
            q=q,
            primary_bu=primary_bu,
            asset_type=asset_type,
            license_flag=license_flag,
            use_case=use_case,
            min_ready=min_ready,
        ),
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    seed_if_empty()

    if request.method == "POST":
        payload = {
            "name": request.form.get("name", "").strip(),
            "url": request.form.get("url", "").strip(),
            "short_summary": request.form.get("short_summary", "").strip(),
            "primary_bu": request.form.get("primary_bu", "").strip(),
            "secondary_bus": request.form.getlist("secondary_bus"),
            "use_cases": request.form.getlist("use_cases"),
            "asset_type": request.form.get("asset_type", "").strip(),
            "license_flag": request.form.get("license_flag", "").strip(),
            "license_notes": request.form.get("license_notes", "").strip(),
            "readiness_score": int(request.form.get("readiness_score", "3") or 3),
            "engineering_score": int(request.form.get("engineering_score", "3") or 3),
            "maintenance_score": int(request.form.get("maintenance_score", "3") or 3),
            "last_validated_on": normalize_date_str(request.form.get("last_validated_on", "").strip()) or date.today().isoformat(),
            "owner": request.form.get("owner", "").strip(),
            "excelra_leverage": request.form.get("excelra_leverage", "").strip(),
            "notes": request.form.get("notes", "").strip(),
        }

        err = validate_payload(payload)
        if err:
            flash(err, "error")
            return redirect(url_for("add"))

        new_id = db.insert_asset(payload)
        flash(f"Saved asset (ID: {new_id})", "success")
        return redirect(url_for("index"))

    return render_template(
        "add.html",
        BU_OPTIONS=BU_OPTIONS,
        ASSET_TYPES=ASSET_TYPES,
        LICENSE_FLAGS=LICENSE_FLAGS,
        DEFAULT_USE_CASES=DEFAULT_USE_CASES,
        today=date.today().isoformat(),
    )


@app.route("/edit/<int:asset_id>", methods=["GET", "POST"])
def edit(asset_id: int):
    seed_if_empty()
    a = db.get_asset(asset_id)
    if not a:
        flash("Asset not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        payload = {
            "name": request.form.get("name", "").strip(),
            "url": request.form.get("url", "").strip(),
            "short_summary": request.form.get("short_summary", "").strip(),
            "primary_bu": request.form.get("primary_bu", "").strip(),
            "secondary_bus": request.form.getlist("secondary_bus"),
            "use_cases": request.form.getlist("use_cases"),
            "asset_type": request.form.get("asset_type", "").strip(),
            "license_flag": request.form.get("license_flag", "").strip(),
            "license_notes": request.form.get("license_notes", "").strip(),
            "readiness_score": int(request.form.get("readiness_score", "3") or 3),
            "engineering_score": int(request.form.get("engineering_score", "3") or 3),
            "maintenance_score": int(request.form.get("maintenance_score", "3") or 3),
            "last_validated_on": normalize_date_str(request.form.get("last_validated_on", "").strip()),
            "owner": request.form.get("owner", "").strip(),
            "excelra_leverage": request.form.get("excelra_leverage", "").strip(),
            "notes": request.form.get("notes", "").strip(),
        }

        err = validate_payload(payload)
        if err:
            flash(err, "error")
            return redirect(url_for("edit", asset_id=asset_id))

        db.update_asset(asset_id, payload)
        flash("Updated.", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        a=a,
        BU_OPTIONS=BU_OPTIONS,
        ASSET_TYPES=ASSET_TYPES,
        LICENSE_FLAGS=LICENSE_FLAGS,
        DEFAULT_USE_CASES=DEFAULT_USE_CASES,
    )


@app.route("/delete/<int:asset_id>", methods=["POST"])
def delete(asset_id: int):
    seed_if_empty()
    db.delete_asset(asset_id)
    flash("Deleted.", "success")
    return redirect(url_for("index"))


import os

if __name__ == "__main__":
    seed_if_empty()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)


