# Get your Refurbi preview link (about 3 minutes of your time)

You need a GitHub account (you already have one). Everything else is automatic.

1. Go to **render.com** and choose **Sign up with GitHub**. Allow access to the `fun2tube/Refurbi` repo when asked.
2. Click **New** > **Blueprint**.
3. Choose the repo **fun2tube/Refurbi** and click **Connect**.
4. Click **Apply**. Render now builds a database, the API and the website. Wait about **10 minutes**.
5. Open the service called **refurbi-web** in the Render dashboard and click the link at the top (ends in `.onrender.com`). That is your preview link.

Then tell the build agent: add a line `Preview URL: <your link>` to `PROGRESS.md`.

## Demo admin login
- Open `<your link>/admin/login`.
- Email: `admin@demo.refurbi`
- Password: in Render, open **refurbi-api** > **Environment** > `SUPER_ADMIN_PASSWORD` > click the eye icon to reveal it.

Every page shows a "Demo data" banner. The stock, counters and prices are fake.

## Good to know
- **Free services go to sleep** when nobody uses them. The first page load after a pause can take about **1 minute**. If the catalogue or login says it can't reach the API, wait a minute and retry.
- **The free database expires** after Render's free period (currently 30 days) and Render deletes it. To recreate it: in the Render dashboard open the Blueprint (**Blueprints** > Refurbi) and click **Manual sync**; if the database is gone, delete the old `refurbi-db` entry, then Manual sync again. The demo data is re-created automatically on the next API start. Nothing real is stored in the preview.
- To stop paying attention to it completely: Render dashboard > Blueprints > Refurbi > Delete.
