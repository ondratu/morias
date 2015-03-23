var M = M || {};

M.locales = M.locales || {};

M._ = function(orig){
    if (orig in M.locales)
        return M.locales[orig];
    console.warn("Missing '" + orig+"' locale");
    return orig;
}
