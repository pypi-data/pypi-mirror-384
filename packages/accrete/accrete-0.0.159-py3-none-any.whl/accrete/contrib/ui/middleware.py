import json
import logging
import ast

from django.utils.deprecation import MiddlewareMixin
from django.http.response import HttpResponseRedirect, HttpResponsePermanentRedirect

from accrete.tenant import get_tenant

_logger = logging.getLogger(__name__)


class HtmxRedirectMiddleware(MiddlewareMixin):

    @staticmethod
    def process_response(request, response):
        if getattr(request, 'skip_htmx_redirect_middleware', False):
            return response
        is_htmx = request.headers.get('HX-Request', 'false') == 'true'
        if not is_htmx:
            return response
        is_redirect = isinstance(response, HttpResponseRedirect)
        is_permanent_redirect = isinstance(response, HttpResponsePermanentRedirect)
        if is_redirect or is_permanent_redirect:
            response.status_code = 200
            header = 'HX-Location' if is_redirect else 'HX-Redirect'
            response[header] = response['Location']
        return response


class HtmxTriggerMiddleware(MiddlewareMixin):

    @staticmethod
    def process_response(request, response):
        tenant = get_tenant()
        trigger = {'setTenant': tenant and tenant.id or 0}
        res_trigger = response.get('HX-Trigger')
        try:
            res_trigger = res_trigger and ast.literal_eval(res_trigger) or None
        except Exception as e:
            _logger.warning(e)
            res_trigger = None
        if res_trigger:
            if isinstance(res_trigger, dict):
                trigger.update(res_trigger)
            else:
                _logger.warning(
                    'Response Header "HX-Trigger" '
                    'could not be evaluated to be a dict and is ignored!'
                )
        response['HX-Trigger'] = json.dumps(trigger)
        return response
