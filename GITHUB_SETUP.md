# GitHub Setup Instructions

## Step 1: Delete Old Repository (if exists)

1. Go to: https://github.com/bullishonyou/knox-wallet-nock
2. Click **Settings** (gear icon in top right)
3. Scroll to **"Danger Zone"**
4. Click **"Delete this repository"**
5. Type the repository name to confirm
6. Click **Delete**

## Step 2: Verify Git is Clean

```bash
# Check status
git status

# If there are untracked files, they'll be listed
# The .gitignore is now configured to exclude:
# - QUICKSTART.md
# - PROJECT_SUMMARY.md
# - INDEX.md
# - SETUP_COMPLETE.txt
# - balances/
# - notes-*.csv
# - *.log
```

## Step 3: Add and Commit Everything

```bash
# Add all files
git add .

# Commit
git commit -m "Initial commit: KNOX - Nockchain web wallet

- Create and import wallets
- Check balance and transaction history
- Send transactions
- Modern dark theme UI
- Complete documentation"
```

## Step 4: Create New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `knox-wallet-nock`
3. Description: "A modern web-based wallet for Nockchain"
4. Choose: **Public**
5. Do NOT initialize with README (we have one)
6. Click **Create repository**

## Step 5: Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/bullishonyou/knox-wallet-nock.git

# Push
git branch -M main
git push -u origin main
```

That's it! Your clean repository is now on GitHub.
