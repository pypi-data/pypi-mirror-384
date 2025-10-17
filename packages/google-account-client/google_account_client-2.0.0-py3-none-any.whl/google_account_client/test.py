import datetime as dt
import os
# Local
from google_account_client import GoogleAccountFactory

# Google Cloud lib
if __name__ == '__main__':
    credentials_path = 'keys/google_webapp_credentials.json'
    # user_token = 'tokens/diacde.json'
    user_token = 'awf'
    redirect_uri = 'http://localhost:8080/callback'
    
    # LOGIN
    # {
    # Use Token
    google_account_factory = GoogleAccountFactory(credentials_path, enable_logs=True)
    
    if not google_account_factory.is_valid_token(user_token):
        auth_url, state = google_account_factory.generate_authorization_url(redirect_uri)
        # └→ envia auth_url pro front, o usuário loga no Google
        # └→ Google chama redirect_uri?code=...&state=...

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

    user_account = google_account_factory.load_account('diacde', user_token)


    # EVENTS
    # {
    # Create Events
    # user_account.calendar.create_event(
    #     summary="Ultimo teste criação de evento",
    #     start_date_time=dt.datetime(2025, 5, 15, 20, 0),
    #     end_date_time=dt.datetime(2025, 5, 15, 22, 0),
    #     location="Rua dos Deploys, 42",
    #     attendees_emails=["teste@exemplo.com"],
    # )

    # List Events
    prox_eventos = user_account.calendar.list_events() # TODO: Adicionar parâmetros para n° de eventos e data inicial
    # }