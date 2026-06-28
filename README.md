# Censorafregning

Streamlit-app til estimat af censorhonorar ved danske universiteter, især SDU, DTU, AAU og AU.

## Kør lokalt

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Kør i Streamlit Community Cloud

1. Push filerne til GitHub-repoet.
2. Gå til Streamlit Community Cloud.
3. Vælg repoet `tbuhl/Censorafregning`.
4. Main file: `app.py`.
5. Deploy.

## Vigtige antagelser

- Universiteter/højere læreanstalter er sat til statslig censorsats A som default.
- Normtid varierer efter den konkrete prøve og skal tjekkes mod eksamensplan/studieadministration.
- Appen er en indikator, ikke en juridisk afregningsgaranti.

## Kilder

- Finansministeriets/Medarbejder- og Kompetencestyrelsens lønoversigt, censorvederlag kap. 8.2, satser pr. 1. april 2024.
- Cirkulære om censorvederlag: vederlag beregnes efter censortime og konkrete tidsnormer for mundtlig/skriftlig prøve.
- AU Tech beskriver 125/250-timers fortolkning for censorer.
- SDU beskriver afregning via eForms.
