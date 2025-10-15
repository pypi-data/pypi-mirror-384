# Anystack

## 项目简介
Anystack 是一个面向云原生应用的 Python 资源抽象层。项目希望通过一组统一的异步协议，包装常见的基础设施能力（数据库、消息队列、对象存储、KV、调度器、实时通道、网关等），降低应用对具体厂商或产品的耦合度，让服务可以在不同环境之间自由迁移。

## 愿景
- 用统一接口使用各种资源
- 消除业务代码与特定基础设施的强绑定
- 让本地开发、云端部署、边缘环境具备一致的编程体验

## 核心特性
- **协议优先**：`src/anystack/protocol` 定义面向数据库、KV、队列、调度器等的最小公共接口。
- **可插拔适配器**：每类资源在 `base.py` 中给出抽象基类，再在子模块内提供具体的实施（如 SQLAlchemy、Cloudflare D1、Supabase 等）。
- **异步优先**：所有适配器都以 `async` 接口暴露，方便在 FastAPI、Starlette 等异步框架中直接使用。
- **类型友好**：广泛使用 Pydantic、类型提示和 `Protocol`，帮助 IDE 和静态检查理解接口契约。
 
## 项目结构
```
src/anystack/
    protocol/        # 统一协议定义
    db/              # 数据库适配器（SQLAlchemy、Cloudflare D1 等）
    storage/         # 基于 OpenDAL 的对象存储实现
    kv/              # KV 抽象与 Redis、Cloudflare KV、PostgreSQL 等实现
    queue/           # 消息队列（AsyncIO、Cloudflare Queue、PGMQ、DB Queue）
    scheduler/       # 调度器抽象与 Supabase 调度实现
    realtime/        # Realtime 通道（Supabase 等）
    gateway/         # Starlette 网关封装
    auth/            # JWT、OAuth 等鉴权能力
    migration/       # 数据库迁移工具
```

## 快速开始
### 环境要求
- Python 3.12+
- 异步运行时（`asyncio`）
- 具体适配器所需的第三方服务/凭证（如 Cloudflare、Supabase、PostgreSQL 等）

### 安装
本地安装推荐使用 [uv](https://github.com/astral-sh/uv)：

```bash
uv pip install anystack
```

也可以使用标准 pip：

```bash
pip install anystack
```

### 最小示例
以下示例演示如何同时使用 SQLAlchemy 数据库适配器和 PostgreSQL PGMQ 队列：

```python
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from anystack.db.sqlalchemy import SQLAlchemyDB, Config as SAConfig
from anystack.queue.pgmq_queue import PGMQueue, Config as QueueConfig

async def main() -> None:
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/app")
    db = SQLAlchemyDB(SAConfig(engine=engine))

    queue = PGMQueue(QueueConfig(db=db, queue_name="jobs"))

    await queue.put({"task": "demo", "payload": {"foo": "bar"}})
    job = await queue.get()
    print(job)

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

要将应用暴露为 ASGI 服务，可以结合 Starlette 路由：

```python
from starlette.responses import JSONResponse

from anystack.gateway.base import PathRoute, ListRouter
from anystack.gateway.starlette_impl import StarletteGateway

async def health(request):
    return JSONResponse({"status": "ok"})

router = ListRouter([
    PathRoute("/health", health, methods=["GET"]),
])

gateway = StarletteGateway(router=router)
app = gateway  # 直接作为 ASGI app 运行
```

## 资源适配器一览
### 数据库
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.db.sqlalchemy.SQLAlchemyDB` | 通用 AsyncEngine 封装，支持事务、连接复用 | `sqlalchemy[asyncio]`
| `anystack.db.d1.D1DB` | 通过 HTTP 与 Cloudflare D1 交互，模拟事务批量提交 | `httpx`, Cloudflare API token |

### 对象存储
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.storage.opendal.OpenDALStorage` | 基于 OpenDAL 的统一对象存储访问，支持多种后端（S3、Supabase Storage、OSS 等） | `opendal` |

### KV 存储
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.kv.redis.RedisKV` | Redis JSON KV，支持键前缀、连接池 | `redis[asyncio]` |
| `anystack.kv.cloudflare_kv.CloudflareKV` | 调用 Cloudflare KV HTTP API | `httpx`, Cloudflare API token |
| `anystack.kv.memory.MemoryKV` | 进程内内存实现，适合本地测试 | 无 |
| `anystack.kv.postgresql.PostgreSQLKV` | 使用关系型数据库持久化 KV | `sqlalchemy`, `asyncpg` |

### 消息队列
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.queue.asyncio_queue.AsyncioQueue` | 基于 `asyncio.PriorityQueue` 的轻量实现 | 内置 |
| `anystack.queue.cloudflare_queue.CloudflareQueue` | Cloudflare Queues API 封装 | `httpx`, Cloudflare API token |
| `anystack.queue.pgmq_queue.PGMQueue` | PostgreSQL PGMQ 扩展适配，支持优先级和 metrics | PostgreSQL, `sqlalchemy`, `asyncpg` |
| `anystack.queue.db_queue.DBQueue` | 纯 SQL 的通用队列，支持优先级和自动建表 | 任意符合 `DB` 协议的适配器 |

### 调度器
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.scheduler.single.supabase.SupabaseScheduler` | 依托 Supabase/PostgreSQL 的任务调度，支持定时、延迟、Cron | `supabase`, `croniter` |
| `anystack.scheduler.single.worker.SingleWorker` | 单实例 worker，负责轮询执行调度任务 | 同上 |

### 实时系统
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.realtime.supabase.SupabaseRealtime` | 封装 Supabase Realtime，支持 broadcast、db changes、presence | `supabase` |

### 网关与应用容器
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.gateway.base.PathRoute` / `ListRouter` | 纯 Python 路由和中间件装配 | `starlette` (用于类型) |
| `anystack.gateway.starlette_impl.StarletteGateway` | 将协议路由映射到 Starlette/ASGI | `starlette`, `uvicorn`(运行时) |

### 鉴权
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.auth.jwt_provider.JWTProvider` | 无状态 JWT 认证，支持自定义用户校验器 | `authlib` |
| `anystack.auth.oauth.github.GitHubOAuthProvider` | GitHub OAuth 登录适配器，可与 JWTProvider 组合 | `authlib`, GitHub OAuth App |
| `anystack.auth.oauth.logto.LogtoOAuthProvider` | Logto OIDC 登录适配器，提供通用用户信息映射 | `authlib`, Logto Cloud 或自托管实例 |
| `anystack.auth.oauth.provider.OAuthAuthProvider` | 直接复用第三方 OAuth Access Token，不再额外颁发 JWT | `authlib` |

### 数据库迁移
| 适配器 | 描述 | 主要依赖 |
| --- | --- | --- |
| `anystack.migration.db.DBMigration` | 基于 SQL 文件的数据库迁移工具，支持版本管理和自动追踪 | 任意符合 `DB` 协议的适配器 |

示例：使用数据库迁移工具管理表结构变更：

```python
from anystack.db.sqlalchemy import SQLAlchemyDB, Config as SAConfig
from anystack.migration.db import DBMigration
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations():
    engine = create_async_engine("sqlite+aiosqlite:///app.db")
    db = SQLAlchemyDB(SAConfig(engine=engine))
    
    # 从目录加载 SQL 迁移文件，或直接传入 MigrationData 列表
    migration = DBMigration(db=db, migration="./migrations", table_name="migrations")
    
    # 执行所有待执行的迁移
    await migration.up()
    
    await db.close()
```

迁移工具会自动创建 `migrations` 表来追踪已执行的版本，只执行未执行过的迁移文件。SQL 文件按文件名排序执行。

---

示例：使用 GitHub OAuth 获取用户信息并颁发内部 JWT：

```python
from starlette.responses import RedirectResponse, JSONResponse

from anystack.auth.jwt_provider import JWTConfig, JWTProvider
from anystack.auth.oauth.github import GitHubOAuthConfig, GitHubOAuthProvider
from anystack.auth.oauth.provider import OAuthAuthProvider

github = GitHubOAuthProvider(
    GitHubOAuthConfig(
        client_id="<client-id>",
        client_secret="<client-secret>",
        redirect_uri="https://example.com/auth/github/callback",
    )
)

jwt_provider = JWTProvider(JWTConfig(secret_key="change-me"))
oauth_provider = OAuthAuthProvider(github)

async def github_login(request):
    url, state = await github.get_authorize_url()
    request.session["github_state"] = state
    return RedirectResponse(url)

async def github_callback(request):
    code = request.query_params["code"]
    state = request.query_params.get("state")
    if state != request.session.pop("github_state", None):
        return JSONResponse({"detail": "state mismatch"}, status_code=400)

    result = await github.authenticate(code=code, state=state)

    if request.query_params.get("mode") == "oauth":
        token = oauth_provider.to_auth_token(result)
        user = result.user
        return JSONResponse({
            "mode": "oauth",
            "user": user.extra | {"id": user.id, "email": user.email},
            "github_token": {
                "access_token": token.access_token,
                "token_type": token.token_type,
            },
        })

    internal_token = await jwt_provider.login({"email": result.user.email, "user_id": result.user.id})
    return JSONResponse({
        "mode": "jwt",
        "user": result.user.extra | {"id": result.user.id, "email": result.user.email},
        "github_token": result.token.raw,
        "internal_token": internal_token.access_token,
    })
```

## 设计理念
1. **Protocol 层** 定义服务与资源的能力边界（如 `DB`, `Queue`, `Storage`）。
2. **Base 层** 在每个子模块内实现可复用的抽象基类，封装公共逻辑。
3. **Adapter 层** 将具体厂商或产品接入，保持最小依赖范围和一致行为。

这种分层让业务代码只依赖协议接口，替换具体实现时不需要改动逻辑；同时方便在测试环境注入内存实现或桩对象。

## 开发与测试
- 克隆仓库后，使用 `uv pip install -e .` 或 `pip install -e .` 安装依赖。
- 建议为需要的第三方服务准备本地或云端实例，例如 PostgreSQL、Redis、Supabase、Cloudflare 等。
- 目前仓库尚未附带统一的自动化测试；编写新适配器时，建议使用 `pytest` 并为协议契约增补测试用例。
- 完成后请运行自测脚本或示例代码，确保接口与协议保持兼容。

## 路线图
- [x] 数据库适配器（SQLAlchemy、Cloudflare D1）
- [x] 存储系统（OpenDAL）
- [x] 认证系统（JWT Provider、GitHub OAuth）
- [x] 消息队列（AsyncIO、Cloudflare Queue、PGMQ、DB Queue）
- [x] 调度系统（Supabase 单实例调度器）
- [x] 实时系统（Supabase Realtime）
- [x] 路由系统 / API 网关（Starlette Gateway）
- [x] 数据库迁移工具（DBMigration）
- [ ] 更多 OAuth 提供商（Google、Discord 等）
- [ ] 更多实时系统适配器
- [ ] 边缘函数 / 边缘执行环境
- [ ] 丰富网关中间件（限流、CORS、日志等）
- [ ] 完善测试覆盖

欢迎在 issues 或 PR 中讨论新的适配器需求与设计建议。

## 贡献
欢迎贡献代码、报告问题或提出建议！在提交 PR 之前，请确保：

1. 代码符合项目的类型提示和异步编程风格
2. 新增适配器遵循协议层定义
3. 添加必要的示例代码和文档说明
4. 保持依赖最小化，可选依赖应在文档中明确说明

## 许可证
本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
