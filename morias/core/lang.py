

def get_langs(req):
    if 'Accept-Language' in req.subprocess_env:
        alangs = req.subprocess_env['Accept-Language']
        # Accept-Language	:cs,en-us;q=0.7,en;q=0.3
        alangs = map(lambda s: s.split(';')[0], alang.split(','))
        alangs = list( k for k in alang if k in req.cfg.langs)
        return alangs if len(alangs) else req.cfg.langs
    else:
        return req.cfg.langs
#enddef


def get_lang(req):
    return get_langs(req)[0]
#enddef

