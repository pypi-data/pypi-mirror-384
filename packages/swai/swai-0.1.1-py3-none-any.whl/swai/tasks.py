import requests
import argparse
import os
import zipfile
import uuid
import shutil
import json
from datetime import datetime
from tabulate import tabulate
from swai.const import SWAI_API_URL, TASK_SUBMIT_ROUTE, TASK_LIST_ROUTE, TASK_CANCEL_ROUTE, TASK_DOWNLOAD_ROUTE, AVAILABLE_TASK_TYPES, CACHE_DIR
from swai.utils.log import logger

def clean_tmp(tmp_dir):
    if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)

def check_swdocking_task_input(task_input: str):
    tmp_dir = os.path.join(CACHE_DIR, "tmp-swai-submit", str(uuid.uuid4()))
    extract_dir = tmp_dir
    receptor_dir = os.path.join(extract_dir, "receptor_pdbqt")
    ligand_dir = os.path.join(extract_dir, "ligand_pdbqt")
    
    try:
        with zipfile.ZipFile(task_input, 'r') as zip_ref:
            os.makedirs(extract_dir, exist_ok=True)
            zip_ref.extractall(extract_dir)
            
    except Exception as e:
        clean_tmp(tmp_dir)
        return False, f"failed to unpack zip file: {str(e)}"
    
    if os.path.exists(receptor_dir) and os.path.exists(ligand_dir):
        flag = False
        for file in os.listdir(receptor_dir):
            if file.endswith('.pdbqt'):
                flag = True
                break
        if not flag:
            clean_tmp(tmp_dir)
            return False, f"directory `receptor_pdbqt/` in zip file cannot find any pdbqt file"
        flag = False
        for file in os.listdir(ligand_dir):
            if file.endswith('.pdbqt'):
                flag = True
                break
        if not flag:
            clean_tmp(tmp_dir)
            return False, f"directory `ligand_pdbqt/` in zip file cannot find any pdbqt file"
    else:
        clean_tmp(tmp_dir)
        return False, f"zip file should contain `receptor_pdbqt/` and `ligand_pdbqt/` directories"
    
    clean_tmp(tmp_dir)
    return True, "ok"

def check_swbind_task_input(task_input: str):
    tmp_dir = os.path.join(CACHE_DIR, "tmp-swai-submit", str(uuid.uuid4()))
    extract_dir = tmp_dir
    json_file = os.path.join(extract_dir, "input.json")
    try:
        with zipfile.ZipFile(task_input, 'r') as zip_ref:
            os.makedirs(extract_dir, exist_ok=True)
            zip_ref.extractall(extract_dir)
            
    except Exception as e:
        clean_tmp(tmp_dir)
        return False, f"failed to unpack zip file: {str(e)}"
    
    files = list(filter(lambda x: x.endswith('.json'), os.listdir(extract_dir)))
    if len(files) != 1:
        clean_tmp(tmp_dir)
        return False, f"zip file should contain ONE json file, but got {len(files)} files: {files}"

    json_file = os.path.join(extract_dir, files[0])
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        clean_tmp(tmp_dir)
        return False, f"json file is not valid"
        
    if 'entities' not in data:
        clean_tmp(tmp_dir)
        return False, f"json file should contain `entities` field"
    if len(data['entities']) == 0:
        clean_tmp(tmp_dir)
        return False, f"json file should contain at least ONE entity"
    for entity in data['entities']:
        if 'type' not in entity or 'count' not in entity:
            clean_tmp(tmp_dir)
            return False, f"entity should contain `type` and `count` fields"
        if entity['type'] not in {'protein', 'dna', 'rna', 'ligand'}:
            clean_tmp(tmp_dir)
            return False, f"entity type should be one of `protein`, `dna`, `rna`, `ligand`, but got {entity['type']}"
        if entity['count'] <= 0:
            clean_tmp(tmp_dir)
            return False, f"entity count should be greater than 0, but got {entity['count']}"
        if not "sequence" in entity and not "smiles" in entity and not "ccd" in entity:
            clean_tmp(tmp_dir)
            return False, f"entity should contain `sequence`, `smiles`, or `ccd` fields, but got {entity.keys()}"
    clean_tmp(tmp_dir)
    return True, "ok"

class TaskManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str, args: argparse.Namespace):
        self.api_key = api_key
        self.args = args
        self.check_funcs = {
            'swdocking': check_swdocking_task_input,
            'swbind': check_swbind_task_input,
        }

    
    def parse_datetime(self, datetime_str: str):
        # datetime_str: 2025-09-04T13:31:17.870551+08:00
        parsed_date = datetime.fromisoformat(datetime_str)
        return parsed_date.strftime("%Y-%m-%d %H:%M:%S")

    def submit_task(self, task_type: str, task_input: str, subscribe_email: bool, description: str):
        task_input = os.path.abspath(task_input)
        if task_type not in AVAILABLE_TASK_TYPES:
            logger.error(f"Invalid task type: {task_type}")
            return
        if not os.path.exists(task_input):
            logger.error(f"Task input file not found: {task_input}")
            return
        if not task_input.endswith('.zip'):
            logger.error(f"Task input file should be a zip file: {task_input}")
            return
        if len(description) == 0:
            logger.error(f"Description is required")
            return
        if len(description) > 140:
            logger.error(f"Description should be less than 140 characters")
            return
        if os.path.getsize(task_input) > 10 * 1024 * 1024:
            logger.error(f"Task input file should be less than 10MB: {task_input}")
            return

        logger.info(f"Start checking task input: {task_input}")
        flag, msg = self.check_funcs[task_type](task_input)
        if not flag:
            logger.error(f"Task input check failed: {msg}")
            return

        with open(task_input, 'rb') as f:
            files = {
                'file': (os.path.basename(task_input), f, 'application/zip')
            }
            try:
                r = requests.post(f"{SWAI_API_URL}{TASK_SUBMIT_ROUTE}", data={
                    "api_key": self.api_key,
                    "task_type": task_type,
                    "remark": description,
                    "subscribe_email": subscribe_email
                }, files=files)
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Submit task failed: Connection Failed, please check your network")
                return
        # # r.raise_for_status()
        resp = r.json()
        if resp['msg'] == 'accepted':
            logger.info(f"Task submitted successfully, response:\n{resp}")
        else:
            logger.error(f"Task submission failed: response:\n{resp}")

    # def get_task(self, task_id: str):
    #     pass

    def list_tasks(self, status: str = None, task_id: str = None, task_type: str = None, limit: int = 50):
        if status not in {'queued', 'running', 'done', 'failed', 'cancelled', 'all'}:
            logger.error(f"Invalid argument: {status=}")
            return
        status = "queued,running,done,failed,cancelled" if status == 'all' else status
        if task_type not in {'swbind', 'swdocking', 'all'}:
            logger.error(f"Invalid argument: {task_type=}")
            return
        task_type = None if task_type == 'all' else task_type
        if limit <= 0:
            logger.error(f"Invalid argument: {limit=}")
            return
        if task_id is not None and not isinstance(task_id, str):
            logger.error(f"Invalid argument: {task_id=}")
            return
        
        data = {
            "api_key": self.api_key,
            "status": status,
            "task_id": task_id,
            "type": task_type,
            "limit": limit
        }
        res = []
        columns = ['task_id', 'type', 'status', 'progress', 'last_update', 'submit_time', 'subscribe_email']
        
        try:
            r = requests.get(f"{SWAI_API_URL}{TASK_LIST_ROUTE}", json=data)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"List tasks failed: Connection Failed, please check your network")
            return
        resp = r.json()
        for idx, task in enumerate(resp):
            show_task = []
            for col in columns:
                if col in {'last_update', 'submit_time'}:
                    task[col] = self.parse_datetime(task[col])
                show_task.append(task[col])
            res.append(show_task)
        logger.info("\n" + tabulate(res, headers=columns, tablefmt="grid"))
        

    def cancel_task(self, task_id: str):
        if not task_id.startswith('swbind') and not task_id.startswith('swdocking'):
            logger.error(f"Invalid task id: {task_id}")
            return

        data = {"api_key": self.api_key}
        try:
            r = requests.post(f"{SWAI_API_URL}{TASK_CANCEL_ROUTE.format(task_id=task_id)}", json=data)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cancel task failed: Connection Failed, please check your network")
            return
        resp = r.json()
        if resp['status'] == 'error':
            logger.error(f"Cancel task failed: {resp['msg']}")
        else:
            logger.info(f"Task {task_id} cancelled successfully")
        
    def download_task(self, task_id: str, output: str = None):
        if not task_id.startswith('swbind') and not task_id.startswith('swdocking'):
            logger.error(f"Invalid task id: {task_id}")
            return
        if output is None:
            output = f"{task_id}.zip"
        elif not output.endswith('.zip'):
            logger.error(f"output file path should end with .zip: {output}")
            return
        output = os.path.abspath(output)

        data = {"api_key": self.api_key}
        try:
            resp = requests.get(f"{SWAI_API_URL}{TASK_DOWNLOAD_ROUTE.format(task_id=task_id)}", params=data)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Download task failed: Connection Failed, please check your network")
            return

        if resp.status_code != 200:
            logger.error(f"Download task failed, error code={resp.status_code}")
            return
        
        with open(output, "wb") as f:
            f.write(resp.content)
        logger.info(f"Task result downloaded successfully: {output}")
        