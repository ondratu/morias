
from random import seed, randint
from gettext import gettext as _

from errors import ErrorValue


robot_questions = []
seed()

# generate simple math questions
pm = ['+', '-', '*']
for i in xrange(0, 100):
    expression = '%s %s %s' % (randint(0, 10), pm[i % 3], randint(0, 10))
    question = _('Calculate the expression %s.') % expression
    answer = str(eval(expression))
    robot_questions.append((question, answer))
# endfor


class RobotError(ErrorValue):
    code = 403
    reason = 'robot_error'
    message = 'Robot detected from form'
