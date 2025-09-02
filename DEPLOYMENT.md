# AmpAI Deployment Guide

## 🚀 Deploy to Railway (Recommended)

Railway is the recommended platform for deploying AmpAI due to its support for large applications and generous resource limits.

### Prerequisites
- GitHub account
- Railway account (free tier available)
- Git installed locally

### Step 1: Prepare Repository
```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit - AmpAI deployment ready"

# Push to GitHub
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app)
2. Sign in with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your AmpAI repository
6. Railway will automatically detect the Dockerfile and begin deployment

### Step 3: Configure Environment (Optional)
In Railway dashboard:
1. Go to your project
2. Click on "Variables" tab
3. Add any custom environment variables if needed:
   - `PORT` (Railway sets this automatically)
   - `SECRET_KEY` (for production security)

### Step 4: Monitor Deployment
- Railway will build the Docker image (this takes 10-15 minutes)
- The model will be downloaded during build (~2.6GB)
- Once deployed, Railway will provide a public URL

## 🔧 Alternative Deployment Options

### Deploy to Render
1. Connect your GitHub repository to Render
2. Use the provided Dockerfile
3. Set build command: `docker build -t ampai .`
4. Set start command: `/app/start.sh`
5. Configure environment variables as needed

### Deploy to VPS/Cloud Server
```bash
# On your server
git clone YOUR_REPO_URL
cd ampAI
docker build -t ampai .
docker run -p 8081:8081 ampai
```

## 📋 Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] Large model files excluded from Git (handled by download script)
- [ ] Environment variables configured
- [ ] Dockerfile tested locally (optional but recommended)
- [ ] Railway project created and deployed
- [ ] Application accessible via public URL
- [ ] RAG system working (test with questions)
- [ ] AI responses functioning correctly

## 🔍 Troubleshooting

### Build Issues
- **Model download fails**: Check internet connectivity in build environment
- **Out of memory**: Increase Railway plan or optimize model size
- **Build timeout**: Model download can take time, be patient

### Runtime Issues
- **OpenAI API errors**: Check API key is set and billing is enabled
- **RAG system empty**: Sources may not have indexed properly
- **Port binding issues**: Railway handles port assignment automatically

### Performance Issues
- **Slow responses**: Consider upgrading Railway plan for more CPU/RAM
- **Memory errors**: Reduce context size or batch size in environment variables

## 📊 Resource Requirements

### Minimum Requirements
- **RAM**: 4GB (for 3B model)
- **CPU**: 2 cores
- **Storage**: 5GB (including model)
- **Bandwidth**: 1GB+ for model download

### Recommended Requirements
- **RAM**: 8GB
- **CPU**: 4 cores  
- **Storage**: 10GB
- **Bandwidth**: Unlimited

## 🔐 Security Considerations

1. **Change Secret Key**: Update `SECRET_KEY` environment variable
2. **HTTPS Only**: Railway provides HTTPS by default
3. **Rate Limiting**: Consider adding rate limiting for production use
4. **Access Control**: Add authentication if needed for sensitive data

## 🚨 Important Notes

- The AI model (2.6GB) is downloaded during deployment, not stored in Git
- First deployment takes longer due to model download
- Railway free tier has usage limits - monitor your usage
- The application includes electrical safety information - ensure proper disclaimers

## 📞 Support

If you encounter issues:
1. Check Railway build logs for errors
2. Verify all files are properly committed to Git
3. Test locally with Docker if possible
4. Check this deployment guide for common solutions

## 🔄 Updates and Maintenance

To update your deployment:
```bash
git add .
git commit -m "Update application"
git push origin main
```
Railway will automatically redeploy on Git push.

## 🌐 Accessing Your Deployed App

Once deployed, your AmpAI application will be available at:
- Railway: `https://your-app-name.railway.app`
- Custom domain can be configured in Railway dashboard

The application provides:
- Web chat interface at the root URL
- API endpoints for system status and chat
- File upload for additional knowledge sources
- Real-time AI responses with RAG-enhanced knowledge
