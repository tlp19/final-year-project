VALID_BOX_IDS = []
VALID_CUP_IDS = ['8295f584-f45d-490c-5466-2654a546', '8288f584-dd6f-490c-8137-2b85f49ff488']


def check_container(container):
    type = container.get('type', 'error')
    id = container.get('id', 'error')
    
    if type == 'box':
        return (id in VALID_BOX_IDS)
    elif type == 'cup':
        return (id in VALID_CUP_IDS)
    