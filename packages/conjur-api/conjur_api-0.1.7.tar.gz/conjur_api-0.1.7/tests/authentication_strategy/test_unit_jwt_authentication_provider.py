from aiounittest import AsyncTestCase

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.providers import JWTAuthenticationStrategy

class JWTAuthenticationStrategyTest(AsyncTestCase):

    async def test_missing_serviceid(self):
        conjur_url = "https://conjur.example.com"
        connection_info = ConjurConnectionInfo(conjur_url, "some_account")

        jwt_token = "eyJhb..."

        provider = JWTAuthenticationStrategy(jwt_token)
        with self.assertRaises(MissingRequiredParameterException) as context:
            await provider.authenticate(connection_info, None)

        self.assertRegex(context.exception.message, "service_id is required")
