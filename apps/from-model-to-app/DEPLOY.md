# Hosting the dashboard on DigitalOcean App Platform

The dashboard is a local teaching app first (`python launch.py`, see
`README.md`). This document covers the optional hosted copy for students who
cannot set it up on their own machines. Nothing in the app changes for
hosting: DigitalOcean starts the same `app.py` with server-appropriate
Streamlit flags, defined in `.do/app.yaml` at the repository root.

## One-time deployment (DigitalOcean console)

1. Sign in at <https://cloud.digitalocean.com> → **Create** → **App Platform**.
2. Choose **GitHub** as the source and authorize access to
   `jrmst102/businessanalytics` (branch `main`). App Platform picks up the
   committed spec at `.do/app.yaml`, which sets:
   - source directory `apps/from-model-to-app` (dependencies from its
     `requirements.txt`, Python 3.12);
   - run command
     `streamlit run app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false`;
   - one instance, 1 vCPU / 1 GB (`apps-s-1vcpu-1gb`);
   - health check on Streamlit's `/_stcore/health`.
3. Review the plan and click **Create resources**. The first build takes a few
   minutes; the app then gets a URL like
   `https://from-model-to-app-xxxxx.ondigitalocean.app` — that is the link to
   give students.

Command-line alternative: `doctl apps create --spec .do/app.yaml`
(then `doctl apps list` for the URL).

**Auto-deploy is on** (`deploy_on_push: true`): every push to `main` rebuilds
the hosted app. Turn it off in the app's settings if you prefer manual deploys
during the semester.

## Classroom notes for the hosted copy

- **Sessions are independent.** Each browser tab is its own Streamlit session:
  every student trains their own model and their results never mix (all fitted
  state lives in `st.session_state`). The dataset itself is loaded once and
  shared read-only.
- **Shared CPU.** All students share one instance. Single fits are fast
  (ensemble ≈ 7 s on the reference machine), but if a whole class clicks
  "Train model" at once, fits queue up. For a live in-class exercise with many
  simultaneous users, scale up temporarily (Settings → dashboard component →
  larger instance, or more instances) and scale back afterwards.
- **Cost.** The 1 vCPU / 1 GB instance bills per month while the app exists.
  You can destroy the app after the unit and recreate it next term from the
  same spec — the URL changes unless you attach a custom domain.
- **No secrets, no uploads.** The app bundles the approved CSV, calls no
  external services, and accepts no file uploads, so there is nothing
  sensitive to configure.
- The specification's "no cloud accounts" exclusion applies to the student
  experience (students only need the URL); the instructor's DigitalOcean
  account hosts it.

## Verifying a deployment

Open the URL and check: the three tabs (Data, Model, Test) render with the
course footer; training the default KNN shows the four metric cards; a typed
prediction works on the Test tab. The health endpoint
`<app-url>/_stcore/health` returns `ok`.
