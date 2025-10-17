from typing import  Literal
import jwt.utils
import sempy.fabric as sfabric
import jwt

class UserCredAuth:
    def __init__(self,token: str)->None:
        self.acces_token = token

    def __call__(self,audience: Literal["pbi", "storage"] = "pbi") -> str:
            return self.acces_token


def initializeToken(ExplicitToken):
    sfabric._token_provider._get_token = UserCredAuth(ExplicitToken) # type: ignore
