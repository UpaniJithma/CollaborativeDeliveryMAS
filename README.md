# CollaborativeDeliveryMAS — Installation and Setup Guide

## 1. Project Repository

Clone the project from the GitHub repository:

**Repository:** https://github.com/UpaniJithma/CollaborativeDeliveryMAS

If the repository is private, ensure you have been granted access and are signed in to GitHub.

## 2. Prerequisites

Install the following software before running the project:

- **Python 3.11** — recommended version for this project.
- **Git** — to clone the GitHub repository.
- **Visual Studio Code** — recommended editor, but optional.

Verify the installations by opening PowerShell or the VS Code terminal and running:

```powershell
python --version
git --version
```

The Python version should be Python 3.11.x.

## 3. Clone the Repository

Open PowerShell and run:

```powershell
cd $HOME\Desktop
git clone https://github.com/UpaniJithma/CollaborativeDeliveryMAS.git
cd CollaborativeDeliveryMAS
```

If GitHub requests authentication, sign in using an authorized account.

## 4. Create a Virtual Environment

Inside the project folder, run:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

## 5. Install Dependencies

With the virtual environment activated, run:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Wait until the installation completes successfully.

## 6. Configure the Environment

For a local test run, open PowerShell in the project directory and set:

```powershell
$env:MAS_AGENT_XMPP_PASSWORD = "TestPassword123!"
$env:MAS_UI_XMPP_PASSWORD = "TestPassword123!"
$env:MAS_DASHBOARD_PASSWORD = "LocalDashboard2026!"
$env:MAS_DATABASE_PATH = (Join-Path (Get-Location).Path "delivery_mas.db")
$env:MAS_XMPP_BIND_HOST = "localhost"
```

These are example local-development credentials. Do not reuse them for a publicly accessible deployment.

## 7. Prepare the Database

Check whether the project includes a database initialization script or automatically creates the database on startup.

The project uses SQLite and the database file is named `delivery_mas.db`. If the database is created automatically, follow the project's startup process.

**Important:** If the project requires preloaded courier records, obtain an approved copy of the database from the project owner. A new empty database may not contain the courier data needed for allocation testing. Do not overwrite an existing database containing important data.

## 8. Start the Application

Use only one startup method at a time.

### Option A — Run the deployment launcher

From the activated virtual environment, run:

```powershell
python deploy.py
```

If startup succeeds, open:

http://localhost:10000

### Option B — Use the batch launcher

If the project owner confirms that `start_system.bat` is configured correctly, run:

```powershell
.\start_system.bat
```

The dashboard may be available at:

http://localhost:8502

Do not run both startup methods simultaneously because they may compete for the same ports.

## 9. Log In and Test

1. Open the dashboard URL.
2. Log in using the dashboard password configured in Step 6.
3. Check courier availability and service areas.
4. Register a test parcel.
5. Verify whether the Coordinator allocates a suitable courier.
6. Check parcel tracking and allocation history.
7. Review the agent logs if an allocation fails.

## 10. Troubleshooting

- **`ModuleNotFoundError`:** Activate `.venv` and install `requirements.txt` again.
- **Port 5222 already in use:** Check whether another XMPP server instance is running.
- **Dashboard unavailable:** Check the startup terminal for errors and verify the correct port.
- **Parcel remains unallocated:** Check courier service areas, remaining capacity, availability, and the Coordinator's allocation logic.
- **Database has no courier records:** Confirm that the correct database is being used and initialized.
- **GitHub access denied:** Ask the repository owner to grant access.

## 11. Completion Checklist

- [ ] Python 3.11 installed
- [ ] Repository cloned successfully
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Correct database prepared
- [ ] XMPP server and agents started successfully
- [ ] Dashboard opened in the browser
- [ ] Test parcel registered and allocation checked

**Note:** This guide describes the expected setup process. If any command fails, share the complete error message with the project owner before changing application code or deleting database files.
