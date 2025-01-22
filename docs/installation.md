# LabMonitor
LabMonitor, a Python application designed to simplify the management of computing resources in decentralized networks of Linux machines.


## Prerequisites

Ensure you have the following installed on your system:
- [Python 3.8+](https://www.python.org/downloads/)
- [Conda Package Manager](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- Git (for cloning the repository)

## Installation Guide

### Step 1: Clone the Repository
Use Git to clone the repository to your local machine:
```bash
git clone https://github.com/anchieta-oliveira/LabMonitor.git
cd LabMonitor
```

### Step 1.1: Clone the Repository
Create a new Conda environment using the provided requirements.txt file:
```bash
conda create --name labmonitor --file requirements.txt
conda activate labmonitor
```

### Start LabMonitor:
```bash
python3.10 main.py --help
```