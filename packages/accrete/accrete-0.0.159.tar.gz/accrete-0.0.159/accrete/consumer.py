from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer

from accrete.tenant import get_tenant


class WebsocketTenantConsumer(WebsocketConsumer):
    
    def websocket_connect(self, message):
        tenant = get_tenant()
        if tenant is None:
            raise ValueError('Tenant must be set.')
        super().websocket_connect(message)


class JsonWebsocketTenantConsumer(JsonWebsocketConsumer):

    pass

