"""An asynchronous drop-in replacement for the Dash Class that uses Quart.

Quart is a Flask-API compatible web framework that is based on asyncio, which
means it's faster at processing IO bound requests than apparently even gunicorn
with async workers.

This is a proof of concept that shows we can switch out Flask and use Quart with
Dash.

https://gitlab.com/pgjones/quart


To use as drop in replacement for the Dash class do the following:

    $ pip install quart
 
Then just use like the Dash class:

    app = DashAsync()

or:
    from quart import Quart

    server = Quart(__name__)
    app = DashAsync(__name__, server=server)


Quart is faster that Flask out of the box, but to really get speedups you should
use gunicorn with uvloop worker classes like so:

    $ pip install gunicorn uvloop
    $ gunicorn --worker-class quart.worker.GunicornUVLoopWorker app:app.server

"""




import quart
from quart import Quart

from . import dash


# monkey patch the Flask functions used in the dash module with the equivalent
# from quart
dash.jsonify = quart.jsonify
dash.Response = quart.Response


class DashAsync(dash.Dash):
    """Dash subclass that uses Quart Instead of Flask"""

    def __init__(self, name=None, server=None, static_folder=None, **kwargs):
        name = name or 'dash'
        server = server or Quart(name, static_folder=static_folder)
        super().__init__(
            name=name,
            server=server,
            static_folder=static_folder,
            compress=True,
            **kwargs
        )

    async def dispatch(self):
        body = await quart.request.get_json()
        inputs = body.get('inputs', [])
        state = body.get('state', [])
        output = body['output']

        target_id = '{}.{}'.format(output['id'], output['property'])
        args = []
        for component_registration in self.callback_map[target_id]['inputs']:
            args.append([
                c.get('value', None) for c in inputs if
                c['property'] == component_registration['property'] and
                c['id'] == component_registration['id']
            ][0])

        for component_registration in self.callback_map[target_id]['state']:
            args.append([
                c.get('value', None) for c in state if
                c['property'] == component_registration['property'] and
                c['id'] == component_registration['id']
            ][0])

        return self.callback_map[target_id]['callback'](*args)
