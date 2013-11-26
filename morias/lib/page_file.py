
import json

class Page():
    def __init__(self, id = None):
        self.id = id

    def get(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT name, editor_rights "
                    "FROM page WHERE page_id = %s", self.id)
        self.name, rights = c.fetchone()
        self.rights = json.loads(rights)
        tran.commit()

        with open (req.cfg.pages_source + '/' + self.name, 'r') as f:
            self.text = f.read()
    #enddef

    def add(self, req):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("INSERT INTO page (name, editor_rights, text) "
                    "VALUES ( %s, %s, %s)",
                    (self.name, json.dumps(self.rights), self.text))
        tran.commit()

    @staticmethod
    def list(req, pager):
        tran = req.db.transaction(req.logger)
        c = tran.cursor()
        c.execute("SELECT page_id, name, editor_rights "
                    "FROM page ORDER BY name LIMIT %s, %s",
                    (pager.offset, pager.limit))
        items = []
        row = c.fetchone()
        while row is not None:
            page = Page(row[0])
            page.name = row[1]
            page.rights = row[2]
            row = c.fetchone()
        #endwhile

        c.execute("SELECT count(*) FROM page")
        pager.total = c.fetchone()[0]
        tran.commit()

        return items
    #enddef
#endclass
