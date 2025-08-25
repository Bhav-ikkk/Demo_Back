# 🚀 Quick Start - Deploy Your Backend

## 🎯 Choose Your Deployment Method

### Option 1: Local Development (Recommended for testing)
```bash
# 1. Copy environment file
Copy-Item env.example .env

# 2. Edit .env with your Google API key
notepad .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python run_local.py
```

### Option 2: Production with Docker
```bash
# 1. Copy production environment
Copy-Item env.prod.example .env.prod

# 2. Edit .env.prod with your values
notepad .env.prod

# 3. Deploy with PowerShell script
.\deploy.ps1
```

## 🔑 Required Configuration

**You MUST set these in your environment file:**
- `GOOGLE_API_KEY` - Your Google Gemini AI API key

## 🌐 Frontend Integration

Once deployed, your backend will be available at:
- **Local**: http://localhost:8000
- **Production**: Your server IP/domain

Update your frontend to use this backend URL!

## 🧪 Test Your Deployment

```bash
# Test if everything is working
python test_deployment.py

# Or test manually
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## 📚 Full Documentation

- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **API Documentation**: http://localhost:8000/docs (when running)

## 🆘 Need Help?

1. Check the logs for error messages
2. Verify your Google API key is correct
3. Ensure ports 8000, 5432, 6379 are available
4. Run the test script to diagnose issues

---

**🎉 Your AI Product Council Backend is ready to power amazing AI-driven product development!**
