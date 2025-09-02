# AmpAI Deployment Guide

## 🚀 Deploy to Railway (Recommended)

Railway is the recommended platform for deploying AmpAI due to its support for large applications and generous resource limits. This OpenAI-powered version is much faster to deploy and more cost-effective than the previous Llama version.

### Prerequisites
- GitHub account
- Railway account (free tier available)
- OpenAI API key with billing enabled
- Git installed locally

### Step 1: Prepare Repository
```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit - AmpAI OpenAI deployment ready"

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

### Step 3: Configure OpenAI API Key (REQUIRED)
In Railway dashboard:
1. Go to your project
2. Click on "Variables" tab
3. Add your OpenAI API key:
   - Variable name: `OPENAI_API_KEY`
   - Value: `your_openai_api_key_here`
4. Optional variables:
   - `OPENAI_MODEL`: Choose model (default: gpt-4o)
   - `SECRET_KEY`: For production security (auto-generated if not set)

### Step 4: Monitor Deployment
- Railway will build the Docker image (takes 2-5 minutes - much faster!)
- No large model downloads needed - uses OpenAI's cloud API
- Once deployed, Railway will provide a public URL
- App will be ready when health check passes

## 🔧 Alternative Deployment Options

### Deploy to Render
1. Connect your GitHub repository to Render
2. Use the provided Dockerfile
3. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: Model choice (optional, default: gpt-4o)
4. Deploy - much faster than the old Llama version!

### Deploy to VPS/Cloud Server
```bash
# On your server
git clone YOUR_REPO_URL
cd ampAI
docker build -t ampai .
docker run -e OPENAI_API_KEY="your_key_here" -p 8081:8081 ampai
```

## 📋 Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] OpenAI API key obtained and billing enabled
- [ ] Environment variables configured (OPENAI_API_KEY required)
- [ ] Dockerfile ready for deployment
- [ ] Railway project created and deployed
- [ ] OpenAI API key added to Railway environment variables
- [ ] Application accessible via public URL
- [ ] RAG system working (test with electrical safety questions)
- [ ] AI responses functioning correctly

## 🔍 Troubleshooting

### Build Issues
- **Docker build fails**: Check Dockerfile syntax and base image availability
- **Pip install fails**: Check internet connectivity and Python package versions
- **Build timeout**: Railway has 15-minute build limit - optimize if needed

### Runtime Issues
- **OpenAI API errors**: Check API key validity and billing status at https://platform.openai.com/usage
- **RAG system empty**: Sources may not have indexed properly - check logs
- **Port binding issues**: Railway handles port assignment automatically
- **Application won't start**: Check Flask logs and environment variables

### Performance Issues
- **Slow OpenAI responses**: This is normal - GPT API has network latency
- **High API costs**: Monitor usage at https://platform.openai.com/usage
- **Rate limiting**: OpenAI has rate limits - implement retry logic if needed

## 📊 Resource Requirements

### Minimum Requirements (Railway Free Tier)
- **RAM**: 512MB (for web app only - no local models!)
- **CPU**: 0.5 cores
- **Storage**: 1GB
- **Bandwidth**: Minimal (OpenAI API calls)

### Recommended Requirements
- **RAM**: 1GB
- **CPU**: 1 core
- **Storage**: 5GB (for knowledge base)
- **Bandwidth**: Moderate (for OpenAI API calls)

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
