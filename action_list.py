import os
import hmac
from flask import Response

def authenticate(request):
    if request.method != 'POST':
        r =  '|ERROR| Request must be POST'; print (r)
        return Response(r, status=401, mimetype='application/json')

    elif 'authorization' not in request.headers:
        r = '|ERROR| Request does not have auth token'; print (r)
        return Response(r, status=400, mimetype='application/json')

    else:
        expected_auth_header = 'Token token="{}"'.format(os.environ.get('header'))
        submitted_auth = request.headers['authorization']
        if hmac.compare_digest(expected_auth_header,submitted_auth):
            return Response(status=200, mimetype='application/json')

        else:
            r = '|ERROR| Incorrect token'; print (r)
            return Response(r, status=403, mimetype='application/json')




def action_list(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth
    """Return a list of actions"""
    return {
       "label": "Send Tabbed Dashboards with Tabby!",
       "integrations": [
           {
           "name": "Tabby",
           "label": "Tabby",
           "description": "Write dashboard tiles to a tabbed excel sheet.",
           "form_url":"https://URLGOESHERE.cloudfunctions.net/action_form",
           "supported_action_types": ["dashboard"],
           "supported_download_settings": ["url"],
           "supported_formats": ["csv_zip"],
           "supported_formattings": ["unformatted"],
           "url": "https://URLGOESHERE.cloudfunctions.net/action_execute",
            "icon_data_uri":URIGOESHERE
    
           
           }
       ]
    }
