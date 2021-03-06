from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

from allauth.socialaccount.providers.oauth.client import OAuth
from allauth.socialaccount.providers.oauth.views import (OAuthAdapter,
                                                         OAuthLoginView,
                                                         OAuthCallbackView,
                                                         OAuthCompleteView)

from models import LinkedInProvider


class LinkedInAPI(OAuth):
    url = 'https://api.linkedin.com/v1/people/~'
    fields = ['id', 'first-name', 'last-name']

    def get_user_info(self):
        url = self.url + ':(%s)' % ','.join(self.fields)
        raw_xml = self.query(url)
        try:
            return self.to_dict(ElementTree.fromstring(raw_xml))
        except (ExpatError, KeyError, IndexError):
            return None

    def to_dict(self, xml):
        """
        Convert XML structure to dict recursively, repeated keys
        entries are returned as in list containers.
        """
        children = xml.getchildren()
        if not children:
            return xml.text
        else:
            out = {}
            for node in xml.getchildren():
                if node.tag in out:
                    if not isinstance(out[node.tag], list):
                        out[node.tag] = [out[node.tag]]
                    out[node.tag].append(self.to_dict(node))
                else:
                    out[node.tag] = self.to_dict(node)
            return out


class LinkedInOAuthAdapter(OAuthAdapter):
    provider_id = LinkedInProvider.id
    request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken'
    access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
    authorize_url = 'https://www.linkedin.com/uas/oauth/authorize'

    def get_user_info(self, request, app):
        client = LinkedInAPI(request, app.key, app.secret,
                             self.request_token_url)
        user_info = client.get_user_info()
        uid = user_info['id']
        extra_data = {}  # TODO
        data = dict(linkedin_user_info=user_info)
        if 'first-name' in user_info:
            data['first_name'] = user_info['first-name']
        if 'last-name' in user_info:
            data['last_name'] = user_info['last-name']
        return uid, data, extra_data

oauth_login = OAuthLoginView.adapter_view(LinkedInOAuthAdapter)
oauth_callback = OAuthCallbackView.adapter_view(LinkedInOAuthAdapter)
oauth_complete = OAuthCompleteView.adapter_view(LinkedInOAuthAdapter)
