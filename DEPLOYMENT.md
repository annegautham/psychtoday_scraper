# Deployment Configuration for Psychology Today Scraper

## Deploy to Fly.io (Recommended)

### Prerequisites
1. **Install Fly CLI**:
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Linux/Mac
   curl -L https://fly.io/install.sh | sh
   
   # Or via package managers
   npm install -g @fly.io/flyctl
   brew install flyctl
   ```

### Quick Deploy
1. **Login to Fly.io**:
   ```bash
   flyctl auth login
   ```

2. **Launch your app**:
   ```bash
   flyctl launch
   ```
   - Choose app name: `psychtoday-scraper`
   - Choose region: `iad` (US East)
   - Don't deploy immediately: `N`

3. **Deploy**:
   ```bash
   flyctl deploy
   ```

4. **Your app will be live at**: `https://psychtoday-scraper.fly.dev`

### Using the Deploy Scripts

**Windows**:
```powershell
.\deploy.ps1
```

**Linux/Mac**:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Fly.io Features
- ✅ **Free Tier**: 3 shared-cpu-1x machines
- ✅ **Auto-scaling**: Scales to zero when not used
- ✅ **Global deployment**: Edge locations worldwide
- ✅ **Custom domains**: Add your own domain
- ✅ **Persistent storage**: Optional volumes for database

### Monitoring
```bash
# View logs
flyctl logs

# SSH into machine
flyctl ssh console

# Scale machines
flyctl scale count 1

# Check status
flyctl status
```

---

## Alternative: Deploy to Render

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

---

## Alternative: Deploy to Railway

1. **Go to [railway.app](https://railway.app)**
2. **Login with GitHub**
3. **"New Project"** → **"Deploy from GitHub repo"**
4. **Select**: `psychtoday_scraper`
5. **Railway auto-detects** Python and deploys

---

## Environment Variables

For production, set these in your hosting dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key-here`
- `PORT=5000`

## Database Notes

- **SQLite**: Works for small-scale usage (included)
- **PostgreSQL**: For production scale (available on all platforms)
- **Persistent Storage**: Consider adding volumes for large databases

## Chrome/Selenium Notes

- **Fly.io**: Works with included Dockerfile
- **Render**: May need additional buildpack configuration
- **Railway**: Usually works out of the box

## Free Tier Limits

- **Fly.io**: 3 shared machines, auto-sleep after inactivity
- **Render**: 750 hours/month, sleeps after 15min inactivity
- **Railway**: $5 credit/month usage-based

## Recommended: Fly.io

- ✅ **Best performance**
- ✅ **Most reliable for Selenium**
- ✅ **Great free tier**
- ✅ **Easy scaling**
- ✅ **Global edge network**
