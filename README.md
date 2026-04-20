# High School Disease Forecast Demo

A mobile-friendly Streamlit app that lets students change forecasting inputs and see how predicted respiratory disease activity changes across zones.

## What this demo does

- Lets students control disease type and transmission assumptions.
- Visualizes forecast cases by zone on a map.
- Estimates hospital admissions and ED visits.
- Generates a QR code from the public app URL so students can open it on their phones.

## Recommended stack

- **Frontend + backend:** Streamlit
- **Charts/maps:** Plotly
- **QR code generation:** qrcode + Pillow
- **Hosting:** Streamlit Community Cloud for the easiest free public demo, or Render if you want more control.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repo and upload these files.
2. Sign in to Streamlit Community Cloud.
3. Choose the repo, branch, and `app.py` as the entrypoint.
4. Deploy.
5. Copy the public URL into the QR section of the app.
6. Download the generated QR code and put it on your final slide.

## Deploy on Render

1. Push the repo to GitHub.
2. Create a **Web Service** on Render.
3. Build command:

```bash
pip install -r requirements.txt
```

4. Start command:

```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

## Adapting this to real data

To turn this into a more realistic public health demo:

- Replace `data/zones.geojson` with real local health regions or neighborhood polygons.
- Replace `src/model.py` with your real forecasting pipeline.
- Add uploaded CSV support for weekly case counts.
- Connect to a lightweight API or nightly batch predictions.

## Suggested repo structure

```text
highschool_disease_demo/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   └── zones.geojson
└── src/
    ├── data_utils.py
    ├── model.py
    └── qr_utils.py
```
