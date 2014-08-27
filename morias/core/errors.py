from poorwsgi import *

from render import generate_page

BAD_LOGIN       = 1000
ACCESS_DENIED   = 1001
NOT_FOUND       = 1002

SUCCESS         = 2000

@app.http_state(state.HTTP_NOT_FOUND)
def not_found(req):
    req.state = state.HTTP_NOT_FOUND
    req.write(generate_page(req, "error/not_found.html",
        request_uri = req.environ['REQUEST_URI']))
    return state.DONE


@app.http_state(state.HTTP_PRECONDITION_FAILED)
def precondition_failed(req):
    req.state = state.HTTP_PRECONDITION_FAILED
    req.write(generate_page(req, "error/precondition_failed.html",
        precondition = req.precondition))
    return state.DONE
