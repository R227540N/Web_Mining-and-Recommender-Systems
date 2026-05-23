🌍 UZ Global News — Vercel Deployment
A live AI-powered news aggregator for the University of Zimbabwe, deployed permanently on Vercel.
---
📁 Project Structure
```
uz-news/
├── api/
│   ├── index.py       ← Flask app (Vercel entry point)
│   └── uz_logo.png    ← Your UZ logo (add this file!)
├── vercel.json        ← Vercel routing & build config
├── requirements.txt   ← Python dependencies
└── README.md
```
---
🚀 Deploy in 5 Steps
1. Add your UZ logo
Copy your logo file into the `api/` folder and name it `uz_logo.png`.
2. Push to GitHub
```bash
git init
git add .
git commit -m "Initial deploy"
git remote add origin https://github.com/YOUR_USERNAME/uz-news.git
git push -u origin main
```
3. Connect to Vercel
Go to vercel.com and sign in (free account)
Click "Add New Project"
Import your GitHub repo
Leave all settings as default — Vercel auto-detects the config
Click Deploy
4. Get your permanent URL
Vercel gives you a URL like:
```
https://uz-news.vercel.app
```
This link works forever — no need to keep anything running.
5. (Optional) Redeploy after changes
Any `git push` to the `main` branch triggers an automatic redeploy.
---
⚙️ How It Works
Component	Role
`feedparser`	Fetches RSS feeds from BBC, CNN, Fox, Wired, CNBC
`TF-IDF`	Converts article text into numerical feature vectors
`K-Means`	Clusters similar articles into topic groups
`Flask`	Serves the rendered HTML page
`Vercel`	Hosts the app as a serverless function — always on
---
⚠️ Vercel Free Tier Limits
Limit	Value
Function execution time	30 seconds max
Bandwidth	100 GB / month
Deployments	Unlimited
The app fetches 20 articles per feed × 5 feeds = up to 100 articles per request, which comfortably fits within the 30s limit.
