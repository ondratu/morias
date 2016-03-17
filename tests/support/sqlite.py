from logging import error


def sql_script(c, sql_path, sql_script):
    with open(sql_path+'/'+sql_script) as f:
        error('SQL << %s' % f.name)
        c.executescript(f.read())
