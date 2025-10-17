"""
Módulo de tratamento centralizado de exceções para aplicações FastAPI.

Este módulo define uma série de exceções personalizadas e registra handlers
para capturar e tratar erros comuns na aplicação, retornando respostas JSON
padronizadas para o cliente, de forma consistente e segura.

Responsabilidades principais:
- Registrar exceções específicas (e.g. BadRequestException, EntityNotFound)
- Tratar exceções de infraestrutura (SQLAlchemy, erros 404/500)
- Mapear erros de validação de entrada (RequestValidationError)
- Gerar logs estruturados para análise e auditoria

Benefícios:
- Melhora a observabilidade da aplicação por meio de logs consistentes
- Evita vazamento de detalhes internos para o cliente
- Padroniza mensagens de erro e códigos HTTP
"""

import logging
from typing import Any, Callable, Optional

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError


class ErrorResponse(BaseModel):
    """
    Modelo de resposta de erro padronizado para a API.

    Attributes:
        detail (str): Descrição do erro ocorrido.
    """

    detail: str


logger = logging.getLogger(__name__)


class BaseException(Exception):
    """
    Classe base para exceções personalizadas da aplicação.

    Attributes:
        message (Optional[str]): Mensagem descritiva do erro.
    """

    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message or ""

    def __repr__(self):
        return self.__str__()


class BadRequestException(BaseException):
    pass


class InternalServerException(BaseException):
    pass


class EntityNotFound(BaseException):
    pass


class FieldNotAllowed(BaseException):
    pass


class FormException(BaseException):
    pass


class ApiGraphiqlExeception(BaseException):
    """Exceção para falhas ao acessar a API GraphQL."""

    pass


class ExpiredTokenException(BaseException):
    pass


class AccessDeniedException(BaseException):
    pass


class CRUDException(BaseException):
    pass


def create_exception_handler(
    status_code: int, initial_detail: Any
) -> Callable[[Request, Exception], JSONResponse]:
    """
    Fábrica de handlers de exceção.

    Cria dinamicamente uma função para tratar exceções específicas, retornando
    uma resposta JSON padronizada de acordo com o status HTTP e os detalhes
    iniciais informados.

    Args:
        status_code (int): Código HTTP a ser retornado.
        initial_detail (Any): Estrutura base da resposta de erro.

    Returns:
        Callable: Função handler compatível com FastAPI.
    """

    def exception_handler(_: Request, exc: Exception):
        detail = dict(initial_detail)  # cópia imutável
        if f"{exc}":
            detail["detail"] = f"{exc}"
        return JSONResponse(content=detail, status_code=status_code)

    return exception_handler


def register_all_errors(app: FastAPI) -> None:
    """
    Registra todos os manipuladores de exceção customizados na aplicação FastAPI.

    Este método centraliza o registro dos erros conhecidos da aplicação,
    além de tratar erros genéricos e de infraestrutura (como SQLAlchemy e validações Pydantic).

    Args:
        app (FastAPI): Instância principal da aplicação FastAPI.

    Returns:
        None
    """
    app.add_exception_handler(
        BadRequestException,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "detail": "Requisição inválida!",
                "resolution": "Por favor, verifique os campos da requisição.",
                "error_code": "bad_request",
            },
        ),
    )

    app.add_exception_handler(
        AccessDeniedException,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "detail": "Você não tem permissão para acessar o recurso!",
                "resolution": "Por favor, solicite a permissão junto a "
                "administração do sistema",
                "error_code": "access_denied",
            },
        ),
    )

    app.add_exception_handler(
        ApiGraphiqlExeception,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "detail": "Erro ao buscar dados na api graphQL.",
                "resolution": "Por favor, confira e corrija os "
                "dados informados na requisição.",
                "error_code": "api_graphiql_error",
            },
        ),
    )

    app.add_exception_handler(
        CRUDException,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "detail": "Erro ao manipular registros no banco de dados!",
                "resolution": "Por favor, confira e corrija os dados "
                "informados na requisição.",
                "error_code": "crud_error",
            },
        ),
    )

    app.add_exception_handler(
        EntityNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "detail": "Registro não encontrado no banco de dados!",
                "resolution": "Por favor, informe um registro válido.",
                "error_code": "entity_not_found",
            },
        ),
    )

    app.add_exception_handler(
        ExpiredTokenException,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "detail": "Token expirado!",
                "resolution": "Por favor, obtenha um token válido.",
                "error_code": "token_expired",
            },
        ),
    )

    app.add_exception_handler(
        FieldNotAllowed,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "detail": "Campo não permitido!",
                "resolution": "Por favor, informe um campo válido.",
                "error_code": "field_not_allowed",
            },
        ),
    )

    app.add_exception_handler(
        FormException,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "detail": "Formulário inválido!",
                "resolution": "Por favor, confira e corrija os dados do formulário informados na requisição.",
                "error_code": "form_exception",
            },
        ),
    )

    app.add_exception_handler(
        InternalServerException,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail={
                "detail": "Ocorreu um erro inesperado!",
                "resolution": "Por favor, tente novamente mais tarde, se o problema persistir, entre em contato com o suporte.",
                "error_code": "internal_server_error",
            },
        ),
    )

    @app.exception_handler(Exception)
    def exception_handler(request: Request, exc: Exception):
        message = {
            "detail": "Ops! Ocorreu um erro inesperado.",
            "error_code": "internal_server_error",
            "resolution": "Por favor, se o erro persistir entre em contato.",
        }

        logger.critical(
            f"[{request.method}] {request.url.path} - Erro inesperado: {exc}",
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=message,
        )

    @app.exception_handler(500)
    def internal_server_error(request: Request, exc: Exception):
        message = {
            "detail": "Ops! Ocorreu um erro inesperado.",
            "error_code": "internal_server_error",
            "resolution": "Por favor, se o erro persistir entre em contato.",
        }

        logger.critical(
            f"[{request.method}] {request.url.path} - Erro inesperado: {exc}",
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=message,
        )

    @app.exception_handler(404)
    def route_not_found(request: Request, _: Exception):
        _path = request.url

        message = {
            "detail": f"O endereço {_path} não encontrado!",
            "error_code": "bad_request",
            "resolution": "Informe um endereço válido.",
        }

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=message,
        )

    @app.exception_handler(SQLAlchemyError)
    def database__error(_: Request, exc: Exception):
        message = {
            "detail": "Ocorreu um erro inesperado ao acessar os dados!",
            "error_code": "internal_server_error",
            "resolution": "Por favor, se o erro persistir entre em contato.",
        }

        logger.critical(msg=f"{exc}")

        return JSONResponse(
            content=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(_: Request, exc: RequestValidationError):
        """
        Manipulador global para erros de validação de requisições (RequestValidationError).

        Este handler captura erros gerados pelo FastAPI/Pydantic durante a validação
        dos dados de entrada (query params, body, path params, etc.) e retorna uma
        resposta JSON padronizada.

        Args:
            request (Request): Objeto da requisição HTTP.
            exc (RequestValidationError): Exceção gerada pelo FastAPI.

        Returns:
            JSONResponse: Resposta HTTP 400 com informações detalhadas do erro.
        """
        errors = exc.errors()
        error = errors[0]
        error_type = error.get("type", None)
        error_loc = error.get("loc", ("", ""))
        error_ctx = error.get("ctx", "")
        dado = error_loc[0]

        for e in errors:
            logger.debug(e)
            logger.debug(e.get("type", None))

        status_code = status.HTTP_400_BAD_REQUEST

        match error_type:
            case "value_error":
                dado = error_loc[1]
                message = f"Informe um {dado} válido!"

            case "literal_error":
                dado = error_loc[1]
                message = f"O campo {dado} está fora dos padrões.\
                    Os valores esperados são: {error_ctx.get('expected')}"

            case "value_error.missing":
                message = f'O dado "{dado}" não foi informado na requisição!'

            case "missing":
                try:
                    dado = error_loc[1]
                    message = f'O campo "{dado}" não foi informado na requisição!'
                except Exception:
                    message = "Não foi encontrado corpo na requisição!"

            case "model_attributes_type":
                message = f'O tipo do campo "{dado}" está incorreto!'

            case "string_type":
                dado = error_loc[1]
                message = f"Informe um {dado} com o formato válido!"

            case "string_too_short":
                dado = error_loc[1]
                size = error_ctx["min_length"]
                message = f'O campo "{dado}" deve ter mais que {size} caracteres!'

            case "string_too_long":
                dado = error_loc[1]
                size = error_ctx["max_length"]
                message = f'O campo "{dado}" deve ter menos que {size} caracteres!'

            case "bool_parsing":
                dado = error_loc[1]
                message = f"Informe o campo {dado} com o formato boleano válido!\
                    true ou false"

            case "string_parsing":
                dado = error_loc[1]
                message = f"Informe o campo {dado} com o formato string válido!"

            case "json_invalid":
                dado = error.get("ctx", {})
                message = f"O json da requisição é inválido! {dado.get('error')}"

            case _:
                logger.error(msg=f"Erro do cliente não mapeado: {errors}")
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Requisição inválida!"

        logger.error(msg=f"Erro na validação dos dados! {status_code} - {message}")

        _message = {
            "detail": message,
            "error_code": "bad_request",
            "resolution": "Por favor, corriga as informações antes de enviar a requisição novamente.",
        }

        return JSONResponse(
            status_code=status_code,
            content=_message,
        )

    _ = (
        exception_handler,
        internal_server_error,
        route_not_found,
        database__error,
        validation_exception_handler,
    )
