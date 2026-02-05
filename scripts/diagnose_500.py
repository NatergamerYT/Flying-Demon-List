from app import create_app
import os
import traceback

app = create_app(os.getenv('FLASK_ENV') or 'development')
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

routes_to_test = ['/', '/auth/login', '/auth/register', '/admin', '/claims']

with app.test_client() as c:
    for r in routes_to_test:
        try:
            print(f'GET {r}')
            resp = c.get(r)
            print('Status:', resp.status_code)
            if resp.status_code >= 500:
                print('Response body:')
                print(resp.get_data(as_text=True)[:2000])
        except Exception:
            print('Exception while requesting', r)
            traceback.print_exc()
            print('---')

print('Diagnostic complete')
