#!/usr/bin/python
import json
import sys
import sqlite3


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: %s database.db" % sys.argv[0]
        sys.exit(1)

    with sqlite3.connect(sys.argv[1]) as conn:
        cr = conn.cursor()
        cw = conn.cursor()
        cr.execute("SELECT attachment_id, data FROM attachments");
        for id, data in cr:
            raw = json.loads(data)
            md5 = raw.pop('md5')
            cw.execute("UPDATE attachments SET "
                        "md5 = '%s', data = '%s' WHERE attachment_id = %d" % \
                    (md5, json.dumps(raw), int(id)))
