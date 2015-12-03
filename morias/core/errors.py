from poorwsgi import app, state

from traceback import format_exc

from render import generate_page

BAD_LOGIN = 1000
ACCESS_DENIED = 1001
NOT_FOUND = 1002
SUCCESS = 2000


@app.http_state(state.HTTP_FORBIDDEN)
def forbidden(req):
    req.state = state.HTTP_FORBIDDEN
    req.write(generate_page(req, "error/forbidden.html",
                            request_uri=req.environ['REQUEST_URI']))
    return state.DONE


@app.http_state(state.HTTP_NOT_FOUND)
def not_found(req):
    req.state = state.HTTP_NOT_FOUND
    req.write(generate_page(req, "error/not_found.html",
                            request_uri=req.environ['REQUEST_URI']))
    return state.DONE


@app.http_state(state.HTTP_PRECONDITION_FAILED)
def precondition_failed(req):
    req.state = state.HTTP_PRECONDITION_FAILED
    req.write(generate_page(req, "error/precondition_failed.html",
                            precondition=req.precondition))
    return state.DONE


@app.http_state(state.HTTP_INTERNAL_SERVER_ERROR)
def internal_server_error(req):
    traceback = format_exc()
    traceback = ''.join(traceback)
    req.log_error(traceback, state.LOG_ERR)

    req.state = state.HTTP_PRECONDITION_FAILED
    req.write(generate_page(req, "error/internal_server_error.html",
                            traceback=traceback.split('\n')))
    return state.DONE
