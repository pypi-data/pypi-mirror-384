## zanzipy ✨

Zanzibar‑style authorization for Python, with a tiny DSL to declare your schema and a simple client to write and check permissions. Friendly, lightweight, and practical.

### Install 📦
```bash
pip install zanzipy
```

### Quick start 🚀
```python
from zanzipy.dsl.builder import SchemaBuilder
from zanzipy.client import ZanzibarClient
from zanzipy.storage.repos.concrete.memory.relations import InMemoryRelationRepository

# Define schema with the fluent DSL
registry = (
    SchemaBuilder()
        .namespace("user").done()
        .namespace("document")
            .relation("owner", subjects=["user"])  # direct
            .permission("can_view", union=["owner"])  # computed
            .done()
        .build()
)

# Use the in‑memory repo for a zero‑dependency start
client = ZanzibarClient(schema=registry, relations_repository=InMemoryRelationRepository())

client.write("document:readme", "owner", "user:alice")
assert client.check("document:readme", "can_view", "user:alice")
```

That’s it. Add more relations/permissions with the DSL, and swap the repository when you’re ready to plug in your storage.

See the `examples/` folder 📁 for more patterns (tuple‑to‑userset, groups, nested folders). A good starting point is `examples/boobledrive.py`.

### Quick start with mixins 🧩

Zanzipy also provides convenient mixins for Pythonic integration with your domain models.


```python
from dataclasses import dataclass

from zanzipy.client import ZanzibarClient
from zanzipy.dsl.builder import SchemaBuilder
from zanzipy.engine_integration import ZanzibarEngine, configure_authorization
from zanzipy.integration.mixins import AuthorizableResource, AuthorizableSubject
from zanzipy.storage.repos.concrete.memory.relations import InMemoryRelationRepository

# Define a minimal schema (user + document)
registry = (
    SchemaBuilder()
        .namespace("user").done()
        .namespace("document")
            .relation("owner", subjects=["user"])  # direct relation
            .permission("can_view", union=["owner"])  # computed permission
            .done()
        .build()
)

# Wire up the engine used by the mixins
client = ZanzibarClient(schema=registry, relations_repository=InMemoryRelationRepository())
configure_authorization(ZanzibarEngine(client))

# Domain models using mixins
@dataclass
class User(AuthorizableSubject):
    id: str

    def get_subject_dict(self) -> dict:
        return {"namespace": "user", "id": self.id}


@dataclass
class Document(AuthorizableResource):
    id: str

    def get_resource_dict(self) -> dict:
        return {"namespace": "document", "id": self.id}


# Use high‑level helpers
alice = User(id="alice")
readme = Document(id="readme")

readme.grant(alice, "owner")  # writes a tuple: document:readme#owner@user:alice
assert readme.check(alice, "can_view")  # True via the computed permission
```

For a fuller mixins setup with groups, SQLAlchemy models, and caching, see `examples/boobledrive_sqlalchemy_and_mixins.py`.

### Key features 🧰
- ✨ DSL‑first schema authoring (`SchemaBuilder`, `NamespaceBuilder`).
- 🔗 Zanzibar semantics: relations, permissions, union/intersection/exclusion, tuple‑to‑userset.
- ✅ Correctness‑first evaluation: cycle detection, max‑depth limits, and subject expansion.
- 🧩 Simple client API: `write`, `delete`, `check`, `list_objects`, `expand`.
- 🗄️ Storage‑agnostic: implement `RelationRepository`; start with in‑memory.
- ⚡ Optional caching: tuple cache and compiled rule cache for hot paths.

### When should you use zanzipy? 🤔
- You want ReBAC embedded in your Python app without running another service.
- You prefer a human‑readable, declarative schema (via a tiny DSL).
- Your app has shared resources (e.g., docs, folders, teams) and needs roles, groups, or nested access patterns.
- You need cross‑resource edges (tuple‑to‑userset) and clear, testable authorization logic.

### License
Apache‑2.0


