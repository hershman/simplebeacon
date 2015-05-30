from functools import update_wrapper
import time

from flask import *

''' Note: decorator returning a decorator returning wrapped function '''
def require_session(redirect_handler):
    def decorator(func):
        def wrapped(*args, **kwargs):
            if 'id' not in session or 'id_expiry' not in session:
                return redirect(url_for(redirect_handler))
            if session['id_expiry'] < int(time.time()):
                session.clear()
                return redirect(url_for(redirect_handler))
            return make_response(func(*args, **kwargs))
        return update_wrapper(wrapped, func)
    return decorator
