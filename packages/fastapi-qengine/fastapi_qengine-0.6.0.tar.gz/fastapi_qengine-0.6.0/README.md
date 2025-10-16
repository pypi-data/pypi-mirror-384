# fastapi-qengine

[![PyPI version](https://badge.fury.io/py/fastapi-qengine.svg)](https://badge.fury.io/py/fastapi-qengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**fastapi-qengine** es un motor de consultas avanzado para FastAPI que permite a tus clientes construir consultas complejas directamente desde la URL, sin configuración por modelo. Inspirado en el sistema de filtros de Loopback 4, ofrece una arquitectura limpia basada en AST (Abstract Syntax Tree) para procesar, validar y compilar filtros hacia diferentes backends de base de datos.

## ¿Por qué fastapi-qengine?

En lugar de definir filtros manualmente para cada modelo y campo, **fastapi-qengine** proporciona:

- 🎯 **Zero Configuration**: No necesitas crear clases de filtro por cada modelo
- 🔒 **Seguridad incorporada**: Validación automática y políticas de seguridad configurables
- 🏗️ **Arquitectura basada en AST**: Pipeline robusto de parseo → normalización → validación → optimización → compilación
- 🔌 **Multi-backend**: Actualmente soporta Beanie/PyMongo (SQLAlchemy y otros en desarrollo)
- 📝 **Sintaxis flexible**: Soporta tanto parámetros URL anidados como JSON completo
- 🚀 **Alto rendimiento**: Optimización automática de consultas y caching opcional
- 📚 **Documentación OpenAPI automática**: Integración perfecta con FastAPI

Este proyecto se enfoca en la **generación de consultas**, delegando la paginación a librerías especializadas como [fastapi-pagination](https://github.com/uriyyo/fastapi-pagination).

## Arquitectura

fastapi-qengine implementa un pipeline de procesamiento en varias etapas:

```
URL/JSON Input → Parser → Normalizer → Validator → AST Builder → Optimizer → Compiler → Backend Query
```

### Componentes Principales

1. **Parser** (`core.parser`): Procesa la entrada desde diferentes formatos (JSON string, params anidados, dict)
2. **Normalizer** (`core.normalizer`): Normaliza la estructura de datos a un formato estándar
3. **Validator** (`core.validator`): Valida la seguridad y estructura de las consultas
4. **AST Builder** (`core.ast`): Construye un árbol de sintaxis abstracta tipado
5. **Optimizer** (`core.optimizer`): Optimiza el AST eliminando redundancias
6. **Compiler** (`core.compiler_base`): Interfaz base para compiladores de backend
7. **Backend Compilers** (`backends/`): Implementaciones específicas (Beanie, etc.)

### Tipos de Nodos AST

- **FieldCondition**: Condiciones sobre campos específicos (`price > 100`)
- **LogicalCondition**: Combinaciones lógicas (`and`, `or`, `nor`)
- **OrderNode**: Especificaciones de ordenamiento
- **FieldsNode**: Proyecciones de campos (selección)

## Características Principales

### 🎯 Sintaxis de Consulta
- **Dos formatos soportados**: Parámetros URL anidados o JSON stringificado
- **Operadores de comparación**: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`, `regex`, `exists`, `size`, `type`
- **Operadores lógicos**: `and`, `or`, `nor` con anidamiento ilimitado
- **Alias sin **: Acepta tanto `gt` como `gt` para mayor flexibilidad

### 🔒 Seguridad
- **Políticas de seguridad configurables**: Control de campos permitidos/prohibidos
- **Límites configurables**: Máximo de condiciones, profundidad de anidamiento, valores en arrays
- **Validación automática**: Tipos de datos, nombres de campos, estructura de consultas
- **Protección contra inyección**: Validación estricta de operadores y valores

### ⚡ Performance
- **Optimización automática**: Simplificación de operadores lógicos, combinación de rangos, eliminación de redundancias
- **Caching opcional**: Cache de filtros parseados y consultas compiladas
- **Pipeline eficiente**: Procesamiento en múltiples etapas con validación temprana

### 🔌 Integración
- **FastAPI native**: Integración como dependencia de FastAPI
- **OpenAPI automático**: Documentación generada automáticamente en Swagger UI
- **Multi-backend**: Arquitectura extensible para soportar múltiples ORMs
- **Pagination-agnostic**: Compatible con cualquier librería de paginación

## Instalación

```bash
pip install fastapi-qengine
```

### Dependencias Opcionales

Para usar con Beanie/MongoDB:
```bash
pip install fastapi-qengine fastapi beanie pymongo
```

Para desarrollo completo con testing:
```bash
pip install fastapi-qengine[dev]
```

Para paginación (recomendado):
```bash
pip install fastapi-pagination
```

## Uso Rápido

### 1. Configuración Básica

```python
from fastapi import FastAPI, Depends
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.beanie import paginate

from fastapi_qengine import create_qe_dependency, BeanieQueryEngine

# Define tu modelo Beanie
class Product(Document):
    name: str
    category: str
    price: float
    in_stock: bool

    class Settings:
        name = "products"

# Inicializa FastAPI
app = FastAPI()

# Crea el motor de consultas para tu modelo
engine = BeanieQueryEngine(Product)
qe_dep = create_qe_dependency(engine)

# Define tu endpoint
@app.get("/products", response_model=Page[Product])
async def get_products(q = Depends(qe_dep)):
    query, projection_model, sort = q
    return await paginate(query, projection_model=projection_model, sort=sort)

add_pagination(app)
```

### 2. Inicialización de Base de Datos

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conectar a MongoDB
    client = AsyncMongoClient("mongodb://localhost:27017")
    await init_beanie(database=client.db_name, document_models=[Product])
    yield
    # Cleanup si es necesario

app = FastAPI(lifespan=lifespan)
```

### 3. Realizar Consultas

fastapi-qengine soporta dos formatos para construir consultas, proporcionando flexibilidad según la complejidad.

#### Formato 1: Parámetros URL Anidados
Ideal para consultas simples y uso desde navegadores:

```bash
# Productos con precio mayor a 50
GET /products?filter[where][price][gt]=50

# Productos en stock de categoría "electronics"
GET /products?filter[where][category]=electronics&filter[where][in_stock]=true

# Con ordenamiento descendente por precio
GET /products?filter[where][in_stock]=true&filter[order]=-price

# Selección de campos específicos
GET /products?filter[where][category]=books&filter[fields][name]=1&filter[fields][price]=1
```

#### Formato 2: JSON Stringificado
Recomendado para consultas complejas con operadores lógicos:

```bash
# OR lógico: electronics O precio < 20
GET /products?filter={"where":{"or":[{"category":"electronics"},{"price":{"lt":20}}]}}

# AND con múltiples condiciones
GET /products?filter={"where":{"and":[{"in_stock":true},{"price":{"gte":10,"lte":100}}]}}

# Consulta compleja anidada
GET /products?filter={"where":{"or":[{"category":"electronics","price":{"lt":1000}},{"category":"books","in_stock":true}]},"order":"-price","fields":{"name":1,"price":1,"category":1}}
```

**Nota**: En URLs reales, el JSON debe estar URL-encoded.

## Referencia de Sintaxis

### Estructura del Filtro

El objeto `filter` acepta tres claves principales:

```typescript
{
  "where": {...},      // Condiciones de búsqueda
  "order": "...",      // Ordenamiento
  "fields": {...}      // Proyección de campos
}
```

### Cláusula `where`

Define las condiciones de búsqueda usando operadores de MongoDB/PyMongo.

#### Operadores de Comparación

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `eq` o `=` | Igual a | `{"price": 100}` o `{"price": {"eq": 100}}` |
| `ne` | No igual a | `{"category": {"ne": "books"}}` |
| `gt` | Mayor que | `{"price": {"gt": 50}}` |
| `gte` | Mayor o igual que | `{"price": {"gte": 50}}` |
| `lt` | Menor que | `{"price": {"lt": 100}}` |
| `lte` | Menor o igual que | `{"price": {"lte": 100}}` |
| `in` | En array | `{"category": {"in": ["electronics", "books"]}}` |
| `nin` | No en array | `{"category": {"nin": ["toys"]}}` |
| `regex` | Expresión regular | `{"name": {"regex": "^Product"}}` |
| `exists` | Campo existe | `{"description": {"exists": true}}` |
| `size` | Tamaño de array | `{"tags": {"size": 3}}` |
| `type` | Tipo de campo | `{"price": {"type": "number"}}` |

#### Operadores Lógicos

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `and` | Y lógico | `{"and": [{"price": {"gt": 10}}, {"in_stock": true}]}` |
| `or` | O lógico | `{"or": [{"category": "electronics"}, {"price": {"lt": 20}}]}` |
| `nor` | NOR lógico | `{"nor": [{"category": "toys"}, {"in_stock": false}]}` |

#### Ejemplos de Consultas Complejas

```python
# Rango de valores
{"price": {"gte": 10, "lte": 50}}

# Múltiples condiciones (AND implícito)
{"category": "electronics", "in_stock": true, "price": {"lt": 1000}}

# OR con condiciones anidadas
{"or": [
    {"category": "electronics", "price": {"lt": 500}},
    {"category": "books", "in_stock": true}
]}

# Combinación de AND y OR
{"and": [
    {"in_stock": true},
    {"or": [
        {"category": "electronics"},
        {"price": {"lt": 30}}
    ]}
]}
```

### Cláusula `order`

Especifica el ordenamiento de resultados. Usa `-` como prefijo para orden descendente.

```python
# Ascendente
{"order": "price"}

# Descendente
{"order": "-price"}

# Múltiples campos (como string separado por comas)
{"order": "category,-price"}
```

### Cláusula `fields`

Define qué campos incluir en los resultados (proyección).

```python
# Incluir solo name y price
{"fields": {"name": 1, "price": 1}}

# Excluir campos específicos (usar 0)
{"fields": {"internal_id": 0, "metadata": 0}}
```

## Configuración Avanzada

### Políticas de Seguridad

Controla qué campos y operadores pueden usar tus clientes:

```python
from fastapi_qengine import SecurityPolicy, BeanieQueryEngine, create_qe_dependency

# Define política de seguridad
security_policy = SecurityPolicy(
    allowed_fields=["name", "category", "price", "in_stock"],  # Solo estos campos
    forbidden_fields=["internal_id", "secret_data"],           # Campos prohibidos
    allowed_operators=["eq", "gt", "lt", "in", "and"],    # Operadores permitidos
    max_conditions=10,                                          # Máximo de condiciones
    max_array_size=100,                                         # Tamaño máximo de arrays en in
    max_depth=5                                                 # Profundidad máxima de anidamiento
)

# Aplica al crear el motor
engine = BeanieQueryEngine(Product, security_policy=security_policy)
qe_dep = create_qe_dependency(engine)
```

### Configuración Personalizada

```python
from fastapi_qengine import QEngineConfig
from fastapi_qengine.core import ParserConfig, ValidatorConfig, OptimizerConfig

config = QEngineConfig(
    debug=True,
    parser=ParserConfig(
        max_nesting_depth=8,
        strict_mode=True,
        case_sensitive_operators=False
    ),
    validator=ValidatorConfig(
        validate_types=True,
        validate_operators=True
    ),
    optimizer=OptimizerConfig(
        enabled=True,
        simplify_logical_operators=True,
        remove_redundant_conditions=True,
        max_optimization_passes=3
    )
)

qe_dep = create_qe_dependency(engine, config=config)
```

### Uso del Pipeline Directo

Para casos avanzados, puedes usar el pipeline de procesamiento directamente:

```python
from fastapi_qengine import process_filter_to_ast
from fastapi_qengine.backends import compile_to_mongodb

# Procesa filtro a AST
filter_input = {"where": {"price": {"gt": 50}}, "order": "-price"}
ast = process_filter_to_ast(filter_input, config=config)

# Compila a MongoDB
mongodb_query = compile_to_mongodb(ast)
# Resultado: {"filter": {"price": {"gt": 50}}, "sort": [("price", -1)]}
```

### Proyección Dinámica de Respuestas

Genera modelos de respuesta dinámicos basados en los campos solicitados:

```python
from fastapi_qengine import create_response_model

ProductResponse = create_response_model(Product)

@app.get("/products", response_model=Page[ProductResponse])
async def get_products(q = Depends(qe_dep)):
    query, projection_model, sort = q
    # projection_model es dinámico según los campos solicitados
    return await paginate(query, projection_model=projection_model, sort=sort)
```

## Operadores Personalizados

Extiende la funcionalidad con operadores personalizados:

```python
from fastapi_qengine.operators import register_custom_operator, create_simple_operator

# Operador simple
custom_op = create_simple_operator(
    name="contains",
    compile_func=lambda field, value, backend: {field: {"regex": f".*{value}.*"}}
)
register_custom_operator("contains", custom_op)

# Ahora puedes usar: {"name": {"contains": "Product"}}
```

## Backends Soportados

### Beanie/PyMongo (Actual)

Soporte completo para MongoDB a través de Beanie ODM:

```python
from fastapi_qengine import BeanieQueryEngine

engine = BeanieQueryEngine(YourDocument)
```

### Próximamente

- **SQLAlchemy**: Para bases de datos SQL (PostgreSQL, MySQL, SQLite)
- **Tortoise ORM**: Async ORM para múltiples backends
- **Motor**: Driver async de MongoDB puro

## Integración con FastAPI Pagination

fastapi-qengine está diseñado para trabajar sin problemas con `fastapi-pagination`:

```python
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.ext.beanie import paginate as beanie_paginate

# Opción 1: Con Beanie
@app.get("/products", response_model=Page[Product])
async def list_products(q = Depends(qe_dep)):
    query, projection, sort = q
    return await beanie_paginate(query, projection_model=projection, sort=sort)

# Opción 2: Paginación manual
from fastapi_pagination import Params

@app.get("/products")
async def list_products(
    q = Depends(qe_dep),
    params: Params = Depends()
):
    query, projection, sort = q
    items = await query.skip(params.offset).limit(params.size).to_list()
    total = await query.count()
    return {"items": items, "total": total, "page": params.page, "size": params.size}

add_pagination(app)
```

## Ejemplos Completos

Consulta la carpeta `examples/` para ver implementaciones completas:

- **`basic.py`**: Ejemplo básico con Beanie
- **`security_policies.py`**: Uso avanzado de políticas de seguridad
- **`with_paginate.py`**: Integración con fastapi-pagination

## Comparación con Alternativas

| Característica | fastapi-qengine | fastapi-filter | Loopback 4 |
|----------------|-----------------|----------------|------------|
| Zero config | ✅ | ❌ | ✅ |
| Sintaxis flexible | ✅ | ⚠️ | ✅ |
| Operadores lógicos anidados | ✅ | ⚠️ | ✅ |
| AST-based | ✅ | ❌ | ✅ |
| Multi-backend | 🔄 | ✅ | ✅ |
| Políticas de seguridad | ✅ | ⚠️ | ✅ |
| Optimización de queries | ✅ | ❌ | ✅ |
| OpenAPI docs | ✅ | ✅ | ✅ |

✅ Soportado completamente | ⚠️ Parcialmente | ❌ No soportado | 🔄 En desarrollo

## Manejo de Errores

fastapi-qengine proporciona errores descriptivos para ayudar en debugging:

```python
from fastapi_qengine.core import QEngineError, ParseError, ValidationError, SecurityError

# Los errores se convierten automáticamente a HTTPException
# ParseError -> 400 Bad Request (JSON inválido o sintaxis incorrecta)
# ValidationError -> 400 Bad Request (estructura inválida)
# SecurityError -> 400 Bad Request (violación de política de seguridad)
```

Ejemplo de respuesta de error:

```json
{
  "detail": "Field 'secret_field' is not allowed by security policy"
}
```

## Testing

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
uv run pytest

# Con cobertura
uv run pytest --cov=fastapi_qengine --cov-report=html

# Tests específicos
uv run pytest tests/test_basic.py
uv run pytest tests/core/test_parser.py -v

# Por palabra clave
uv run pytest -k "security"
```

**Estadísticas de Testing:**
- ✅ 66 tests
- 📊 78% de cobertura de código
- 🔐 Tests de seguridad y validación
- 🧪 Tests unitarios, integración y E2E

## Rendimiento

fastapi-qengine está optimizado para alto rendimiento:

- **Pipeline eficiente**: Validación temprana para fallar rápido
- **Optimización automática**: Simplifica consultas antes de compilar
- **Caching opcional**: Cache de ASTs parseados y consultas compiladas
- **Zero overhead**: Sin reflection en runtime para backends soportados

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para discutir cambios.

### Guía de Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/urielcuriel/fastapi-qengine.git
cd fastapi-qengine

# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"

# Ejecutar tests
uv run pytest

# Lint y formato
ruff check fastapi_qengine/
ruff format fastapi_qengine/

# Ver cobertura
uv run pytest --cov=fastapi_qengine --cov-report=html
# Abre htmlcov/index.html en tu navegador
```

Consulta [DEVELOPMENT.md](DEVELOPMENT.md) para más detalles.

## Roadmap

- [x] Soporte completo para Beanie/PyMongo
- [x] Operadores de comparación y lógicos
- [x] Políticas de seguridad configurables
- [x] Optimización de AST
- [x] Documentación OpenAPI automática
- [ ] Backend para SQLAlchemy
- [ ] Backend para Tortoise ORM
- [ ] Soporte para agregaciones
- [ ] Cache de consultas con Redis
- [ ] Métricas y observabilidad

## Recursos

- **Documentación**: [https://github.com/urielcuriel/fastapi-qengine](https://github.com/urielcuriel/fastapi-qengine)
- **PyPI**: [https://pypi.org/project/fastapi-qengine/](https://pypi.org/project/fastapi-qengine/)
- **Issues**: [https://github.com/urielcuriel/fastapi-qengine/issues](https://github.com/urielcuriel/fastapi-qengine/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## Licencia

Este proyecto está bajo la Licencia MIT.

## Agradecimientos

Inspirado por el excelente sistema de filtros de [Loopback 4](https://loopback.io/doc/en/lb4/Querying-data.html), adaptado para el ecosistema Python/FastAPI.

---

**¿Necesitas ayuda?** Abre un [issue](https://github.com/urielcuriel/fastapi-qengine/issues) o inicia una [discusión](https://github.com/urielcuriel/fastapi-qengine/discussions).

**¿Te gusta el proyecto?** Dale una ⭐ en [GitHub](https://github.com/urielcuriel/fastapi-qengine)!
