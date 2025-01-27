    <div style="text-align: center;">
        <h1>Tutorial</h1>
    </div>

## Prerequisites
Ensure you have the following installed on your system:
- [Python 3.8+](https://www.python.org/downloads/)
- [Conda Package Manager](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- (Optional) Git - for cloning the repository

## Installation Guide "
""
### Step 1: Clone the Repository
Use Git to clone the repository to your local machine:
```bash
git clone https://github.com/anchieta-oliveira/LabMonitor.git
```
### Step 2: Create a virtual environment dedicated to LabMonitor
Navigate to the cloned Git folder:
```bash
cd LabMonitor
```
Create a new Conda environment using the provided requirements.txt file:
```bash
conda create --name labmonitor --file requirements.txt
```

## Usage Guide 

### Step 1: Navigate to LabMonitor folder:
```bash
cd path/to/LabMonitor/file/
```
### Step 2: Fill in the .csv tables in /LabMonitor folder:
- Start with \"machines.csv\" which is essential for the functioning of te dashboard.
- (Optional) fill in \"machines_job.csv\" with the information of machines you want to be avaiable for recruitment to perform tasks/to be included in the task queue.

We recommend including sudo users to the \"machines_job.csv\", so every user can be accessed.
- (Optional) fill in \"users.csv\" to be able to restrict the number of tasks or ammount of resources a single person can request.
### Optional Step: Fill in the email.json file
This email will serve as a virtual assistant, sending users notifications regarding machine availability, as well as the start and completion of tasks.
### Step 3: Activate the LabMonitor dedicated environment:
```bash
conda activate labmonitor
```
### Step 4: Call LabMonitor
You can either request LabMonitor to activate all or a subset of its functionalities:

Displaying LabMonitor usage options:
```bash
python3.10 main.py --help
```
Starting the dashboard (Most basic usage:)
```bash
python3.10 main.py -s
```
Starting the dashboard and enabling all of LabMonitor utilities:
```bash
python3.10 main.py -s -sh -sq -sqj
```
Whatever the case may be, we recommend running the command in the background:
```bash
nohup python3.10 main.py -s -sh -sq -sqj &
```