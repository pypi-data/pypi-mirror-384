import logging

from typing import Any, Dict, List, Optional, Type, Union

from edat_utils.v2.graphql_service import T, GraphQLService

logger = logging.getLogger(__name__)


class ApiFuncionarioService(GraphQLService):
    """Classe para gerenciar funcionarios"""

    head_query = """
    query buscarFuncionarios {
        getDadosFuncionarios(
            filter: {"""

    tail_query = """},
            orders: {field: "nome", type: ASC},
        ) {
            items {
                identificador: matricula
                nome
                email
                telefone: ramal
                unidade
                nome_unidade: nomeUnidade
                local
                nome_local: nomeLocal
                classificacaoCarreira
                cargo: tituloCargo
                descricaoNivel
                nomeSindicato
                designacao: nomeFuncao
            }
        }
      }"""

    def __init__(
        self,
        endpoint_url: str,
        response_model: Type[T],
        max_retries: int = 3,
        timeout: float = 10,
        logger: Optional[logging.Logger] = None,
        token: Optional[str] = None,
    ):
        super().__init__(
            endpoint_url, response_model, max_retries, timeout, logger, token
        )

    async def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Union[T, List[T]]:
        """
        Método para buscar na api

        Args:
        - query: str dos filtros
        - variables: dict com as variáveis
        """
        query = query.replace("'", '"')
        _query = f"{self.head_query}{query}{self.tail_query}"
        return await super().execute_query(_query, variables)
