# from fastapi import FastAPI

# app = FastAPI(title="Agent Control Room")

# @app.get("/")
# def root():
#     return {"message": "Agent Control Room is running 🚀"}

# from fastapi import FastAPI
# from .database import engine

# app = FastAPI(title="Agent Control Room")

# @app.get("/")
# def root():
#     try:
#         conn = engine.connect()
#         conn.close()
#         return {"message": "Agent Control Room is running 🚀", "database": "connected ✅"}
#     except Exception as e:
#         return {"message": "DB connection failed ❌", "error": str(e)}
    

# from fastapi import FastAPI
# from .database import engine
# from .models import AgentRun, ToolCall, AgentEvent, Base

# app = FastAPI(title="Agent Control Room")

# @app.on_event("startup")
# def startup():
#     try:
#         Base.metadata.create_all(bind=engine)
#     except Exception as e:
#         print(f"Table creation skipped (tables may already exist): {e}")

# @app.get("/")
# def root():
#     return {"message": "Agent Control Room is running 🚀"}


# from fastapi import FastAPI
# from sqlalchemy import text
# from .database import engine
# from .models import Base
# from .routes.agent_runs import router as runs_router

# app = FastAPI(title="Agent Control Room")

# @app.on_event("startup")
# def startup():
#     try:
#         with engine.begin() as conn:
#             conn.execute(text("CREATE SCHEMA IF NOT EXISTS agentcontrolroom_data"))
#         Base.metadata.create_all(bind=engine)
#     except Exception as e:
#         print(f"Table creation skipped or failed: {e}")

# app.include_router(runs_router)

# @app.get("/")
# def root():
#     return {"message": "Agent Control Room is running 🚀"}

# from fastapi import FastAPI
# from .database import engine
# from .models import Base
# from .routes.agent_runs import router as runs_router
# from .routes.replay import router as replay_router

# app = FastAPI(title="Agent Control Room")

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)

# app.include_router(runs_router)
# app.include_router(replay_router)

# @app.get("/")
# def root():
#     return {"message": "Agent Control Room is running 🚀"}

# from fastapi import FastAPI
# from .database import engine
# from .models import Base
# from .routes.agent_runs import router as runs_router
# from .routes.replay import router as replay_router
# from .routes.quality import router as quality_router

# app = FastAPI(title="Agent Control Room")

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)

# app.include_router(runs_router)
# app.include_router(replay_router)
# app.include_router(quality_router)

# @app.get("/")
# def root():
#     return {"message": "Agent Control Room is running 🚀"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routes.agent_runs import router as runs_router
from routes.replay import router as replay_router
from routes.quality import router as quality_router
from routes.agent import router as agent_router

app = FastAPI(title="Agent Control Room")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(runs_router)
app.include_router(replay_router)
app.include_router(quality_router)
app.include_router(agent_router)

@app.get("/")
def root():
    return {"message": "Agent Control Room is running 🚀"}