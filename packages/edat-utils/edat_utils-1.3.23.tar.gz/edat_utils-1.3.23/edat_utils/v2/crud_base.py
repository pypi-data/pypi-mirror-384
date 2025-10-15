from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import as_declarative, selectinload


class_registry: Dict = {}


# ==================================================================
#      Classe base para sqlalchemy
# ==================================================================
@as_declarative(class_registry=class_registry)
class Base:
    id: Any
    __name__: str


# ==================================================================
#       Tipos genéricos
# ==================================================================

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
T = TypeVar("T")


# ==================================================================
#      Classe de retorno genérica de retorno
# ==================================================================
class Data(BaseModel, Generic[T]):
    """
    Modelo genérico para retorno de dados paginados.

    Exemplo:
    ```python
        @router.get("/usuarios", response_model=Data[Usuario])
        async def listar_usuarios(...):
            return await crud_usuario.get_multi(...)
    ```
    """

    data: List[T]
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None
    pages: Optional[int] = None


# ====================================================================
#   Classe Base para implementação de crud sqlalchemy versão 2.
#   Atende conexões assíncronas
#
#   Aborda operações básicas:
#   - get
#   - get_multi
#   - get_multi_advanced
#   - create
#   - update
#   - delete
#
#   Exemplo de uso:
#
#   result = await crud.get(id=123, relationships=['solicitacoes', 'historicos'])
#
# ====================================================================
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """CRUD genérico com suporte a operações assíncronas."""
        self.model = model

    async def get(
        self, db: AsyncSession, id: Any, relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        Busca uma instância pelo ID.

        Args:
        - id: identificador do registro
        - relationships: Lista de str com os nomes dos campos de relacionamentos
            estrangeiros que deseja obter na mesma query. Obtem os childrens*

        Return:
        - Optional: Se houver o registro, senão retorna None
        """
        stmt = select(self.model).where(self.model.id == id)

        # Carregar relacionamentos, se especificado
        if relationships:
            stmt = stmt.options(
                *[selectinload(getattr(self.model, rel)) for rel in relationships]
            )

        result = await db.scalar(stmt)
        return result

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: Optional[int] = 0,
        limit: Optional[int] = 5000,
        relationships: Optional[List[str]] = None,
    ) -> Data:
        """
        Busca múltiplas instâncias do modelo com suporte a paginação simples.

        Args:
        - db: Sessão assíncrona do SQLAlchemy.
        - skip: Quantidade de registros a ignorar (offset).
        - limit: Quantidade máxima de registros a retornar.
        - relationships: Lista opcional de relacionamentos para carregar
          de forma antecipada via `selectinload`.

        Returns:
        - Dict:
            {
                "data": [ModelType],
                "total": int,
                "page": int,
                "pages": int,
                "limit": int
            }

        Exemplo:
        ```python
            result = await crud.get_multi(
                db=session,
                skip=0,
                limit=50,
                relationships=["perfil"]
            )
            print(result.data, result.total)
        ```
        """

        # Normaliza parâmetros de paginação
        skip = max(skip or 0, 0)
        limit = max(
            min(limit or 100, 1000), 1
        )  # segurança para evitar limites excessivos

        # ====== Query base ======
        stmt = select(self.model)

        # Carregar relacionamentos, se especificado
        if relationships:
            stmt = stmt.options(
                *[selectinload(getattr(self.model, rel)) for rel in relationships]
            )

        # ====== Contagem total ======
        count_stmt = select(func.count(self.model.id))
        count_stmt = select(func.count()).select_from(self.model)
        total = await db.scalar(count_stmt)
        total = total or 0

        # ====== Paginação ======
        stmt = stmt.offset(skip).limit(limit)
        result = await db.scalars(stmt)
        items = list(result.all())

        # ====== Metadados ======
        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit if total > 0 else 0

        return Data(data=items, total=total, page=page, limit=limit, pages=pages)

    async def get_multi_advanced(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        skip: int = 0,
        limit: int = 100,
        relationships: Optional[List[str]] = None,
    ) -> Data:
        """
        Retorna múltiplas instâncias aplicando filtros dinâmicos,
        ordenação e paginação, além do total de registros encontrados.

        Args:
        - db: Sessão assíncrona do SQLAlchemy.
        - filters: Dicionário opcional de filtros dinâmicos,
          onde a chave é o nome do campo e o valor é o valor a filtrar.
        - order_by: Nome do campo utilizado para ordenação.
        - order_desc: Define se a ordenação será descendente (True) ou ascendente (False).
        - skip: Quantidade de registros a ignorar (offset).
        - limit: Quantidade máxima de registros a retornar.
        - relationships: Lista opcional com nomes de relacionamentos
          para carregar de forma antecipada via `selectinload`.

        Returns:
        - Dict:
            {
                "data": [ModelType],
                "total": int,
                "page": int,
                "pages": int,
                "limit": int
            }

        Exemplo:
        ```python
            result = await crud.get_multi_advanced(
                db=session,
                filters={"ativo": True},
                order_by="nome",
                order_desc=False,
                skip=0,
                limit=50,
                relationships=["perfil"]
            )
            print(result.data, result.total)
        ```
        """

        # Normaliza parâmetros
        skip = max(skip, 0)
        limit = max(min(limit, 1000), 1)  # limite de segurança

        # Base da query
        stmt = select(self.model)

        # Carregar relacionamentos, se especificado
        if relationships:
            stmt = stmt.options(
                *[selectinload(getattr(self.model, rel)) for rel in relationships]
            )

        # Filtros dinâmicos
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    stmt = stmt.where(getattr(self.model, field_name) == value)

        # Ordenação
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            stmt = stmt.order_by(desc(column) if order_desc else asc(column))

        # ====== Contagem otimizada ======
        count_stmt = select(func.count()).select_from(self.model)
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    count_stmt = count_stmt.where(
                        getattr(self.model, field_name) == value
                    )
        total = await db.scalar(count_stmt)
        total = total or 0

        # ====== Paginação ======
        stmt = stmt.offset(skip).limit(limit)
        result = await db.scalars(stmt)
        items = list(result.all())

        # ====== Metadados ======
        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit if total > 0 else 0

        return Data(data=items, total=total, page=page, limit=limit, pages=pages)

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        load_relationships: Optional[List[str]] = None,
    ) -> Optional[ModelType]:
        """
        Cria um novo registro no banco de dados, com suporte opcional a criação de
        relacionamentos aninhados (objetos filhos) e recarregamento de relacionamentos
        após a inserção.

        Args:
        - db: Sessão assíncrona do SQLAlchemy.
        - obj_in: Objeto de entrada Pydantic contendo os campos para criação do registro.
        - relationships: (Opcional) Dicionário contendo listas de objetos relacionados
          que devem ser criados junto ao objeto principal.
            Exemplo:
            ```python
            {
                "enderecos": [
                    {"logradouro": "Rua A", "numero": 10},
                    {"logradouro": "Rua B", "numero": 22}
                ]
            }
            ```
        - load_relationships: (Opcional) Lista de relacionamentos que devem ser
          carregados após a criação, utilizando `selectinload`.

        Returns:
        - ModelType: Instância do modelo criada e persistida no banco.

        Exemplo:
        ```python
        novo_usuario = await crud_usuario.create(
            db=session,
            obj_in=UsuarioCreate(nome="João", email="joao@teste.com"),
            relationships={
                "enderecos": [{"logradouro": "Rua A", "numero": 10}]
            },
            load_relationships=["enderecos"]
        )
        ```
        """
        obj_in_data = jsonable_encoder(obj_in)

        # Criar o objeto principal
        db_obj = self.model(
            **{k: v for k, v in obj_in_data.items() if not isinstance(v, (list, dict))}
        )

        # Processar relacionamentos aninhados, se fornecidos
        if relationships:
            for rel_name, rel_data in relationships.items():
                if hasattr(self.model, rel_name):
                    rel_model = getattr(self.model, rel_name).property.mapper.class_
                    related_objects = [rel_model(**data) for data in rel_data]
                    setattr(db_obj, rel_name, related_objects)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)

        # Recarregar o objeto com relacionamentos, se especificado
        if load_relationships:
            stmt = (
                select(self.model)
                .where(self.model.id == db_obj.id)
                .options(
                    *[
                        selectinload(getattr(self.model, rel))
                        for rel in load_relationships
                    ]
                )
            )
            result = await db.execute(stmt)
            db_obj = result.scalars().first()

        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> ModelType:
        """
        Atualiza um registro existente no banco de dados, com suporte opcional à
        atualização de relacionamentos aninhados.

        Args:
        - db: Sessão assíncrona do SQLAlchemy.
        - db_obj: Instância existente do modelo a ser atualizada.
        - obj_in: Objeto Pydantic ou dicionário contendo os campos a serem atualizados.
        - relationships: (Opcional) Dicionário contendo listas de objetos relacionados
          a serem atualizados ou recriados.

        Returns:
        - ModelType: Instância atualizada do modelo.

        Observações:
        - Caso `obj_in` seja um modelo Pydantic, apenas os campos definidos serão atualizados.
        - Relacionamentos fornecidos substituirão os existentes no registro.

        Exemplo:
        ```python
        usuario = await crud_usuario.get(db=session, id=1)
        usuario_atualizado = await crud_usuario.update(
            db=session,
            db_obj=usuario,
            obj_in={"nome": "Maria Silva"},
            relationships={
                "enderecos": [{"logradouro": "Av. Brasil", "numero": 123}]
            }
        )
        ```
        """
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        # Atualizar campos simples
        for field, value in update_data.items():
            if not isinstance(value, (list, dict)):
                setattr(db_obj, field, value)

        # Atualizar relacionamentos, se fornecidos
        if relationships:
            for rel_name, rel_data in relationships.items():
                if hasattr(self.model, rel_name):
                    rel_model = getattr(self.model, rel_name).property.mapper.class_
                    print(f"hasattr={rel_model}")
                    related_objects = [rel_model(**data) for data in rel_data]
                    print(f"related_objects={related_objects}")
                    setattr(db_obj, rel_name, related_objects)

        db.add(db_obj)
        await db.flush()

        # Recarregar com relacionamentos se foram atualizados
        if relationships:
            stmt = (
                select(self.model)
                .where(self.model.id == db_obj.id)
                .options(
                    *[
                        selectinload(getattr(self.model, rel))
                        for rel in relationships.keys()
                    ]
                )
            )
            result = await db.execute(stmt)

            if result:
                db_obj = result.scalars().first()
        else:
            await db.refresh(db_obj)

        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> None:
        """
        Remove uma instância do banco de dados com base no seu ID.

        Args:
        - db: Sessão assíncrona do SQLAlchemy.
        - id: Identificador do registro a ser removido.

        Returns:
        - None

        Observações:
        - Caso o registro não seja encontrado, nenhuma ação é realizada.
        - A remoção é feita via `flush`, permitindo encadeamento com outras operações
          antes do commit final.

        Exemplo:
        ```python
        await crud_usuario.remove(db=session, id=10)
        ```
        """
        obj = await db.get(self.model, id)
        if obj is not None:
            await db.delete(obj)
            await db.flush()
