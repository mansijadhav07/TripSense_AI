# 🚀 GitHub Push Commands

## Step-by-Step Guide to Push TripSense-AI to GitHub

### 1. Create a New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `TripSense-AI`
3. Description: `AI-Powered Hotel Recommendation System with Apache Spark and Next.js`
4. Choose: **Public** or **Private**
5. ⚠️ **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **"Create repository"**

---

### 2. Prepare Your Local Repository

```bash
# Navigate to project directory
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# Check current git status
git status

# Add all files to staging
git add .

# Commit all changes
git commit -m "Initial commit: Complete TripSense-AI hotel recommendation system

- FastAPI backend with JWT authentication
- Next.js 16 frontend with TypeScript
- 4 ML models: Collaborative, Content-Based, Hybrid, Popularity
- Apache Spark data pipeline (50,780 hotels, 201K reviews)
- Real-time recommendation engine
- Advanced filters and aspect weight tuning
- Analytics dashboard
- Production-ready with comprehensive documentation"
```

---

### 3. Link to GitHub Remote

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/TripSense-AI.git

# Verify remote was added
git remote -v
```

---

### 4. Push to GitHub

```bash
# Push to main branch
git push -u origin main
```

**If you get an error about "main" vs "master":**
```bash
# Rename branch to main (if needed)
git branch -M main

# Then push
git push -u origin main
```

---

### 5. Verify on GitHub

1. Visit: `https://github.com/YOUR_USERNAME/TripSense-AI`
2. Check that all files are uploaded
3. Verify README.md displays correctly
4. Check that .gitignore is working (no .env, *.db, node_modules)

---

## 🔄 Future Updates

After making changes, use these commands:

```bash
# Check what changed
git status

# Add specific files
git add file1.py file2.tsx

# Or add all changes
git add .

# Commit with descriptive message
git commit -m "Add new feature: XYZ"

# Push to GitHub
git push
```

---

## 🌿 Working with Branches

### Create a new feature branch:
```bash
# Create and switch to new branch
git checkout -b feature/new-feature

# Make your changes...
git add .
git commit -m "Implement new feature"

# Push branch to GitHub
git push -u origin feature/new-feature
```

### Create a Pull Request:
1. Go to your repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select your feature branch
4. Add description and create PR

---

## 🏷️ Creating Releases

### Tag a version:
```bash
# Create a tag
git tag -a v1.0.0 -m "Release version 1.0.0 - Production ready"

# Push tag to GitHub
git push origin v1.0.0
```

### Create Release on GitHub:
1. Go to repository → "Releases"
2. Click "Create a new release"
3. Select your tag (v1.0.0)
4. Add release notes
5. Publish release

---

## 🔐 Authentication

### If prompted for credentials:

**Option 1: Personal Access Token (Recommended)**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use token as password when pushing

**Option 2: SSH Keys**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote URL to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/TripSense-AI.git
```

---

## ⚠️ Important Notes

### Before Pushing, Verify:

```bash
# Check .env is not tracked
git status | grep .env
# Should show nothing (it's in .gitignore)

# Check database is not tracked
git status | grep "\.db"
# Should show nothing

# Check node_modules is not tracked
git status | grep node_modules
# Should show nothing
```

### If .env or sensitive files appear:

```bash
# Remove from tracking (keeps local file)
git rm --cached .env
git rm --cached apps/api/tripsense.db

# Commit the removal
git commit -m "Remove sensitive files from tracking"
```

---

## 📋 Complete Command Sequence

Copy and paste this entire sequence (update YOUR_USERNAME):

```bash
# 1. Navigate to project
cd /Users/mansijadhav/Documents/BigData/TripSense-AI

# 2. Check status
git status

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit: Complete TripSense-AI system"

# 5. Add remote (REPLACE YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/TripSense-AI.git

# 6. Rename branch to main (if needed)
git branch -M main

# 7. Push to GitHub
git push -u origin main
```

---

## ✅ Success Indicators

After successful push, you should see:

```
Enumerating objects: XXX, done.
Counting objects: 100% (XXX/XXX), done.
Delta compression using up to X threads
Compressing objects: 100% (XXX/XXX), done.
Writing objects: 100% (XXX/XXX), X.XX MiB | X.XX MiB/s, done.
Total XXX (delta XXX), reused XXX (delta XXX)
To https://github.com/YOUR_USERNAME/TripSense-AI.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 🎉 You're Done!

Your repository is now on GitHub! Share the link:
```
https://github.com/YOUR_USERNAME/TripSense-AI
```

---

## 📞 Troubleshooting

### "Repository not found"
- Check your username is correct
- Verify repository exists on GitHub
- Check you have write access

### "Authentication failed"
- Use Personal Access Token instead of password
- Or set up SSH keys

### "Remote already exists"
```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR_USERNAME/TripSense-AI.git
```

### Large files error
```bash
# Check file sizes
find . -type f -size +50M

# If you have large files, add to .gitignore:
echo "data/raw/*.csv" >> .gitignore
```
