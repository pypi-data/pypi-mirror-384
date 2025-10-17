import boto3
from homelink.auth.aws_srp import AWSSRP
from homelink.auth.abstract_auth import AbstractAuth
from homelink.settings import COGNITO_POOL_ID, COGNITO_CLIENT_ID
import hmac
import hashlib
import base64


# Function used to calculate SecretHash value for a given client
def calculateSecretHash(client_id, client_secret, username):
    key = bytes(client_secret, "utf-8")
    message = bytes(f"{username}{client_id}", "utf-8")
    return base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()


class SRPAuth:

    def async_get_access_token(self, username, password):
        client = boto3.client("cognito-idp", region_name="us-east-2")
        aws = AWSSRP(
            username=username,
            password=password,
            pool_id=COGNITO_POOL_ID,
            client_id=COGNITO_CLIENT_ID,
            client=client,
        )
        return aws.authenticate_user()
