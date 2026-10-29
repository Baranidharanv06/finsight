import boto3
client = boto3.client('cognito-idp', region_name='us-east-1')
response = client.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    ClientId='5vt84f5poh0hqkuqcblvkn45ai',
    AuthParameters={'USERNAME': 'executive@test.com', 'PASSWORD': 'Test@12345'}
)
print(response['AuthenticationResult']['IdToken'])
