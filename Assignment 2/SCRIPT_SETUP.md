## Script Setup

### Setup and use the Python VENV


- Create the virtual environment
```bash
python3 -m venv venv
```
- Activate the virtual environment

```bash
source venv/bin/activate
```
- Install dependencies from the `requirements.txt` file

```bash
pip install -r requirements.txt 
```

Run the script and choose from the following options:

- Create resources on Catalyst Cloud

```bash
python3 assignment2.py create
```

- Run the created Catalyst Cloud servers

```bash
python3 assignment2.py run
```

- Obtain the status of the servers

```bash
python3 assignment2.py status
```

- Stop the servers

```bash
python3 assignment2.py stop
```

- Destroy all created resources

```bash
python3 assignment2.py destroy
```