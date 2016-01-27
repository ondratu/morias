from poorwsgi import app, state

from traceback import format_exc

from render import generate_page

BAD_LOGIN = 1000
ACCESS_DENIED = 1001
NOT_FOUND = 1002
SUCCESS = 2000


@app.http_state(state.HTTP_FORBIDDEN, state.METHOD_ALL)
def forbidden(req):
    req.status = state.HTTP_FORBIDDEN
    req.write(generate_page(req, "error/forbidden.html",
                            request_uri=req.environ['REQUEST_URI']))
    return state.DONE


@app.http_state(state.HTTP_NOT_FOUND, state.METHOD_ALL)
def not_found(req):
    req.status = state.HTTP_NOT_FOUND
    req.write(generate_page(req, "error/not_found.html",
                            request_uri=req.environ['REQUEST_URI']))
    return state.DONE


@app.http_state(state.HTTP_PRECONDITION_FAILED, state.METHOD_ALL)
def precondition_failed(req):
    req.status = state.HTTP_PRECONDITION_FAILED
    req.write(generate_page(req, "error/precondition_failed.html",
                            precondition=req.precondition))
    return state.DONE


@app.http_state(state.HTTP_INTERNAL_SERVER_ERROR, state.METHOD_ALL)
def internal_server_error(req):
    traceback = format_exc()
    traceback = ''.join(traceback)
    req.log_error(traceback, state.LOG_ERR)

    req.status = state.HTTP_INTERNAL_SERVER_ERROR
    req.write(generate_page(req, "error/internal_server_error.html",
                            traceback=traceback.split('\n')))
    return state.DONE
