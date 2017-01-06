import os
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow, Everyone, Authenticated
from pyramid.session import SignedCookieSessionFactory

from passlib.apps import custom_app_context as pwd_context


class MyRoot(object):
    def __init__(self, request):
        self.reqeust = request

    __acl__ = [
        (Allow, Authenticated, 'admin')
    ]


def check_credentials(username, password):
    if username and password:
        if username == os.environ['AUTH_USERNAME']:
            return pwd_context.verify(password, os.environ['AUTH_PASSWORD'])
    return False


def includeme(config):
    """Pyramid security configuration."""
    auth_secret = os.environ.get('AUTH_SECRET', 'donttellanyone')
    authn_policy = AuthTktAuthenticationPolicy(
        secret=auth_secret,
        hashalg='sha512'
    )
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_root_factory(MyRoot)
    session_secret = os.environ.get('SESSION_SECRET', 'shhhecret')
    session_factory = SignedCookieSessionFactory(session_secret)
    config.set_session_factory(session_factory)
    config.set_default_csrf_options(require_csrf=True)
