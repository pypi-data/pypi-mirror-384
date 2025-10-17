import datetime as dt
import os
# Local
from google_account_client import GoogleAccountFactory

# Config
credentials_path = 'keys/google_webapp_credentials.json'
user_token = None
redirect_uri = 'http://localhost:8080/callback'
# 


google_account_factory = GoogleAccountFactory(credentials_path, enable_logs=True)

if not google_account_factory.is_valid_token(user_token):
    auth_url, state = google_account_factory.generate_authorization_url(redirect_uri)

    # Produção
    '''
    @app.route("/auth/callback")
    def google_callback():
        redirected_url = request.url  # ou request.full_path se preferir só os params
        state = session.get('oauth_state')  # ou o que você tiver usado pra guardar
        creds = google_account_factory.fetch_token_from_redirect(redirected_url, expected_state=state)
        
        # agora salva o token, ou carrega a conta
    '''
    
    # Teste dev
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print('OAuth link:\n', auth_url, '\n')
    redirect_response = input('Input redirect response:\n')
    user_token = google_account_factory.fetch_token_from_redirect(redirect_response, expected_state=state)
    
    '''Save token'''

user = google_account_factory.load_account('diacde', user_token)


# Create Events
user.calendar.create_event(
    summary="Ultimo teste criação de evento",
    start_date_time=dt.datetime(2025, 10, 17, 20, 0),
    end_date_time=dt.datetime(2025, 10, 17, 22, 0),
    location="Rua dos Deploys, 42",
    attendees_emails=["teste@exemplo.com"],
)

# List Events
prox_eventos = user.calendar.list_events()