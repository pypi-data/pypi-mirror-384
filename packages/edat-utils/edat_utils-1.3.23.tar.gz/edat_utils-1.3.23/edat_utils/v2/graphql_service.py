from typing import TypeVar, Type, Generic, Optional, Dict, Any, Union, List
from pydantic import BaseModel, ValidationError
import httpx
import asyncio
import logging

T = TypeVar("T", bound=BaseModel)


class GraphQLService(Generic[T]):
    """
    Serviço genérico para comunicação com APIs GraphQL, com suporte a:
      - Retorno de lista ou objeto único
      - Repetição automática (erros 5xx)
      - Timeout e logging configuráveis
      - Token para ambiente de desenvolvimento ou testes
    """

    def __init__(
        self,
        endpoint_url: str,
        response_model: Type[T],
        max_retries: int = 3,
        timeout: float = 10.0,
        logger: Optional[logging.Logger] = None,
        token: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url
        self.response_model = response_model
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

    async def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Union[T, List[T]]:
        """
        Executa uma query GraphQL e retorna um modelo ou uma lista de modelos.

        Raises:
            httpx.HTTPStatusError: Se houver erro HTTP.
            Exception: Para erros GraphQL explícitos.
            ValidationError: Se o JSON não corresponder ao modelo.
            RuntimeError: Se todas as tentativas falharem sem sucesso.
        """
        payload = {"query": query, "variables": variables or {}}

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url=self.endpoint_url, headers=self.headers, json=payload
                    )
                    response.raise_for_status()

                    json_data = response.json()

                    if "errors" in json_data:
                        raise Exception(f"GraphQL errors: {json_data['errors']}")

                    # Obtém o conteúdo dentro de "data"
                    data_root = json_data.get("data")
                    if not data_root:
                        raise ValueError(
                            "Resposta GraphQL inválida: campo 'data' ausente."
                        )

                    # Pega a primeira chave dentro de data (dinâmica)
                    first_key = next(iter(data_root.keys()))
                    items = data_root[first_key].get("items")
                    if items is None:
                        raise ValueError(
                            f"Resposta GraphQL inválida: 'items' ausente em '{first_key}'."
                        )

                    # Converte cada item para o modelo Pydantic
                    return [self.response_model(**item) for item in items]

            except httpx.HTTPStatusError as e:
                last_exception = e
                status = e.response.status_code
                if 500 <= status < 600 and attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)
                    self.logger.warning(
                        f"Erro {status} na tentativa {attempt}/{self.max_retries}. "
                        f"Tentando novamente em {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                self.logger.error(f"Erro HTTP ao acessar {self.endpoint_url}: {e}")
                break

            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)
                    self.logger.warning(
                        f"Falha de transporte ou timeout ({e}). "
                        f"Tentando novamente em {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                self.logger.error(
                    f"Falha permanente ao acessar {self.endpoint_url}: {e}"
                )
                break

            except (ValidationError, Exception) as e:
                last_exception = e
                self.logger.error(f"Erro ao executar query GraphQL: {e}")
                break

        # 🔥 Garante que sempre há retorno (ou erro explícito)
        raise RuntimeError(
            f"Falha ao executar query GraphQL após {self.max_retries} tentativas."
        ) from last_exception
