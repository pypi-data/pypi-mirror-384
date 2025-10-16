import os
from swai.data_precess.swdocking import SWDocking
from swai.data_precess.swbind import SWBind
from swai.utils.log import logger

def process_data(args):
    task_type = args.task_type
    output_dir = os.path.abspath(args.output_dir)
    is_exist = os.path.exists(output_dir)
    if is_exist:
        logger.error(f"output_dir {output_dir} already exists")
        exit(1)
    if task_type == "swdocking":
        swdocking = SWDocking(args.receptor_dir, args.ligand_dir, output_dir, args.ligand_format)
        zip_path = swdocking.process()
        logger.info(f"data processing finished")
        logger.info(f"` swai submit -t swdocking -i {zip_path} -d \"task description\" ` to submit task")

    elif task_type == "swbind":
        swbind = SWBind(args.input_json, output_dir)
        zip_path = swbind.process()
        logger.info(f"data processing finished")
        logger.info(f"` swai submit -t swbind -i {zip_path} -d \"task description\" ` to submit task")
    else:
        logger.error(f"invalid task type: {task_type}")
        exit(1)