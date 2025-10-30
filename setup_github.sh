#!/bin/bash

# GitHub Repository Setup Script
# This script will help you create and push to GitHub

echo "======================================="
echo "ISYE6202 GitHub Repository Setup"
echo "======================================="
echo ""

# Step 1: Create repository on GitHub
echo "Step 1: Create GitHub Repository"
echo "--------------------------------"
echo "Please go to: https://github.com/new"
echo ""
echo "Repository settings:"
echo "  - Repository name: ISYE6202_WarehousingCaseworks"
echo "  - Description: Warehousing and Probabilistic Models coursework"
echo "  - Visibility: Public or Private (your choice)"
echo "  - DO NOT initialize with README, .gitignore, or license"
echo ""
read -p "Press Enter after you've created the repository on GitHub..."

# Step 2: Add remote and push
echo ""
echo "Step 2: Adding remote and pushing to GitHub"
echo "-------------------------------------------"

# Assuming GitHub username is TIH233 based on SSH test
GITHUB_USERNAME="TIH233"
REPO_NAME="ISYE6202_WarehousingCaseworks"

echo "Using GitHub username: $GITHUB_USERNAME"
echo "Using repository name: $REPO_NAME"
echo ""

# Add remote
echo "Adding remote origin..."
git remote add origin "git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "======================================="
echo "Setup Complete!"
echo "======================================="
echo ""
echo "Your repository should now be available at:"
echo "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "Repository structure:"
echo "  - case01/ - Integer Optimization Case Study"
echo "  - case02/ - Data Analysis Case Study"
echo "  - case03/ - Advanced Optimization Case Study"
echo "  - case04/ - Probabilistic Modeling Case Study"
echo "  - venv/ - Python virtual environment"
echo "  - requirements.txt - Python dependencies"
echo "  - README.md - Main documentation with hyperlinks"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Start working on case studies!"
