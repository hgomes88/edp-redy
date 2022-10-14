import argparse

REGION = 'eu-west-1'
USER_POOL_ID = REGION + '_' + '7qre3K7aN'
CLIENT_ID = '78fe04ngpmrualq67a5p59sbeb'
IDENTITY_POOL_ID = REGION + ':' + 'a9a52b46-1722-49a0-8f8b-e8532c12abef'
IDENTITY_LOGIN = 'cognito-idp' + '.' + REGION + \
    '.' + 'amazonaws.com' + '/' + USER_POOL_ID


parser = argparse.ArgumentParser(description='Login into Redy')

parser.add_argument(
    '-u', '--username',
    action='store',
    help='Username'
)

parser.add_argument(
    '-p', '--password',
    action='store',
    help='Password'
)

parser.add_argument(
    '-upid', '--user_pool_id',
    action='store',
    default=USER_POOL_ID,
    help='User Pool Id',
)

parser.add_argument(
    '-cid', '--client_id',
    action='store',
    default=CLIENT_ID,
    help='Client Id'
)

parser.add_argument(
    '-r', '--region',
    action='store',
    default=REGION,
    help='Region'
)

parser.add_argument(
    '-iid', '--identity_id',
    action='store',
    default=IDENTITY_POOL_ID,
    help='Identity Id'
)

parser.add_argument(
    '-il', '--identity_login',
    action='store',
    default=IDENTITY_LOGIN,
    help='Identity Login'
)
