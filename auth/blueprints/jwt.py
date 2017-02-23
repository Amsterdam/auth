"""
    auth.blueprints.token
    ~~~~~~~~~~~~~~~~~~~~~
"""
from flask import Blueprint, make_response

from auth import audit, httputils


def blueprint(refreshtokenbuilder, accesstokenbuilder, authz_level_for):
    """ JWT-only resources.

    This function returns a blueprint with two routes configured:

    - GET /refreshtoken: get an anonymous refreshtoken
    - GET /accesstoken: get an accesstoken

    :param token.RefreshTokenBuilder refreshtokenbuilder: JWT builder for refreshtokens
    :param token.AccessTokenBuilder accesstokenbuilder: JWT builder for accesstokens
    :param func authz_level_for: callable that maps a ``subject`` to an authz level
    :return: :class:`flask.Blueprint`
    """
    blueprint = Blueprint('jwt_app', __name__)

    @blueprint.route('/accesstoken', methods=('GET',))
    @httputils.assert_acceptable('text/plain')
    @httputils.response_mimetype('text/plain')
    @httputils.insert_jwt(refreshtokenbuilder)
    def accesstoken(tokendata, refreshjwt):
        """ Route for creating an access token based on a refresh token
        """
        authz_level = authz_level_for(tokendata['sub'])
        accesstoken = accesstokenbuilder.create(authz=authz_level)
        accessjwt = accesstoken.encode()
        audit.log_accesstoken(refreshjwt, accessjwt)
        return make_response((accessjwt, 200))

    @blueprint.route('/refreshtoken', methods=('GET',))
    @httputils.assert_acceptable('text/plain')
    @httputils.response_mimetype('text/plain')
    def refreshtoken():
        """ Route for creating an anonymous refreshtoken
        """
        refreshtoken = refreshtokenbuilder.create(sub=None)
        refreshjwt = refreshtoken.encode()
        audit.log_refreshtoken(refreshjwt)
        return make_response((refreshjwt, 200))

    return blueprint
