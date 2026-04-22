# Interactive Disease Dashboard — Live Voting Version

This is a classroom/demo extension of your Metro Vancouver outbreak simulator.

## What it adds
- presenter dashboard
- audience voting page via `?mode=vote`
- live shared scenario votes using SQLite
- freeze/unfreeze voting
- freeze current scenario snapshot
- live map updates as students push values up or pull them down
- push-vs-pull chart showing which factors are driving spread up or down

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
1. Deploy to Streamlit Community Cloud
2. Enter the public app URL in the sidebar
3. Students scan the QR code
4. The voting page opens at `?mode=vote`

## Notes
- SQLite is fine for a classroom demo and a single deployed app instance
- votes may reset on redeploy, which is usually acceptable for a presentation
