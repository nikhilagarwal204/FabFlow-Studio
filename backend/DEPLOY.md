# FabFlow Studio Backend - Deployment Guide

## Deploying to Render

### Option 1: Deploy via Render Dashboard (Recommended)

1. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub/GitLab repository

2. **Configure the service**
   - **Name**: `fabflow-studio-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`

3. **Set Environment Variables**
   In the Render dashboard, add these environment variables:
   
   | Key | Description |
   |-----|-------------|
   | `OPENAI_API_KEY` | Your OpenAI API key |
   | `BRIA_API_KEY` | Your Bria FIBO API key |
   | `FRONTEND_URL` | Your Vercel frontend URL (e.g., `https://fabflow-studio.vercel.app`) |

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

### Option 2: Deploy via render.yaml (Infrastructure as Code)

1. **Update render.yaml**
   Edit `backend/render.yaml` and update the `FRONTEND_URL` value:
   ```yaml
   - key: FRONTEND_URL
     value: https://your-actual-frontend-domain.vercel.app
   ```

2. **Create Blueprint**
   - Go to Render Dashboard → "Blueprints"
   - Click "New Blueprint Instance"
   - Connect your repository
   - Render will detect `render.yaml` and create the service

3. **Set Secret Environment Variables**
   After deployment, go to the service settings and add:
   - `OPENAI_API_KEY`
   - `BRIA_API_KEY`

## Post-Deployment

### Verify Deployment

1. **Health Check**
   ```bash
   curl https://your-service.onrender.com/health
   # Expected: {"status":"healthy"}
   ```

2. **API Root**
   ```bash
   curl https://your-service.onrender.com/
   # Expected: {"status":"ok","message":"FabFlow Studio API is running"}
   ```

### Update Frontend Configuration

Update your frontend's `.env.local` (or Vercel environment variables):
```
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - The Dockerfile installs FFmpeg automatically
   - If issues persist, check Render build logs

2. **API Key errors**
   - Verify environment variables are set correctly in Render dashboard
   - Check that keys don't have extra whitespace

3. **CORS errors**
   - Ensure `FRONTEND_URL` matches your actual frontend domain
   - Multiple origins can be comma-separated: `https://domain1.com,https://domain2.com`

4. **Slow cold starts (Free tier)**
   - Render free tier spins down after inactivity
   - First request after idle may take 30-60 seconds
   - Consider upgrading to paid tier for production

### Viewing Logs

- Go to Render Dashboard → Your Service → "Logs"
- Filter by "Deploy" for build logs
- Filter by "Service" for runtime logs

## Local Docker Testing

Before deploying, you can test the Docker build locally:

```bash
cd backend

# Build the image
docker build -t fabflow-backend .

# Run with environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e BRIA_API_KEY=your_key \
  -e FRONTEND_URL=http://localhost:3000 \
  fabflow-backend

# Test the API
curl http://localhost:8000/health
```

## Architecture Notes

- **Temp Storage**: Generated frames and videos are stored in `/tmp/fabflow`
- **In-Memory Jobs**: Job status is stored in memory (resets on restart)
- **FFmpeg**: Installed via apt-get in the Docker image
- **Port**: Render sets `PORT` env var; defaults to 8000
