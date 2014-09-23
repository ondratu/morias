var M = M || {};

M.locales = {};

M._ = function(orig){
    if (orig in M.locales)
        return M.locales[orig];
    console.error("Missing '" + orig+"' locale");
    return orig;
}
