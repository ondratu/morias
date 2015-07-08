

def get_langs(req):
    if 'Accept-Language' in req.headers_in:
        alangs = req.headers_in['Accept-Language']
        # Accept-Language	:cs,en-us;q=0.7,en;q=0.3
        alangs = map(lambda s: s.split(';')[0], alangs.split(','))
        alangs = tuple( k for k in alangs if k in req.cfg.langs)
        return alangs if len(alangs) else req.cfg.langs
    else:
        return req.cfg.langs
#enddef


def get_lang(req):
    return get_langs(req)[0]
#enddef

