# ☁️ AmpAI Cloud Setup Guide

This guide will help you set up AmpAI as a completely cloud-based system with **zero local dependencies**.

## 🌟 Cloud Architecture

- **Web App**: Railway (cloud hosting)
- **Vector Database**: Pinecone (cloud vector database)
- **AI Model**: OpenAI GPT-4 (cloud API)
- **Source Files**: GitHub (cloud storage)
- **No Local Storage**: Everything runs in the cloud

## 📋 Prerequisites

1. **GitHub Account** (for code repository)
2. **Railway Account** (for web hosting) - [railway.app](https://railway.app)
3. **OpenAI Account** (for AI models) - [platform.openai.com](https://platform.openai.com)
4. **Pinecone Account** (for vector database) - [pinecone.io](https://pinecone.io)

## 🚀 Step 1: Set Up Pinecone (Vector Database)

1. Go to [pinecone.io](https://pinecone.io) and create a free account
2. Create a new project
3. Go to **API Keys** and copy your API key
4. Save this key - you'll need it for Railway: `PINECONE_API_KEY`

**Free Tier**: 1 index, 5M vectors, perfect for this project!

## 🔑 Step 2: Set Up OpenAI API

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account and add billing information
3. Go to **API Keys** and create a new key
4. Save this key - you'll need it for Railway: `OPENAI_API_KEY`

## 🚂 Step 3: Deploy to Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your AmpAI repository
4. Railway will automatically detect the configuration

### Environment Variables in Railway

Go to your Railway project → **Variables** tab and add:

```bash
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
PINECONE_API_KEY=YOUR_PINECONE_KEY_HERE
SECRET_KEY=your-random-secret-key-here
```

**Important**: Replace the values with your actual API keys!

## 🔄 Step 4: Automatic Deployment

Railway will automatically:
1. ✅ Build the Docker container
2. ✅ Install cloud dependencies (Pinecone, OpenAI)
3. ✅ Start the cloud web application
4. ✅ Load source documents from GitHub
5. ✅ Initialize Pinecone vector database
6. ✅ Provide a public URL

## 🌐 Step 5: Access Your Cloud App

Once deployed, Railway will provide a URL like:
`https://your-app-name.railway.app`

The system will:
- ✅ Load immediately (no local dependencies)
- ✅ Auto-populate knowledge base from GitHub
- ✅ Work from any device, anywhere
- ✅ Scale automatically with Railway

## 📊 Cloud Benefits

### ✅ What You Get:
- **Zero Local Dependencies**: Nothing stored on your computer
- **Global Access**: Works from any device, anywhere
- **Auto-Scaling**: Railway handles traffic automatically
- **Auto-Updates**: Push to GitHub = automatic deployment
- **Persistent Storage**: Pinecone keeps your data safe
- **High Availability**: Cloud infrastructure reliability

### 🚫 What You Don't Need:
- ❌ Local Python installation
- ❌ Local database files
- ❌ Local model downloads
- ❌ Local file storage
- ❌ Manual server management
- ❌ Local environment setup

## 🔧 How It Works

1. **Source Loading**: Documents loaded from GitHub repository
2. **Vector Database**: Pinecone stores embeddings in the cloud
3. **AI Processing**: OpenAI GPT-4 handles all AI tasks
4. **Web Interface**: Railway serves the web application
5. **Global CDN**: Fast access from anywhere in the world

## 💰 Cost Breakdown (Monthly)

- **Railway**: $0 (Hobby tier) or $5/month (Pro)
- **Pinecone**: $0 (Free tier with 5M vectors)
- **OpenAI**: Pay-per-use (~$10-50/month depending on usage)
- **GitHub**: $0 (public repository)

**Total**: ~$10-60/month for a fully managed, scalable system

## 🔄 Updates and Maintenance

To update your cloud application:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Railway automatically redeploys! No manual server management needed.

## 🆘 Troubleshooting

### Common Issues:

1. **"Pinecone API key not set"**
   - Check Railway environment variables
   - Ensure `PINECONE_API_KEY` is set correctly

2. **"OpenAI API error"**
   - Check your OpenAI API key in Railway
   - Ensure you have billing enabled on OpenAI

3. **"Application won't start"**
   - Check Railway build logs
   - Verify all environment variables are set

4. **"No documents in database"**
   - The system auto-loads from GitHub
   - Check that source files exist in your repository

## 🎯 Success Indicators

When everything is working:
- ✅ Railway shows "Deployed" status
- ✅ Your public URL loads the chat interface
- ✅ Pinecone dashboard shows your index with documents
- ✅ Chat responds with electrical safety knowledge
- ✅ No local files or processes needed

## 🌟 Cloud Advantages

- **Device Independence**: Access from phone, tablet, laptop
- **Team Collaboration**: Share one URL with your team
- **Automatic Backups**: Cloud providers handle data safety
- **Professional URLs**: Custom domains available
- **SSL/HTTPS**: Automatic security certificates
- **Global Performance**: CDN acceleration worldwide

Your AmpAI system is now 100% cloud-native! 🎉
