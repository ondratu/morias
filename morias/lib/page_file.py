
class Page():
    def __init__(self, id = None):
        self.id = id

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
