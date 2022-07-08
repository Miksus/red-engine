
import pickle

def is_pickleable(obj):
    try:
        pickle.dumps(obj)
    except:
        return False
    else:
        return True