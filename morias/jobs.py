
from poorwsgi import *
from falias.sql import Sql

from os import waitpid,WNOHANG


from core.render import generate_page
from core.login import check_login, check_right, check_referer

from lib.menu import Item
from lib.pager import Pager
from lib.jobs import Job, clean_zombie

from admin import *

_check_conf = (
    ('morias', 'db', Sql),                      # database configuration
)

system_menu.append(Item('/admin/jobs', label="Background Jobs",
                         rights = ['super']))


@app.pre_process()
def jobs_clean_zombies(req):
    clean_zombie(req)

@app.route('/admin/jobs')
def admin_jobs(req):
    check_login(req)
    check_right(req, 'super')

    pager = Pager()
    pager.bind(req.args)

    rows = Job.list(req, pager)
    return generate_page(req, "admin/jobs.html", pager = pager, rows = rows)
#enddef

@app.route('/admin/jobs/<pid:int>/delete', state.METHOD_POST)
def admin_pages_del(req, pid):
    check_login(req, '/login?referer=/admin/jopbs')
    check_right(req, 'super')
    check_referer(req, '/admin/jobs')

    job = Job(pid = pid)
    job.delete(req)
    redirect(req, '/admin/jobs')
#enddef
