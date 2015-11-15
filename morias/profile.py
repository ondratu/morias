import cProfile

app = None  # only for pep8 checker
cProfile.runctx('from main import *', globals(), locals(),
                filename="log/init.profile")
app.set_profile(cProfile.runctx, 'log/req')
