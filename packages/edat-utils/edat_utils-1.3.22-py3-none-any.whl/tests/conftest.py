import ast
import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
import requests
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.responses import JSONResponse

from edat_utils.api import ApiAcademicoService, ApiFuncionarioService
from edat_utils.v2.funcionario_service import (
    ApiFuncionarioService as FuncionarioService,
)
from edat_utils.v2.models import Usuario as Funcionario
from edat_utils.api.api_colegios_service.service import ApiColegiosTecnicosService
from edat_utils.api.api_dac_service.service import ApiDacService
from edat_utils.api.api_lotacao_service.service import ApiLotacaoService
from edat_utils.api.api_unidade_service.service import ApiUnidadeService
from edat_utils.api.models import Usuario
from edat_utils.api.usuario_service import UsuarioService
from edat_utils.edat_keycloak_service import EdatKeycloakService
from edat_utils.keycloak_service import KeycloakService
from edat_utils.v2.crud_base import Base
from edat_utils.v2.graphql_service import GraphQLService
from edat_utils.v2.errors_handler import register_all_errors
from tests.crud.models import UsuarioCreate, crud_usuario


logger = logging.getLogger(__name__)

# Carregar as variáveis de ambiente
load_dotenv()

# variáveis de ambiente
rh_private_url = os.getenv("RH_PRIVATE_URL", "")
rh_public_url = os.getenv("RH_PUBLIC_URL", "")
academico_private_url = os.getenv("ACADEMICO_PRIVATE_URL", "")
academico_public_url = os.getenv('ACADEMICO_"PUBLIC_URL', "")
keycloak_url = os.getenv("KEYCLOAK_URL", "")

auth_url = os.getenv("AUTH_URL", "")
client_id = os.getenv("CLIENT_ID", "")
client_scope = os.getenv("CLIENT_SCOPE", "")
username = os.getenv("USERNAME", "")
password = os.getenv("PASSWORD", "")

a_client_id = os.getenv("A_CLIENT_ID", "")
a_client_secret = os.getenv("A_CLIENT_SECRET", "")
a_client_scope = os.getenv("A_CLIENT_SCOPE", "")
a_grant_type = os.getenv("A_GRANT_TYPE", "")

usernames = os.getenv("USERNAMES", "[]")
matriculas = os.getenv("MATRICULAS", "[]")
identificadores = os.getenv("IDENTIFICADORES", "[]")
identificadores_funcamp = os.getenv("IDENTIFICADORES_FUNCAMP", "[]")


@pytest.fixture(scope="session")
def get_token() -> Generator:
    access_token = None

    data = {
        "client_id": client_id,
        "client_secret": client_scope,
        "username": username,
        "password": password,
        "grant_type": "password",
    }

    response = requests.post(auth_url, data=data)

    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
    else:
        logger.error(
            msg=f"Erro ao obter o token: {response.status_code} {response.text}"
        )

    yield access_token


@pytest.fixture()
def get_funcionario_service(get_token: str) -> Generator:
    yield FuncionarioService(
        token=get_token, endpoint_url=rh_private_url, response_model=Funcionario
    )


@pytest.fixture()
def get_api_funcionario_service(get_token: str) -> Generator:
    yield ApiFuncionarioService(token=get_token, url=rh_private_url)


@pytest.fixture()
def get_api_academico_service(get_token: str) -> Generator:
    yield ApiAcademicoService(token=get_token, url=academico_private_url)


@pytest.fixture()
def get_api_colegios_tecnicos_service(get_token: str) -> Generator:
    yield ApiColegiosTecnicosService(token=get_token, url=academico_private_url)


@pytest.fixture()
def get_api_unidade_service(get_token: str) -> Generator:
    yield ApiUnidadeService(token=get_token, url=rh_public_url)


@pytest.fixture()
def get_api_lotacao_service(get_token: str) -> Generator:
    yield ApiLotacaoService(token=get_token, url=rh_public_url)


@pytest.fixture()
def get_api_dac_service(get_token: str) -> Generator:
    yield ApiDacService(token=get_token, url=academico_private_url)


@pytest.fixture()
def get_keycloak_service() -> Generator:
    yield KeycloakService(
        base_url=keycloak_url, username=username, password=password, realm="test"
    )


@pytest.fixture()
def get_usuario_service(
    get_api_funcionario_service,
    get_api_academico_service,
    get_api_colegios_tecnicos_service,
) -> Generator:
    yield UsuarioService(
        funcionario_service=get_api_funcionario_service,
        academico_service=get_api_academico_service,
        colegio_service=get_api_colegios_tecnicos_service,
    )


@pytest.fixture(scope="function")
def get_graphql_service(get_token: str):
    """Retorna instância configurada do GraphQLService para uso em testes."""
    yield GraphQLService(
        endpoint_url=rh_private_url,
        response_model=Usuario,
        token=get_token,
    )


@pytest.fixture(scope="function")
def get_student_graphql_service(get_token: str):
    """Retorna instância configurada do GraphQLService para uso em testes."""
    yield GraphQLService(
        endpoint_url=academico_private_url,
        response_model=Usuario,
        token=get_token,
    )


@pytest.fixture()
def get_edat_keycloak_service() -> Generator:
    yield EdatKeycloakService(
        base_url=keycloak_url,
        client_id=a_client_id,
        client_secret=a_client_secret,
        realm="test",
    )


@pytest.fixture
def get_usernames() -> Generator:
    yield ast.literal_eval(usernames)


@pytest.fixture
def get_identificadores() -> Generator:
    yield ast.literal_eval(identificadores)


@pytest.fixture
def get_identificadores_funcamp() -> Generator:
    yield ast.literal_eval(identificadores_funcamp)


@pytest.fixture
def get_matriculas() -> Generator:
    yield ast.literal_eval(matriculas)


@pytest.fixture
async def engine():
    """Cria engine SQLite em memória."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Cria sessão async para testes."""
    connection = await engine.connect()
    transaction = await connection.begin()

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def usuario_sample(db_session):
    """Cria um usuário de exemplo."""
    usuario = await crud_usuario.create(
        db=db_session,
        obj_in=UsuarioCreate(nome="João Silva", email="joao@test.com", ativo=True),
    )
    return usuario


@pytest.fixture
def app():
    """Cria uma instância FastAPI com os handlers de exceção registrados."""
    app = FastAPI()
    register_all_errors(app)

    # Adiciona rota de teste para erro 500
    @app.get("/crash")
    def crash_endpoint():
        raise ZeroDivisionError("Erro forçado")

    return app


@pytest.fixture
def client(app):
    """Cliente de teste síncrono."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Cliente de teste assíncrono."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ==== FIXTURE: SERVIDOR GRAPHQL FAKE ====
@pytest.fixture
async def fake_graphql_server():
    """
    Servidor GraphQL simulado via FastAPI.
    Ele responde a /graphql com diferentes tipos de payloads conforme o "query" recebido.
    """
    app = FastAPI()

    @app.post("/graphql")
    async def graphql_endpoint(payload: dict):
        query = payload.get("query", "")

        # Cenário de sucesso com objeto único
        if "getUser" in query:
            return JSONResponse({"data": {"getUser": {"id": 1, "name": "Alice"}}})

        # Cenário de sucesso com lista
        if "listUsers" in query:
            return JSONResponse(
                {
                    "data": {
                        "listUsers": [
                            {"id": 1, "name": "Alice"},
                            {"id": 2, "name": "Bob"},
                        ]
                    }
                }
            )

        # Cenário de erro GraphQL
        if "graphqlError" in query:
            return JSONResponse(
                {"errors": [{"message": "Some GraphQL error"}]}, status_code=200
            )

        # Cenário de erro 500 para testar retries
        if "serverError" in query:
            return JSONResponse({"error": "Internal Server Error"}, status_code=500)

        # Default
        return JSONResponse({"data": {}})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
