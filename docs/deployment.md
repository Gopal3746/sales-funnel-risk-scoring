# Streamlit Community Cloud deployment

## 1. Push the repository to GitHub

From the project directory:

```bash
git init
git branch -M main
git add .
git commit -m "feat: build sales funnel analytics and deal scoring"
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```


## 2. Create the Streamlit app

1. Open Streamlit Community Cloud.
2. Choose **Create app**.
3. Select the GitHub repository and `main` branch.
4. Set the app file to `dashboard/app.py`.
5. Deploy.

The repository includes generated model/scoring artifacts, so the dashboard can start without retraining on every deployment.

## 3. Optional Claude summaries

In the Streamlit app settings, add a secret/environment variable:

```toml
ANTHROPIC_API_KEY = "your-key"
ANTHROPIC_MODEL = "claude-haiku-4-5"
```

Do not commit API keys to GitHub.

## 4. After deployment

Once deployed, add the public Streamlit URL to the README.
