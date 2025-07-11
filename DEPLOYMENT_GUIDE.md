# Deployment Guide for Render

## Prerequisites
- Your code is pushed to GitHub
- Your PostgreSQL database is set up on Render
- Your database dump has been imported

## Step 1: Push Your Updated Code to GitHub

1. Open GitHub Desktop
2. Commit all your changes (including the updated files)
3. Push to GitHub

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to deploy

### Option B: Manual Deployment
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** `churn-prediction-system`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add Environment Variables:
   - **Key:** `DATABASE_URL`
   - **Value:** Your Render PostgreSQL connection string
6. Click "Create Web Service"

## Step 3: Configure Environment Variables

In your Render web service settings, add:
- `DATABASE_URL`: Your PostgreSQL connection string from Render
- `SECRET_KEY`: A random secret key for Flask sessions

## Step 4: Deploy and Test

1. Render will automatically build and deploy your application
2. Once deployed, visit your application URL
3. Test the login with:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

### Common Issues:
1. **Build fails:** Check that all dependencies are in `requirements.txt`
2. **Database connection fails:** Verify `DATABASE_URL` is correct
3. **App crashes:** Check Render logs for error messages

### View Logs:
- Go to your web service on Render
- Click "Logs" tab to see deployment and runtime logs

## Security Notes

- Change the default admin password after first login
- Consider adding HTTPS redirect
- Review and update the Flask secret key 