# Deployment Configuration for Psychology Today Scraper

## Deploy to Render

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login** with your GitHub account
3. **Click "New +"** → **"Web Service"**
4. **Connect Repository**: Select `psychtoday_scraper`
5. **Configure**:
   - **Name**: `psychology-today-scraper`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: `Free`

6. **Click "Create Web Service"**

Your app will be live at: `https://psychology-today-scraper.onrender.com`

## Deploy to Railway

1. **Go to [railway.app](https://railway.app)**
2. **Login with GitHub**
3. **"New Project"** → **"Deploy from GitHub repo"**
4. **Select**: `psychtoday_scraper`
5. **Railway auto-detects** Python and deploys

## Deploy to Fly.io

1. **Install Fly CLI**: `npm install -g @fly.io/flyctl`
2. **Login**: `fly auth login`
3. **In your project**: `fly launch`
4. **Follow prompts** and deploy

## Environment Variables

For production, set these in your hosting dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key-here`

## Notes

- **Database**: SQLite works for small-scale usage
- **Selenium**: May need additional setup on some platforms
- **Chrome Driver**: Included via webdriver-manager
- **Free Tier Limits**: Check hosting provider limits

## Recommended: Render

- ✅ **Easiest setup**
- ✅ **Auto-deploys from GitHub**
- ✅ **Free SSL certificate**
- ✅ **Custom domain support**
- ✅ **750 hours/month free**
