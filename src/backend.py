import time
import csv


ONLINE = False

RECORDS_PATH = './data/collections.csv'
BACKLOG_PATH = './data/backlog.csv'

VALID_BOX_IDS = []
VALID_CUP_IDS = ['8295f584-f45d-490c-5466-2654a546', '8288f584-dd6f-490c-8137-2b85f49ff488']


def check_container(container):
    c_type = container.get('type', 'error')
    c_id = container.get('id', 'error')
    
    if not ONLINE:
        # Basic checks against locally known ids (temporary)
        if c_type == 'box':
            return (c_id in VALID_BOX_IDS)
        elif c_type == 'cup':
            return (c_id in VALID_CUP_IDS)
    
    else:
        # Send validity request to Cauli API
        pass

    return False


def record_collection(container, status):

    c_type = container.get('type', 'error')
    c_id = container.get('id', 'error')
    timestamp = time.time()

    # Append to collection records
    with open(RECORDS_PATH, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, c_type, c_id, status])
        f.close()

    return (c_type != 'error' and c_id != 'error')


def send_collection_confirmation(container):

    c_type = container.get('type', 'error')
    c_id = container.get('id', 'error')
    timestamp = time.time()

    if not ONLINE:
        # Append to collection backlog (to be sent later)
        with open(BACKLOG_PATH, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, c_type, c_id])
            f.close()
    
    else:
        # 1. Send to Cauli API
        # 2. Send all pending collections in backlog
        # 3. Empty backlog
        # If something fails, put everything back in backlog
        pass

    return (c_type != 'error' and c_id != 'error')