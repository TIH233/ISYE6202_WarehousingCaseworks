# Quick Start Guide - ISYE6202

## Repository Setup Complete

Your ISYE6202 repository has been initialized with the following structure:

```
ISYE6202/
├── case01/          # Integer Optimization Case Study
├── case02/          # Data Analysis Case Study
├── case03/          # Advanced Optimization Case Study
├── case04/          # Probabilistic Modeling Case Study
├── venv/            # Python virtual environment
├── requirements.txt # Python package dependencies
├── README.md        # Main documentation
└── .gitignore       # Git ignore rules
```

## GitHub Setup

To push this repository to GitHub, follow these steps:

### Option 1: Using the Setup Script (Recommended)

```bash
./setup_github.sh
```

This interactive script will guide you through creating the repository on GitHub.

### Option 2: Manual Setup

1. **Create GitHub Repository**
   - Go to https://github.com/new
   - Repository name: `ISYE6202_WarehousingCaseworks`
   - Description: `Warehousing and Probabilistic Models coursework`
   - Do NOT initialize with README, .gitignore, or license
   - Click "Create repository"

2. **Add Remote and Push**
   ```bash
   git remote add origin git@github.com:TIH233/ISYE6202_WarehousingCaseworks.git
   git push -u origin main
   ```

## Virtual Environment Setup

### Activate the environment:
```bash
source venv/bin/activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Deactivate when done:
```bash
deactivate
```

## Package Information

The `requirements.txt` includes:
- **PuLP** - Integer/Linear programming optimization
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation and analysis
- **openpyxl** - Excel file handling
- **SciPy** - Scientific computing
- **Matplotlib & Seaborn** - Visualization
- **Jupyter** - Interactive notebooks

## Working on Case Studies

Each case folder has its own README with specific instructions. Navigate to a case folder:

```bash
cd case01
```

Create subdirectories as needed:
```bash
mkdir -p data scripts notebooks results
```

## Git Workflow

### Check status:
```bash
git status
```

### Add and commit changes:
```bash
git add .
git commit -m "Your commit message"
```

### Push to GitHub:
```bash
git push
```

## GitHub Interface Features

The main [README.md](./README.md) includes clickable hyperlinks to each case folder for easy navigation on GitHub's web interface.

## Troubleshooting

### SSH Key Issues
Test SSH connection:
```bash
ssh -T git@github.com
```

### Virtual Environment Issues
If venv doesn't work, recreate it:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Contact

- **Name**: hty
- **Email**: thu317@gatech.edu
- **Course**: ISYE6202
