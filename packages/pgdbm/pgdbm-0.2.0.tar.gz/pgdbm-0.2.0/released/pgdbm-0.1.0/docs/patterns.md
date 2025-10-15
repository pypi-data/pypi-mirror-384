# Deployment Patterns Guide

This guide helps you choose the right pattern for using pgdbm in your application or library.

## Overview: Three Main Patterns

1. **Standalone Service (Owner)** - Module owns and manages its database connection and migrations
2. **Reusable Library (Flexible)** - Module can own the DB or use one owned by another; always runs its migrations
3. **Shared Pool Application (Consumer)** - Multiple modules share one database/pool with schema isolation

## Pattern 1: Standalone Service (Owner)

Use this when your service runs independently and owns its database.

### When to Use

- Microservices that run separately
- Development and testing environments
- Simple applications with one database
- Services that can't share connections

### Implementation

```python
from pgdbm import AsyncDatabaseManager, DatabaseConfig, AsyncMigrationManager

class MyService:
    def __init__(self):
        self.db = None

    async def initialize(self):
        # Create own connection
        config = DatabaseConfig(
            connection_string="postgresql://localhost/myservice",
            min_connections=10,
            max_connections=20
        )
        self.db = AsyncDatabaseManager(config)
        await self.db.connect()

        # Run migrations
        migrations = AsyncMigrationManager(
            self.db,
            migrations_path="./migrations",
            module_name="myservice"
        )
        await migrations.apply_pending()

    async def shutdown(self):
        if self.db:
            await self.db.disconnect()
```

### Pros and Cons

✅ **Pros:**
- Simple to understand and implement
- Complete control over connection pool
- Easy to scale independently
- Clear ownership boundaries

❌ **Cons:**
- Uses more database connections
- Can't share resources with other services
- Each service needs its own configuration

## Pattern 2: Reusable Library (Flexible)

Use this when building a library that will be used by other applications (like memory-service).

### When to Use

- Building packages for PyPI
- Creating internal shared libraries
- Making pluggable components
- Writing framework extensions

### Implementation

```python
from typing import Optional
from pgdbm import AsyncDatabaseManager, AsyncMigrationManager

class MyLibrary:
    """A library that can work standalone or with shared pools."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        db_manager: Optional[AsyncDatabaseManager] = None,
        schema: Optional[str] = None
    ):
        if not connection_string and not db_manager:
            raise ValueError("Either connection_string or db_manager required")

        self._external_db = db_manager is not None
        self.db = db_manager
        self._connection_string = connection_string
        self._schema = schema

    async def initialize(self):
        # Create connection if not provided
        if not self._external_db:
            config = DatabaseConfig(
                connection_string=self._connection_string,
                schema=self._schema
            )
            self.db = AsyncDatabaseManager(config)
            await self.db.connect()

        # ALWAYS run your own migrations
        migrations = AsyncMigrationManager(
            self.db,
            migrations_path=Path(__file__).parent / "migrations",
            module_name="my_library"  # Unique name!
        )
        await migrations.apply_pending()

    async def close(self):
        # Only close if we created the connection
        if self.db and not self._external_db:
            await self.db.disconnect()

    # Library methods
    async def do_something(self):
        return await self.db.fetch_all(
            "SELECT * FROM {{tables.my_table}}"
        )
```

### Usage Examples

**Standalone mode:**
```python
library = MyLibrary(connection_string="postgresql://localhost/mydb")
await library.initialize()
```

**Shared pool mode:**
```python
# Parent application creates pool
shared_pool = await AsyncDatabaseManager.create_shared_pool(config)
db_manager = AsyncDatabaseManager(pool=shared_pool, schema="my_library")

# Pass to library
library = MyLibrary(db_manager=db_manager)
await library.initialize()
```

### Key Principles

1. **Support both modes** - Accept optional `db_manager` and `schema`
2. **Always run your own migrations** - Your module owns its schema, even on a shared DB
3. **Use `{{tables.}}` syntax** - Makes migrations/queries portable across schemas
4. **Use a unique `module_name`** - Isolates migration history
5. **Clean up conditionally** - Only if you created the connection

### Pros and Cons

✅ **Pros:**
- Flexible deployment options
- Works standalone or integrated
- Encapsulates schema management
- Reusable across projects

❌ **Cons:**
- More complex initialization
- Must handle both patterns
- Requires careful cleanup logic

## Pattern 3: Shared Pool Application (Consumer)

Use this when multiple services share one database with schema isolation.

### When to Use

- Monolithic apps with modular services
- Resource-constrained environments
- Multi-tenant SaaS applications
- Migrating from monolith to microservices

### Implementation

```python
from pgdbm import AsyncDatabaseManager, DatabaseConfig

class Application:
    def __init__(self):
        self.shared_pool = None
        self.services = {}

    async def initialize(self):
        # Create shared pool with total connections
        config = DatabaseConfig(
            connection_string="postgresql://localhost/app",
            min_connections=50,   # Total for ALL services
            max_connections=100   # Monitor usage!
        )
        self.shared_pool = await AsyncDatabaseManager.create_shared_pool(config)

        # Create schema-isolated managers
        user_db = AsyncDatabaseManager(pool=self.shared_pool, schema="users")
        order_db = AsyncDatabaseManager(pool=self.shared_pool, schema="orders")
        billing_db = AsyncDatabaseManager(pool=self.shared_pool, schema="billing")

        # Initialize services with their managers
        self.services['users'] = UserService(db_manager=user_db)
        self.services['orders'] = OrderService(db_manager=order_db)
        self.services['billing'] = BillingService(db_manager=billing_db)

        # Each service runs its own migrations
        for service in self.services.values():
            await service.initialize()

    async def shutdown(self):
        # Shutdown services first
        for service in self.services.values():
            await service.close()

        # Then close shared pool
        if self.shared_pool:
            await self.shared_pool.close()
```

### Schema Isolation

Each service gets its own schema to prevent conflicts:

```
Database: app
├── Schema: public
│   └── schema_migrations (shared)
├── Schema: users
│   ├── users table
│   └── profiles table
├── Schema: orders
│   ├── orders table
│   └── order_items table
└── Schema: billing
    ├── invoices table
    └── payments table
```

### Pool Sizing

Calculate pool size based on service needs:

```python
# Estimate connections per service
services = [
    ("users", 10),     # High traffic
    ("orders", 15),    # Very high traffic
    ("billing", 5),    # Low traffic
    ("analytics", 10), # Periodic jobs
]

# Calculate pool size
min_connections = sum(s[1] for s in services)      # 40
max_connections = min_connections * 2               # 80
surge_capacity = int(max_connections * 0.25)       # 20
total_max = max_connections + surge_capacity       # 100
```

### Monitoring

Track pool usage to detect issues:

```python
async def monitor_pool_health(shared_pool):
    stats = await shared_pool.get_pool_stats()

    usage = stats['used_size'] / stats['size']
    if usage > 0.8:
        logger.warning(f"High pool usage: {usage:.1%}")

    return {
        "total_connections": stats['size'],
        "active_connections": stats['used_size'],
        "idle_connections": stats['free_size'],
        "usage_percent": usage * 100
    }
```

## Security and Reliability Defaults

### TLS/SSL

Enable TLS and enforce certificate verification for production deployments:

```python
config = DatabaseConfig(
    connection_string="postgresql://db.example.com/app",
    ssl_enabled=True,
    ssl_mode="verify-full",        # 'require' | 'verify-ca' | 'verify-full'
    ssl_ca_file="/etc/ssl/certs/ca.pem",
)
db = AsyncDatabaseManager(config)
await db.connect()
```

Guidance:
- Use `verify-full` whenever possible.
- If you terminate TLS at a proxy, ensure the upstream to Postgres is secured and access-controlled.

### Statement and Session Timeouts

Prevent runaway queries and stuck transactions with server-side timeouts (milliseconds):

```python
config = DatabaseConfig(
    statement_timeout_ms=60_000,
    idle_in_transaction_session_timeout_ms=60_000,
    lock_timeout_ms=5_000,
)
```

These default to sane values; set to `None` to disable or override explicitly in `server_settings`.

### Cross-Schema Limitations

PostgreSQL foreign keys cannot cross schemas. Handle references in application code:

```python
# Can't use foreign keys between schemas
# user_id INTEGER REFERENCES users.users(id)  -- Won't work!

# Instead, validate in application:
async def create_order(self, user_id: UUID):
    # Validate user exists in users schema
    user = await self.user_service.get_user(user_id)
    if not user:
        raise ValueError("User not found")

    return await self.db.fetch_one("""
        INSERT INTO {{tables.orders}} (user_id, total)
        VALUES ($1, $2)
        RETURNING *
    """, user_id, total)
```

### Shared Tables Pattern

Some tables might be truly shared across services (in public schema):

```sql
-- migrations/001_shared.sql
-- Don't use {{tables.}} for truly shared tables
CREATE TABLE IF NOT EXISTS service_registry (
    service_name VARCHAR(100) PRIMARY KEY,
    service_url VARCHAR(255) NOT NULL,
    healthy BOOLEAN DEFAULT true
);
```

### Pros and Cons

✅ **Pros:**
- Efficient connection usage
- Centralized configuration
- Easy service coordination
- Good for transitional architectures
- Minimal schema overhead (PostgreSQL handles efficiently)

❌ **Cons:**
- Single point of failure
- Services affect each other
- Complex pool sizing
- Harder to scale individual services
- No foreign keys across schemas

## Decision Matrix

| Factor | Standalone | Library | Shared Pool |
|--------|-----------|---------|-------------|
| **Complexity** | Low | Medium | High |
| **Flexibility** | High | High | Medium |
| **Resource Usage** | High | Varies | Low |
| **Isolation** | Complete | Depends | Schema-only |
| **Scaling** | Independent | Depends | Together |
| **Best For** | Microservices | Packages | Monoliths |

## Common Mistakes to Avoid

### 1. Forgetting {{tables.}} Syntax

❌ **Wrong:**
```sql
CREATE TABLE users (...);
CREATE TABLE orders (
    user_id INT REFERENCES users(id)
);
```

✅ **Right:**
```sql
CREATE TABLE {{tables.users}} (...);
CREATE TABLE {{tables.orders}} (
    user_id INT REFERENCES {{tables.users}}(id)
);
```

### 2. Not Using module_name

❌ **Wrong:**
```python
# All migrations go to default module
migrations = AsyncMigrationManager(db, "./migrations")
```

✅ **Right:**
```python
# Isolated by module name
migrations = AsyncMigrationManager(
    db,
    "./migrations",
    module_name="my_service"
)
```

### 3. Incorrect Library Initialization

❌ **Wrong:**
```python
class MyLibrary:
    async def initialize(self):
        if self._external_db:
            return  # Skip everything!
```

✅ **Right:**
```python
class MyLibrary:
    async def initialize(self):
        # Always run migrations regardless of db source
        migrations = AsyncMigrationManager(...)
        await migrations.apply_pending()
```

### 4. Mixed Schema References

❌ **Wrong:**
```sql
-- Mixing styles causes confusion
CREATE TABLE {{tables.users}} (...);
CREATE TABLE public.audit_log (...);
INSERT INTO myschema.users ...;
```

✅ **Right:**
```sql
-- Consistent use of templates
CREATE TABLE {{tables.users}} (...);
CREATE TABLE {{tables.audit_log}} (...);
INSERT INTO {{tables.users}} ...;
```

## Real-World Example: E-commerce Platform

Here's how an e-commerce platform might use these patterns:

```python
# Main application (Pattern 3: Shared Pool)
class EcommercePlatform:
    async def initialize(self):
        # Shared pool for core services
        self.pool = await AsyncDatabaseManager.create_shared_pool(config)

        # Core services with schema isolation
        catalog_db = AsyncDatabaseManager(pool=self.pool, schema="catalog")
        order_db = AsyncDatabaseManager(pool=self.pool, schema="orders")
        user_db = AsyncDatabaseManager(pool=self.pool, schema="users")

        # Initialize services
        self.catalog = CatalogService(db_manager=catalog_db)
        self.orders = OrderService(db_manager=order_db)
        self.users = UserService(db_manager=user_db)

        # External library (Pattern 2: Reusable Library)
        # This could be memory-service for search
        memory_db = AsyncDatabaseManager(pool=self.pool, schema="memory")
        self.search = MemoryService(db_manager=memory_db)

        # Analytics runs separately (Pattern 1: Standalone)
        # It has its own database for isolation
        self.analytics = AnalyticsService(
            connection_string="postgresql://localhost/analytics"
        )
```

## Framework Integration Example

Here's how to integrate pgdbm with FastAPI using the shared pool pattern:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pgdbm import AsyncDatabaseManager, DatabaseConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create shared pool
    config = DatabaseConfig(
        connection_string="postgresql://localhost/app",
        min_connections=50,
        max_connections=100
    )
    shared_pool = await AsyncDatabaseManager.create_shared_pool(config)

    # Create schema-isolated managers
    app.state.user_db = AsyncDatabaseManager(pool=shared_pool, schema="users")
    app.state.order_db = AsyncDatabaseManager(pool=shared_pool, schema="orders")

    yield

    # Shutdown: Close shared pool
    await shared_pool.close()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await app.state.user_db.fetch_one(
        "SELECT * FROM {{tables.users}} WHERE id = $1",
        user_id
    )
```

This pattern ensures proper resource management and schema isolation for web applications.

## Summary

- **Use Standalone** when services are independent
- **Use Library pattern** when building reusable components
- **Use Shared Pool** when services are tightly coupled
- **Always use {{tables.}}** syntax in migrations
- **Always specify module_name** for migration isolation
- **Libraries should always run their own migrations**

Remember: The pattern you choose affects scalability, resource usage, and operational complexity. Start simple and evolve as needed.
