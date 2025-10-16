"""
FastAPI dependency helpers for query engine.

New explicit backend pattern:
- You construct a backend engine (e.g., BeanieQueryEngine(Product)).
- Use create_qe_dependency(engine) to produce a FastAPI dependency that parses,
  validates and compiles request filters into the backend-specific query.
"""

from typing import Callable, cast

from fastapi import HTTPException, Query, Request

from fastapi_qengine.core.ast import ASTBuilder
from fastapi_qengine.core.compiler_base import BaseQueryCompiler
from fastapi_qengine.core.config import QEngineConfig, default_config
from fastapi_qengine.core.errors import QEngineError
from fastapi_qengine.core.normalizer import FilterNormalizer
from fastapi_qengine.core.optimizer import ASTOptimizer
from fastapi_qengine.core.parser import FilterParser
from fastapi_qengine.core.types import FilterAST, FilterInput, SecurityPolicy, T
from fastapi_qengine.core.validator import FilterValidator


def _build_pipeline(
    config: QEngineConfig | None = None,
    security_policy: SecurityPolicy | None = None,
) -> tuple[QEngineConfig, FilterParser, FilterNormalizer, FilterValidator, ASTBuilder, ASTOptimizer]:
    """Inicializa y devuelve todos los componentes del pipeline de procesamiento."""
    cfg: QEngineConfig = config or default_config
    policy: SecurityPolicy = security_policy or cfg.security_policy
    parser: FilterParser = FilterParser(config=cfg.parser)
    normalizer: FilterNormalizer = FilterNormalizer()
    validator: FilterValidator = FilterValidator(config=cfg.validator, security_policy=policy)
    ast_builder: ASTBuilder = ASTBuilder()
    optimizer: ASTOptimizer = ASTOptimizer(config=cfg.optimizer)
    return cfg, parser, normalizer, validator, ast_builder, optimizer


def process_filter_to_ast(
    filter_input: str | dict[str, object],
    config: QEngineConfig | None = None,
    security_policy: SecurityPolicy | None = None,
) -> FilterAST:
    """Procesa la entrada a través de parse -> normalize -> validate -> build AST -> optimize."""
    _, parser, normalizer, validator, ast_builder, optimizer = _build_pipeline(config, security_policy)

    parsed_input: FilterInput = parser.parse(filter_input)
    normalized_input: FilterInput = normalizer.normalize(filter_input=parsed_input)
    validator.validate_filter_input(filter_input=normalized_input)
    ast: FilterAST = ast_builder.build(filter_input=normalized_input)
    optimized_ast: FilterAST = optimizer.optimize(ast)
    return optimized_ast


def _execute_query_on_engine(engine: BaseQueryCompiler[T], ast: FilterAST | None) -> T:
    """Ejecuta el AST (o vacío) en el motor de backend proporcionado.

    Si ast es None, se convierte a un AST vacío para los motores que esperan
    una instancia de FilterAST.
    """
    effective_ast: FilterAST = ast or FilterAST()
    if hasattr(engine, "build_query"):
        return engine.build_query(effective_ast)
    elif hasattr(engine, "compile"):
        return engine.compile(effective_ast)
    else:
        raise HTTPException(
            status_code=500,
            detail="Engine must have either 'build_query' or 'compile' method",
        )


def _get_filter_input_from_request(request: Request, filter_param: str | None = None) -> str | dict[str, object] | None:
    """Extrae la entrada del filtro del parámetro 'filter' o de los query params."""
    if filter_param is not None:
        return filter_param

    # Extrae parámetros que comienzan con "filter[" para filtros anidados.
    query_params: dict[str, str] = dict(request.query_params)
    filter_params: dict[str, object] = {k: v for k, v in query_params.items() if k.startswith("filter[")}
    return filter_params if filter_params else None


def _handle_processing_error(e: Exception, debug: bool) -> None:
    """Centraliza el manejo de errores, convirtiendo excepciones en respuestas HTTP."""
    if isinstance(e, QEngineError):
        # Errores de validación o parseo del usuario.
        raise HTTPException(status_code=400, detail=str(e))

    # Errores inesperados del servidor.
    if debug:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")

    raise HTTPException(status_code=400, detail="La especificación del filtro no es válida.")


# --- Función principal simplificada ---


def create_qe_dependency(
    engine: BaseQueryCompiler[T],
    *,
    config: QEngineConfig | None = None,
    security_policy: SecurityPolicy | None = None,
) -> Callable[[Request, str | None], T | None]:
    """
    Crea una dependencia de FastAPI usando una instancia explícita del motor de backend.

    La dependencia se encarga de:
    1. Extraer los filtros de la petición.
    2. Procesarlos para generar un AST (Abstract Syntax Tree).
    3. Ejecutar el AST en el motor para construir la consulta final.
    4. Manejar los errores de forma centralizada.
    """

    # Se obtiene la configuración una sola vez al crear la dependencia.
    cfg: QEngineConfig = config or default_config
    filter_query: str = cast(
        str,
        Query(default=None, alias="filter", description="Filtro en formato JSON o anidado"),
    )

    def dependency(
        request: Request,
        filter_param: str | None = filter_query,
    ) -> T | None:
        try:
            filter_input: str | dict[str, object] | None = _get_filter_input_from_request(request, filter_param)

            if not filter_input:
                # Si no hay filtro, delega con None (AST vacío implícito).
                return _execute_query_on_engine(engine, ast=None)

            # La lógica de procesamiento se delega a la función existente.
            ast: FilterAST = process_filter_to_ast(filter_input, config=cfg, security_policy=security_policy)

            return _execute_query_on_engine(engine, ast)

        except Exception as e:
            # La lógica de manejo de errores también se delega.
            _handle_processing_error(e, debug=cfg.debug)

    return dependency
