import quart
from quart import Quart

from . import dash


# monkey patch the Flask functions used in the dash module with the equivalent
# from quart
dash.jsonify = quart.jsonify
dash.Response = quart.Response


class DashAsync(dash.Dash):
    """Dash subclass that uses Quart Instead of Flask"""

    # should hopefully work as a drop in replacement for the Dash class
    
    def __init__(self, name=None, server=None, static_folder=None, **kwargs):
        name = name or 'dash'
        server = server or Quart(name, static_folder=static_folder)
        super().__init__(
            name=name,
            server=server,
            static_folder=static_folder,
            compress=False,
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
