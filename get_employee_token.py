import boto3

client = boto3.client('cognito-idp', region_name='us-east-1')
user_pool_id = 'us-east-1_CwV001fel'
client_id = '5vt84f5poh0hqkuqcblvkn45ai'

# Find employee username
users = client.list_users(UserPoolId=user_pool_id)
employee_username = None
for u in users['Users']:
    for attr in u['Attributes']:
        if attr['Name'] == 'email' and attr['Value'] == 'employee@test.com':
            employee_username = u['Username']

print(f"Found employee username: {employee_username}")

password = 'Test@12345'
client.admin_set_user_password(
    UserPoolId=user_pool_id,
    Username=employee_username,
    Password=password,
    Permanent=True
)

response = client.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    ClientId=client_id,
    AuthParameters={
        'USERNAME': employee_username,
        'PASSWORD': password
    }
)
print("\nEMPLOYEE JWT Token:\n")
print(response['AuthenticationResult']['IdToken'])
