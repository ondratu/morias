import cProfile

cProfile.runctx('from core.config import *', globals(), locals(), filename="log/init.profile")

app.set_profile(cProfile.runctx, 'log/req')
