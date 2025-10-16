import logging, json, os
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp import FastMCP
from fastmcp.prompts.prompt import PromptMessage, TextContent
from agentmake import agentmake, DEVELOPER_MODE, readTextFile
from agentmake.utils.system import getDeviceInfo
from computemate import COMPUTEMATE_VERSION, COMPUTEMATE_PACKAGE_PATH, COMPUTEMATEDATA, AGENTMAKE_CONFIG, config, list_dir_content
from typing import List, Dict, Any, Union
from tabulate import tabulate

# configure backend
AGENTMAKE_CONFIG["backend"] = config.backend

# Configure logging before creating the FastMCP server
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.ERROR)

COMPUTEMATE_STATIC_TOKEN = os.getenv("COMPUTEMATE_STATIC_TOKEN")
COMPUTEMATE_MCP_PUBLIC_KEY = os.getenv("COMPUTEMATE_MCP_PUBLIC_KEY")

verifier = StaticTokenVerifier(
    tokens={
        COMPUTEMATE_STATIC_TOKEN: {
            "client_id": "computemate-ai",
            "scopes": ["read:data", "write:data", "admin:users"]
        },
    },
    required_scopes=["read:data"]
) if COMPUTEMATE_STATIC_TOKEN else JWTVerifier(
    public_key=COMPUTEMATE_MCP_PUBLIC_KEY,
    issuer=os.getenv("COMPUTEMATE_MCP_ISSUER"),
    audience=os.getenv("COMPUTEMATE_MCP_AUDIENCE")
) if COMPUTEMATE_MCP_PUBLIC_KEY else None

mcp = FastMCP(name="ComputeMate AI", auth=verifier)

def getResponse(messages:list) -> str:
    return messages[-1].get("content") if messages and "content" in messages[-1] else "Error!"

@mcp.resource("resource://info")
def info() -> str:
    """Show ComputeMate AI information"""
    info = "ComputeMate AI " + COMPUTEMATE_VERSION
    info += "\n\nSource: https://github.com/eliranwong/computemate\n\nDeveloper: Eliran Wong"
    return info

@mcp.resource("resource://device")
def info() -> str:
    """Show Device Information"""
    return getDeviceInfo()

@mcp.resource("ls://{directory}")
def ls(directory:str) -> str:
    """List content of a directory"""
    return list_dir_content(directory)

@mcp.tool
def execute_task(request:str) -> str:
    """execute computing tasks or retrieve computer information"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'execute_task'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def ask_files(request:str) -> str:
    """ask questions about files content; a file list is required"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'rag/files'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

@mcp.tool
def extract_text(request:str) -> str:
    """extract text from a single file or url; a file path or an url is required"""
    global agentmake, getResponse
    messages = agentmake(request, **{'tool': 'files/extract_text'}, **AGENTMAKE_CONFIG)
    return getResponse(messages)

mcp.run(show_banner=False)