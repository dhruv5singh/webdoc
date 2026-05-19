# Network Automation (deploy guide)

This repository contains a Streamlit/Flask UI and a monitoring script (`ping_test.py`).

This guide shows three ways to expose the app publicly:

1. Deploy the container to Render (recommended for simplicity)
2. Deploy to Fly.io (edge hosting)
3. Quick demo with ngrok (temporary)

Prerequisites
- A GitHub repository with this code
- Dockerfile (already present)
- A GitHub Actions workflow (this repo contains `.github/workflows/docker-publish.yml`) which pushes an image to GitHub Container Registry (GHCR) on pushes to master

Build & publish (automatic via GitHub Actions)
- Push to `master` and GitHub Actions will build and push the image to `ghcr.io/<owner>/<repo>:latest`.

Render (quick deploy)
1. Create an account at https://render.com
2. Create a new Web Service -> Connect to GitHub -> pick this repository
3. For the service, choose Docker (Render will build from your Dockerfile), set port to `8501` and a health check route (e.g., `/`)
4. Deploy — Render will build and run the container and provide a public URL.

Fly.io (alternative)
1. Install `flyctl` and create an account
2. run `flyctl launch` and follow prompts (or create a new app and `flyctl deploy`)

ngrok (temporary demo)
1. Run locally: `streamlit run app.py` (or `python app.py` for Flask)
2. Install ngrok and run `ngrok http 8501` (or 5000 for Flask)
3. Share the public HTTPS URL ngrok provides

GitHub Pages (static read-only dashboard)
1. This repository now contains a read-only static dashboard under `docs/` that reads `report.csv` from the repo and displays it.
2. To enable GitHub Pages for this repo:
	- In your repository on GitHub go to Settings → Pages
	- Select Source: Branch `master` and folder `/docs`
	- Save — GitHub will publish the site at `https://<your-username>.github.io/<repo>` (may take a minute)
3. Note: This static UI is read-only. To make live checks (add rows to `report.csv`) you still need a backend service (Render, Fly, etc.) that writes to the repository or exposes an API the static UI can call.

Backend API contract (optional integration)
- The static UI supports sending a POST request with JSON { "site": "example.com" } to a backend endpoint.
- Expected request: POST /api/run with JSON body { "site": "example.com" }
- Expected response: 200 OK (body optional). The UI will wait ~3s and then refresh `report.csv`.
- Security: protect this endpoint (token or basic auth) to prevent misuse.
Security notes
- Do not embed GitHub PATs or other secrets in client code. Use server-side secrets.
- The Streamlit dev server is not production-grade. For production, consider running behind a proper web server.
