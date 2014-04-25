import logging

from adhocracy import model
from paste.deploy.converters import asbool
from webob import Response

log = logging.getLogger(__name__)


class InstanceDiscriminatorMiddleware(object):

    def __init__(self, app, domain, config):
        self.app = app
        self.domain = domain
        self.config = config
        log.debug("Host name: %s." % domain)

    def __call__(self, environ, start_response):
        relative_urls = asbool(self.config.get('adhocracy.relative_urls',
                                               'false'))
        environ['adhocracy.domain'] = self.domain
        instance_key = self.config.get('adhocracy.instance')
        if instance_key is None:
            if relative_urls:
                path = environ.get('PATH_INFO', '')
                if path.startswith('/i/'):
                    instance_key = path.split('/')[2]
                    environ['PATH_INFO'] = path[len('/i/' + instance_key):]
                    if environ['PATH_INFO'] == '':
                        response = Response()
                        if instance_key == '':
                            response.status_int = 404
                            # Double slashes are stripped, so we can't redirect
                            # to /i//
                            return response(environ, start_response)

                        response.status_int = 302
                        response.headers['location'] = path + '/'
                        return response(environ, start_response)
            else:
                host = environ.get('HTTP_HOST', "")
                host = host.replace(self.domain, "")
                host = host.replace('localhost', "")
                host = host.split(':', 1)[0]
                host = host.strip('.').strip()
                instance_key = host

        if instance_key:  # instance key is set (neither None nor "")
            instance = model.Instance.find(instance_key)
            if instance is None:
                response = Response()
                if not relative_urls:
                    # HTTP_HOST needs to be set to an existing domain,
                    # otherwise we end up here again after being internally
                    # redirected from StatusCodeRedirect and produce a white
                    # page.
                    environ['HTTP_HOST'] = environ['adhocracy.domain']
                    # Fair handling of users prefixing everything with www.
                    if instance_key == 'www':
                        response.status_int = 301
                        response.headers['location'] = environ.get('PATH_INFO',
                                                                   '')
                        return response(environ, start_response)
                response.status_int = 404
                return response(environ, start_response)
            else:
                model.instance_filter.setup_thread(instance)
        try:
            return self.app(environ, start_response)
        finally:
            model.instance_filter.setup_thread(None)


def setup_discriminator(app, config):
    # warn if abdoned adhocracy.domains is used
    if config.get('adhocracy.domains') is not None:
        raise AssertionError('adhocracy.domains is not supported anymore. '
                             'use adhocracy.domain (without the s) with only '
                             'one domain')
    domain = config.get('adhocracy.domain').strip()
    return InstanceDiscriminatorMiddleware(app, domain, config)
