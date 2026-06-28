import json
from pathlib import Path

import pandas as pd
import streamlit as st

CONFIG_PATH = Path(__file__).with_name("rates_and_norms.json")

st.set_page_config(page_title="Censorafregning", page_icon="🧾", layout="wide")

DEFAULT_CONFIG = {
    "rates": {
        "Sats A – universiteter/højere læreanstalter": 508.91,
        "Sats B – øvrige videregående uddannelser": 421.07,
        "Sats C – gymnasium/tekniker mv.": 350.13,
        "Sats D": 304.92,
        "Sats E": 252.02,
        "Sats F": 208.55,
    },
    "vacation_pay_pct": 12.5,
    "km_rate_low": 2.23,
    "universities": ["SDU", "DTU", "AAU", "AU"],
    "exam_templates": {
        "Mundtlig – standard bachelor/kursus": {"minutes_per_student": 30, "fixed_minutes": 0, "count_by": "studerende"},
        "Mundtlig – større projekt/speciale": {"minutes_per_student": 60, "fixed_minutes": 0, "count_by": "studerende"},
        "Skriftlig – kort opgave": {"minutes_per_student": 20, "fixed_minutes": 0, "count_by": "besvarelser"},
        "Skriftlig – projekt/rapport": {"minutes_per_student": 60, "fixed_minutes": 0, "count_by": "besvarelser"},
        "Kombineret skriftlig + mundtlig": {"minutes_per_student": 90, "fixed_minutes": 0, "count_by": "studerende"},
        "Gruppeeksamen": {"minutes_per_student": 0, "fixed_minutes": 60, "minutes_per_group": 60, "count_by": "grupper"},
    },
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


config = load_config()

st.title("🧾 Censorafregning – aflønningsindikator")
st.caption("Estimat for ekstern censur ved danske universiteter. Brug altid den konkrete censornorm fra eksamensplanen/studieadministrationen som endelig kilde.")

with st.sidebar:
    st.header("Globale satser")
    university = st.selectbox("Universitet", config["universities"], index=0)
    rate_name = st.selectbox("Censorsats", list(config["rates"].keys()), index=0)
    hourly_rate = st.number_input("Kr. pr. censortime", value=float(config["rates"][rate_name]), min_value=0.0, step=1.0)
    vacation_pct = st.number_input("Feriegodtgørelse (%)", value=float(config.get("vacation_pay_pct", 12.5)), min_value=0.0, max_value=30.0, step=0.5)
    include_vacation = st.checkbox("Vis inkl. feriegodtgørelse", value=True)
    st.divider()
    st.header("Transport")
    include_transport = st.checkbox("Medtag kørselsgodtgørelse", value=False)
    km = st.number_input("Km tur/retur", value=0.0, min_value=0.0, step=10.0, disabled=not include_transport)
    km_rate = st.number_input("Kr./km", value=float(config.get("km_rate_low", 2.23)), min_value=0.0, step=0.01, disabled=not include_transport)

st.subheader("Eksamenstyper")

if "rows" not in st.session_state:
    st.session_state.rows = [
        {"type": "Mundtlig – standard bachelor/kursus", "count": 11, "groups": 0, "minutes_per_unit": 30, "fixed_minutes": 0},
        {"type": "Skriftlig – projekt/rapport", "count": 1, "groups": 0, "minutes_per_unit": 60, "fixed_minutes": 0},
    ]

col_a, col_b = st.columns([1, 4])
with col_a:
    if st.button("+ Tilføj linje", use_container_width=True):
        st.session_state.rows.append({"type": "Mundtlig – standard bachelor/kursus", "count": 1, "groups": 0, "minutes_per_unit": 30, "fixed_minutes": 0})
with col_b:
    if st.button("Nulstil eksempel", use_container_width=True):
        st.session_state.rows = [{"type": "Mundtlig – standard bachelor/kursus", "count": 1, "groups": 0, "minutes_per_unit": 30, "fixed_minutes": 0}]

rows_out = []
for i, row in enumerate(st.session_state.rows):
    with st.expander(f"Linje {i+1}: {row['type']}", expanded=True):
        c1, c2, c3, c4, c5 = st.columns([2.5, 1, 1, 1, 1])
        with c1:
            exam_type = st.selectbox("Type", list(config["exam_templates"].keys()), key=f"type_{i}", index=list(config["exam_templates"].keys()).index(row["type"]) if row["type"] in config["exam_templates"] else 0)
        template = config["exam_templates"][exam_type]
        default_minutes = int(template.get("minutes_per_student", template.get("minutes_per_group", 30)))
        with c2:
            count_label = "Antal grupper" if template.get("count_by") == "grupper" else "Antal studerende/besvarelser"
            count = st.number_input(count_label, min_value=0, value=int(row.get("count", 1)), step=1, key=f"count_{i}")
        with c3:
            minutes_per_unit = st.number_input("Minutter pr. enhed", min_value=0.0, value=float(row.get("minutes_per_unit", default_minutes)), step=5.0, key=f"mpu_{i}")
        with c4:
            fixed_minutes = st.number_input("Fast tid, min.", min_value=0.0, value=float(row.get("fixed_minutes", template.get("fixed_minutes", 0))), step=5.0, key=f"fixed_{i}")
        with c5:
            remove = st.button("Fjern", key=f"remove_{i}", use_container_width=True)
        if remove:
            st.session_state.rows.pop(i)
            st.rerun()
        total_minutes = count * minutes_per_unit + fixed_minutes
        rows_out.append({
            "Universitet": university,
            "Eksamenstype": exam_type,
            "Antal": count,
            "Min/enhed": minutes_per_unit,
            "Fast min": fixed_minutes,
            "Timer": total_minutes / 60,
            "Honorar ekskl. ferie": total_minutes / 60 * hourly_rate,
        })

result = pd.DataFrame(rows_out)
if result.empty:
    st.info("Tilføj mindst én eksamenslinje.")
    st.stop()

subtotal = float(result["Honorar ekskl. ferie"].sum())
vacation = subtotal * vacation_pct / 100 if include_vacation else 0.0
transport = km * km_rate if include_transport else 0.0
total = subtotal + vacation + transport
hours_total = float(result["Timer"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Censortimer", f"{hours_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
m2.metric("Honorar ekskl. ferie", f"{subtotal:,.0f} kr.".replace(",", "."))
m3.metric("Feriegodtgørelse", f"{vacation:,.0f} kr.".replace(",", "."))
m4.metric("Estimeret total", f"{total:,.0f} kr.".replace(",", "."))

st.dataframe(result.style.format({"Timer": "{:.2f}", "Honorar ekskl. ferie": "{:,.0f} kr.", "Min/enhed": "{:.0f}", "Fast min": "{:.0f}"}), use_container_width=True)

csv = result.to_csv(index=False).encode("utf-8")
st.download_button("Download beregning som CSV", data=csv, file_name="censorafregning.csv", mime="text/csv")

st.divider()
st.subheader("Redigér standardnormer")
st.write("Ændr normerne her, hvis SDU/DTU/AAU/AU eller den konkrete eksamensansvarlige oplyser en anden norm.")

norm_df = pd.DataFrame([
    {"Eksamenstype": k, "Minutter pr. enhed": v.get("minutes_per_student", v.get("minutes_per_group", 0)), "Fast minutter": v.get("fixed_minutes", 0), "Tælles efter": v.get("count_by", "studerende")}
    for k, v in config["exam_templates"].items()
])
edited = st.data_editor(norm_df, use_container_width=True, num_rows="dynamic")
if st.button("Gem normer lokalt"):
    new_templates = {}
    for _, r in edited.iterrows():
        if str(r["Eksamenstype"]).strip():
            new_templates[str(r["Eksamenstype"]).strip()] = {
                "minutes_per_student": float(r["Minutter pr. enhed"]),
                "fixed_minutes": float(r["Fast minutter"]),
                "count_by": str(r["Tælles efter"]).strip() or "studerende",
            }
    config["exam_templates"] = new_templates
    config["rates"][rate_name] = hourly_rate
    config["vacation_pay_pct"] = vacation_pct
    config["km_rate_low"] = km_rate
    save_config(config)
    st.success("Gemt i rates_and_norms.json")

with st.expander("Kilder og forbehold"):
    st.markdown(
        """
- Finansministeriets/Medarbejder- og Kompetencestyrelsens lønoversigt viser censorvederlag pr. 1. april 2024: sats A 508,91 kr./time, sats B 421,07 kr./time, sats C 350,13 kr./time, sats D 304,92 kr./time, sats E 252,02 kr./time og sats F 208,55 kr./time.  
- Cirkulæret om censorvederlag siger, at både skriftlig og mundtlig censur beregnes efter tidsnormer fastsat for den konkrete prøve, og at forberedelse/møder mv. normalt er inkluderet i censorvederlaget.  
- For universiteter og højere læreanstalter anvendes normalt sats A. Normtid varierer efter eksamenstype og lokal praksis, så appens normer er indikatorer, ikke en garanti for udbetaling.  
- Transport og evt. udlæg afregnes efter lokale regler og statens satser, hvis eksamen er fysisk.
        """
    )
