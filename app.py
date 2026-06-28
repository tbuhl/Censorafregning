import json
from pathlib import Path

import pandas as pd
import streamlit as st

CONFIG_PATH = Path(__file__).with_name("rates_and_norms.json")

st.set_page_config(page_title="Censorafregning", page_icon="🧾", layout="wide")


def dk_number(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


config = load_config()

st.title("🧾 Censorafregning – aflønningsindikator")
st.caption(
    "Indikator for ekstern censur ved teknisk-videnskabelige universitetsfag. "
    "SDU TEK-normerne fra 2022 er indbygget; brug altid den konkrete norm fra studieadministrationen som endelig kilde."
)

with st.sidebar:
    st.header("Satser")
    university = st.selectbox("Universitet", config["universities"], index=0)
    rate_name = st.selectbox("Censorsats", list(config["rates"].keys()), index=0)
    hourly_rate = st.number_input(
        "Kr. pr. censortime",
        value=float(config["rates"][rate_name]),
        min_value=0.0,
        step=1.0,
    )
    vacation_pct = st.number_input(
        "Feriegodtgørelse (%)",
        value=float(config.get("vacation_pay_pct", 12.5)),
        min_value=0.0,
        max_value=30.0,
        step=0.5,
    )
    include_vacation = st.checkbox("Vis inkl. feriegodtgørelse", value=True)

    st.divider()
    st.header("Transport / udlæg")
    include_transport = st.checkbox("Medtag transport/udlæg", value=False)
    km = st.number_input("Km tur/retur", value=0.0, min_value=0.0, step=10.0, disabled=not include_transport)
    km_rate = st.number_input("Kr./km", value=float(config.get("km_rate_low", 2.23)), min_value=0.0, step=0.01, disabled=not include_transport)
    other_expenses = st.number_input("Andre udlæg, kr.", value=0.0, min_value=0.0, step=100.0, disabled=not include_transport)

st.subheader("Eksamenstyper")

TEMPLATES = config["exam_templates"]
template_names = list(TEMPLATES.keys())

if "rows" not in st.session_state:
    st.session_state.rows = [
        {"type": "SDU TEK G – 30 min mundtlig/bachelor/semesterprojekt", "count": 11},
        {"type": "SDU TEK Q – Civilingeniør bachelorprojekt / Final Project", "count": 1},
    ]

c_add, c_reset = st.columns([1, 4])
with c_add:
    if st.button("+ Tilføj linje", use_container_width=True):
        st.session_state.rows.append({"type": "SDU TEK D – 15 min mundtlig eksamen", "count": 1})
        st.rerun()
with c_reset:
    if st.button("Nulstil eksempel", use_container_width=True):
        st.session_state.rows = [{"type": "SDU TEK D – 15 min mundtlig eksamen", "count": 1}]
        st.rerun()

rows_out = []
for i, row in enumerate(st.session_state.rows):
    current_type = row.get("type", template_names[0])
    if current_type not in TEMPLATES:
        current_type = template_names[0]

    with st.expander(f"Linje {i + 1}: {current_type}", expanded=True):
        c1, c2, c3, c4, c5, c6 = st.columns([3.3, 1.0, 1.0, 1.0, 1.0, 0.8])
        with c1:
            exam_type = st.selectbox("Type", template_names, key=f"type_{i}", index=template_names.index(current_type))
        template = TEMPLATES[exam_type]
        is_oral = "Mundtlig" in str(template.get("category", ""))
        with c2:
            count = st.number_input(f"Antal {template.get('count_by', 'enheder')}", min_value=0, value=int(row.get("count", 1)), step=1, key=f"count_{i}")
        with c3:
            minutes_per_unit = st.number_input("Eksamen min/enhed", min_value=0.0, value=float(template.get("minutes_per_unit", 0)), step=5.0, key=f"mpu_{i}")
        with c4:
            fixed_minutes = st.number_input("Fast min.", min_value=0.0, value=float(template.get("fixed_minutes", 0)), step=5.0, key=f"fixed_{i}")
        with c5:
            minimum_minutes = st.number_input("Min. total", min_value=0.0, value=float(template.get("minimum_minutes", 0)), step=5.0, key=f"minimum_{i}")
        with c6:
            remove = st.button("Fjern", key=f"remove_{i}", use_container_width=True)

        include_prep = False
        prep_count = count
        prep_minutes_per_unit = 0.0
        prep_fixed_minutes = 0.0
        if is_oral:
            st.caption("Ved mundtlig projekt-/rapporteksamen kan du lægge rapportlæsning/forberedelse oveni selve eksaminationstiden.")
            p1, p2, p3, p4 = st.columns([1.4, 1.0, 1.0, 2.0])
            with p1:
                include_prep = st.checkbox("Medtag særskilt forberedelse/rapportlæsning", value=False, key=f"prep_on_{i}")
            with p2:
                prep_count = st.number_input("Antal rapporter/sæt", min_value=0, value=count, step=1, key=f"prep_count_{i}", disabled=not include_prep)
            with p3:
                prep_minutes_per_unit = st.number_input("Forberedelse min/enhed", min_value=0.0, value=0.0, step=10.0, key=f"prep_mpu_{i}", disabled=not include_prep)
            with p4:
                prep_fixed_minutes = st.number_input("Fast forberedelse min.", min_value=0.0, value=0.0, step=10.0, key=f"prep_fixed_{i}", disabled=not include_prep)

        if remove:
            st.session_state.rows.pop(i)
            st.rerun()

        exam_minutes = count * minutes_per_unit + fixed_minutes
        exam_paid_minutes = max(exam_minutes, minimum_minutes) if count > 0 else 0
        prep_minutes = (prep_count * prep_minutes_per_unit + prep_fixed_minutes) if include_prep else 0
        calculated_minutes = exam_minutes + prep_minutes
        paid_minutes = exam_paid_minutes + prep_minutes
        rows_out.append(
            {
                "Universitet": university,
                "Eksamenstype": exam_type,
                "Kategori": template.get("category", ""),
                "Antal": count,
                "Tælles efter": template.get("count_by", "enheder"),
                "Eksamen min/enhed": minutes_per_unit,
                "Fast eksamen min": fixed_minutes,
                "Minimum eksamen min": minimum_minutes,
                "Forberedelse min": prep_minutes,
                "Beregnet min": calculated_minutes,
                "Afregnet min": paid_minutes,
                "Timer": paid_minutes / 60,
                "Honorar ekskl. ferie": paid_minutes / 60 * hourly_rate,
                "Kilde": template.get("source", ""),
            }
        )

result = pd.DataFrame(rows_out)
if result.empty:
    st.info("Tilføj mindst én eksamenslinje.")
    st.stop()

subtotal = float(result["Honorar ekskl. ferie"].sum())
vacation = subtotal * vacation_pct / 100 if include_vacation else 0.0
transport = km * km_rate if include_transport else 0.0
expenses = other_expenses if include_transport else 0.0
total = subtotal + vacation + transport + expenses
hours_total = float(result["Timer"].sum())

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Censortimer", dk_number(hours_total, 2))
m2.metric("Honorar ekskl. ferie", f"{dk_number(subtotal)} kr.")
m3.metric("Feriegodtgørelse", f"{dk_number(vacation)} kr.")
m4.metric("Transport/udlæg", f"{dk_number(transport + expenses)} kr.")
m5.metric("Estimeret total", f"{dk_number(total)} kr.")

st.dataframe(
    result.style.format(
        {
            "Eksamen min/enhed": "{:.0f}",
            "Fast eksamen min": "{:.0f}",
            "Minimum eksamen min": "{:.0f}",
            "Forberedelse min": "{:.0f}",
            "Beregnet min": "{:.0f}",
            "Afregnet min": "{:.0f}",
            "Timer": "{:.2f}",
            "Honorar ekskl. ferie": "{:,.0f} kr.",
        }
    ),
    use_container_width=True,
)

csv = result.to_csv(index=False).encode("utf-8")
st.download_button("Download beregning som CSV", data=csv, file_name="censorafregning.csv", mime="text/csv")

st.divider()
st.subheader("SDU TEK-normer indbygget")
st.markdown(
    """
- Mundtlige eksamener: 15/20/25/30/45/60 minutter pr. studerende med minimum 60 minutter pr. eksamen.
- Ved mundtlige projekt-/rapporteksamener kan særskilt forberedelse/rapportlæsning tilføjes oveni selve mundtlige eksaminationstid.
- Skriftlige eksamener: MCQ, skriftlig ≤2 timer og skriftlig >2 timer med både fast oprettelsestid og minutter pr. besvarelse/sæt.
- Rapporter/projekter: fra 30 minutter pr. mindre rapport til 360 minutter pr. civilingeniørspeciale.
- Ifølge SDU TEK-vejledningen dækker normen aktiviteter relateret til eksamen, herunder forberedelse, eksamination, votering, karaktergivning, møder før/efter og evaluering.
- Ved mundtlig eksamen betales også for studerende, der er synlige i Digital Exam, men udebliver på dagen.
"""
)

with st.expander("Redigér standardnormer"):
    st.write("Ændr normerne her, hvis DTU/AAU/AU eller den konkrete eksamensansvarlige oplyser en anden norm.")
    norm_df = pd.DataFrame(
        [
            {
                "Eksamenstype": k,
                "Minutter pr. enhed": v.get("minutes_per_unit", 0),
                "Fast minutter": v.get("fixed_minutes", 0),
                "Minimum minutter": v.get("minimum_minutes", 0),
                "Tælles efter": v.get("count_by", "enheder"),
                "Kategori": v.get("category", ""),
                "Kilde": v.get("source", ""),
            }
            for k, v in TEMPLATES.items()
        ]
    )
    edited = st.data_editor(norm_df, use_container_width=True, num_rows="dynamic")
    if st.button("Gem normer lokalt"):
        new_templates = {}
        for _, r in edited.iterrows():
            if str(r["Eksamenstype"]).strip():
                new_templates[str(r["Eksamenstype"]).strip()] = {
                    "minutes_per_unit": float(r["Minutter pr. enhed"]),
                    "fixed_minutes": float(r["Fast minutter"]),
                    "minimum_minutes": float(r["Minimum minutter"]),
                    "count_by": str(r["Tælles efter"]).strip() or "enheder",
                    "category": str(r.get("Kategori", "")).strip(),
                    "source": str(r.get("Kilde", "")).strip(),
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
- Censortimesatsen i appen er sat til statens sats A for universiteter/højere læreanstalter. Kontrollér altid den nyeste lønoversigt.
- SDU TEK-normerne er fra dokumentet *Payment Standards for External Co-examiners*, revideret september 2022.
- Appen er en aflønningsindikator, ikke en officiel afregning. Den konkrete prøve, eksamensplan og studieadministration kan være afgørende.
- Transport, udlæg, bro, hotel og diæter kan være særskilt afregning og er derfor lagt uden for censorhonoraret.
        """
    )
