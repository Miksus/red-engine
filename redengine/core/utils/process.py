from multiprocessing import current_process

def is_main_subprocess():
    return current_process().name == 'MainProcess'