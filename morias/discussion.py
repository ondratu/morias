from poorwsgi import app
from falias.util import uni

app.set_filter('comment_id', r'[0-9\.]+', uni)

right_moderator = 'discussion_moderator'
