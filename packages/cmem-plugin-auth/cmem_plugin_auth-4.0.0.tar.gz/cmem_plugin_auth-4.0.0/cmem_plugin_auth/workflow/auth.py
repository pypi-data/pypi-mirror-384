"""OAuth2 token generator workflow plugin module"""

import collections
from collections.abc import Iterator, Sequence
from typing import Any

from cmem_plugin_base.dataintegration.context import ExecutionContext
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    Entities,
    Entity,
    EntityPath,
    EntitySchema,
)
from cmem_plugin_base.dataintegration.parameter.choice import ChoiceParameterType
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from oauthlib.oauth2 import BackendApplicationClient, LegacyApplicationClient
from requests_oauthlib import OAuth2Session

CLIENT_CREDENTIALS = BackendApplicationClient.grant_type
PASSWORD_GRANT = LegacyApplicationClient.grant_type
GRANT_TYPE = collections.OrderedDict(
    {CLIENT_CREDENTIALS: "Client Credentials", PASSWORD_GRANT: "Password Grant"}
)

HEADLINE = "Provide an OAuth2 access token for other tasks (via config port)."

DOCUMENTATION = f"""{HEADLINE}

This task uses the provided client or user credentials and runs an OAuth2
authorization to the given service URL. It will fetch the output and provide the
token in a way that it can be used by other tasks to access the service.

Note: The consuming task needs to have the parameter `oauth_access_token` in order to
to use the output this task. You need to connect this task to the
**config port** of the consuming task.
"""

GRANT_TYPE_DESCRIPTION = """Select the used OAuth Grant Type in order to
specify how this plugin gets a valid token.

Depending on the value of this parameter, other authentication related parameter
will become mandatory or obsolete. The following values can be used:

- `client_credentials`: - this refers to the OAuth 2.0 Client Credentials Grant Type.
Mandatory parameter for this grant type are Client ID and Client Secret.
- `password` - this refers to the OAuth 2.0 Password Grant Type. Mandatory variables
for this grant type are Client ID, User name and Password.
"""

# nosec
OIDC = "OpenID Connect (OIDC) OAuth 2.0"
OAUTH_TOKEN_DESCRIPTION = f"""This is the {OIDC} token endpoint location
(a HTTP(S) URL)."""


@Plugin(
    label="OAuth2 Authentication",
    description=HEADLINE,
    documentation=DOCUMENTATION,
    parameters=[
        PluginParameter(
            name="oauth_grant_type",
            label="Grant Type",
            description=GRANT_TYPE_DESCRIPTION,
            param_type=ChoiceParameterType(GRANT_TYPE),
            default_value=CLIENT_CREDENTIALS,
        ),
        PluginParameter(
            name="oauth_token_url",
            label="Token Endpoint",
            description=OAUTH_TOKEN_DESCRIPTION,
        ),
        PluginParameter(
            name="oauth_client_id",
            label="Client ID",
            description="The Client ID obtained during registration.",
            default_value="",
        ),
        PluginParameter(
            name="oauth_client_secret",
            label="Client Secret",
            description="The Client Secret obtained during registration.",
            default_value="",
        ),
        PluginParameter(
            name="user_name",
            label="Username",
            description="The user account name used for authentication.",
            default_value="",
        ),
        PluginParameter(
            name="password",
            label="Password",
            description="The user account password.",
            default_value="",
        ),
    ],
)
class OAuth2(WorkflowPlugin):
    """Workflow Plugin: Generate oauth access token"""

    def __init__(  # noqa: PLR0913
        self,
        oauth_grant_type: str,
        oauth_token_url: str,
        oauth_client_id: str,
        oauth_client_secret: str,
        user_name: str,
        password: str,
    ) -> None:
        self.oauth_token_url: str = oauth_token_url
        self.oauth_client_id: str = oauth_client_id
        self.oauth_client_secret: str = oauth_client_secret
        self.oauth_grant_type: str = oauth_grant_type
        self.user_name: str = user_name
        self.password: str = password
        self.token: dict[str, Any] = {}

    def execute(self, inputs: Sequence[Entities], context: ExecutionContext) -> Entities:
        """Execute the workflow task"""
        _ = inputs, context
        self.log.info("Start creating access token.")
        if self.oauth_grant_type == CLIENT_CREDENTIALS:
            client = BackendApplicationClient(client_id=self.oauth_client_id)
        else:
            client = LegacyApplicationClient(client_id=self.oauth_client_id)
        oauth = OAuth2Session(client=client)
        self.token = oauth.fetch_token(
            token_url=self.oauth_token_url,
            client_id=self.oauth_client_id,
            client_secret=self.oauth_client_secret,
            username=self.user_name,
            password=self.password,
        )

        return self.get_or_create_entities([])

    def get_or_create_entities(self, inputs: Sequence[Entities]) -> Entities:
        """Get or create entities

        If exists append oauth access token to the first entity or create a new one with
        an oauth access token path
        """
        entity = None
        if inputs and inputs[0].entities:
            entity = next(self.get_entities(inputs[0]))
            schema = self.clone_schema(inputs[0].schema)
        if not entity:
            schema = EntitySchema(
                type_uri="https://eccenca.com/plugin/auth",
                paths=[],
            )
            entity = Entity(uri="", values=[])

        entity.uri = "urn:Parameter"
        entity.values.append([self.token["access_token"]])

        schema.type_uri = "urn:ParameterSettings"
        schema.paths.append(EntityPath(path="oauth_access_token"))

        return Entities(entities=[entity], schema=schema)

    def get_entities(self, entities: Entities) -> Iterator[Entity]:
        """Generate python entity iterator"""
        for entity in entities.entities:
            yield self.clone_entity(entity)

    def clone_entity(self, entity: Entity) -> Entity:
        """Clone java entity to python entity"""
        self.log.info("Clone java entity to python entity")
        values = list(entity.values)
        return Entity(uri=entity.uri, values=values)

    def clone_schema(self, schema: EntitySchema) -> EntitySchema:
        """Clone java schema to python schema"""
        self.log.info("Clone java schema to python schema")
        paths = list(schema.paths)
        return EntitySchema(type_uri=schema.type_uri, paths=paths)
