from app import create_app

app = create_app()
config_dict = {k: v for k, v in app.config.items() if 'PASSWORD' not in k}
print('Flask Configuration:')
for key, value in sorted(config_dict.items()):
    print(f'{key}: {value}')
