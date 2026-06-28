# Censorafregning

Streamlit-app til at estimere censorvederlag for teknisk-videnskabelige universitetsfag.

Appen indeholder:

- statslig censorsats som redigerbar timesats
- SDU TEK Payment Standards fra september 2022 som konkrete normtider
- mundtlige eksamener med 60 minutters minimum
- skriftlige eksamener med fast oprettelsestid + minutter pr. besvarelse/sæt
- rapporter, bachelorprojekter, diplomingeniør-afgangsprojekter og specialer
- transport/udlæg som særskilt estimat
- CSV-download af beregningen

## Kør lokalt

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy på Streamlit Cloud

Main file path:

```text
app.py
```

## Forbehold

Dette er en indikator, ikke officiel afregning. Brug altid den konkrete norm og den seneste censorsats fra universitet/studieadministration.
