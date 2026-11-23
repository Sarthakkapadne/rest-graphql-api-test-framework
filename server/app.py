"""
Main FastAPI Application combining REST and GraphQL APIs.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from server.rest_routes import router as rest_router
from server.graphql_schema import schema

graphql_app = GraphQLRouter(schema)

app = FastAPI(
    title="eCommerce QA Target API",
    description="Multi-protocol backend service exposing REST endpoints and GraphQL queries/mutations for automated test validation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST routes
app.include_router(rest_router)

# Mount GraphQL router
app.include_router(graphql_app, prefix="/graphql")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="127.0.0.1", port=8000, reload=True)
