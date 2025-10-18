"""
Server implementation embedded in package.

This file contains the real server implementation migrated from the repository
top-level `server.py`. It attempts to add the repository `src/` to sys.path
when running in a development checkout (detected by presence of pyproject.toml),
so imports like `tools`, `utils`, and `rag_core_openai` continue to work during
development. When installed as a package, repository files won't be found and
the normal installed packages are used.

Keep this file minimal and prefer relative imports within the package when
refactoring further.
"""

import os
import sys
from datetime import datetime
from urllib.parse import urlparse

# optional runtime dependencies: prefer to import but fall back to safe no-op
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

try:
    from mcp.server.fastmcp import FastMCP
except Exception:
    # Minimal dummy FastMCP to allow import-time stability in environments
    # without the real `mcp` package. The dummy supports `tool` decorator and
    # `run` so code that attaches functions to mcp or calls run won't crash at import.
    class FastMCP:
        def __init__(self, *args, **kwargs):
            self._tools = {}

        def tool(self, *dargs, **dkwargs):
            def decorator(func):
                # store but do not change behavior
                self._tools[func.__name__] = func
                return func
            return decorator

        def run(self, *args, **kwargs):
            # no-op runtime fallback
            return None



def _maybe_add_repo_src():
    """If this code is running from a repository checkout, add repo/src to sys.path.

    This looks for a parent directory containing pyproject.toml and, if found,
    inserts its `src` subdirectory onto sys.path. This preserves developer
    convenience while remaining safe when installed from a wheel.
    """
    cur = os.path.abspath(os.path.dirname(__file__))
    prev = None
    while cur and cur != prev:
        if os.path.isfile(os.path.join(cur, 'pyproject.toml')):
            src_dir = os.path.join(cur, 'src')
            if os.path.isdir(src_dir):
                sys.path.insert(0, os.path.abspath(src_dir))
            break
        prev = cur
        cur = os.path.dirname(cur)


_maybe_add_repo_src()

# 导入工具（在 repo 开发模式下，上面的代码使这些导入可用）
try:
    from utils.logger import log, log_mcp_server
except Exception:
    # minimal fallback logger for import-time stability
    def log(*args, **kwargs):
        print(*args, **kwargs)

    def log_mcp_server(*args, **kwargs):
        print(*args, **kwargs)

try:
    from utils.config import Config
except Exception:
    # minimal Config fallback used only during import/smoke checks
    class Config:
        SERVER_NAME = 'mcp-rag'
        CONVERTED_DOCS_DIR = os.path.join(os.path.abspath('.'), 'converted_docs')

        @staticmethod
        def ensure_directories():
            os.makedirs(Config.CONVERTED_DOCS_DIR, exist_ok=True)

# RAG core functions are imported lazily inside functions to avoid
# forcing heavy external deps (like openai) at import time.
_rag_core = None

def _ensure_rag_core_loaded():
    global _rag_core
    if _rag_core is None:
        try:
            import rag_core_openai as _rc
            _rag_core = _rc
        except Exception:
            _rag_core = None
    return _rag_core

# 导入结构化模型
try:
    from models import DocumentModel, MetadataModel
    MODELS_AVAILABLE = True
    log_mcp_server("✅ 结构化模型 (DocumentModel, MetadataModel) 可用")
except Exception as e:
    MODELS_AVAILABLE = False
    # At this point logger may not be available; fallback to print if necessary
    try:
        log_mcp_server(f"⚠️ 结构化模型不可用: {e}")
    except Exception:
        print(f"⚠️ 结构化模型不可用: {e}")

# --- 初始化服务器和配置 ---
load_dotenv()
mcp = FastMCP(Config.SERVER_NAME)

# 状态现在包括有关结构化模型的信息
rag_state = {
    "models_available": MODELS_AVAILABLE,
    "structured_processing": MODELS_AVAILABLE,
    "document_models": [],  # 已处理的 DocumentModel 列表
    "metadata_cache": {}    # 每个文档的 MetadataModel 缓存
}

md_converter = None


def warm_up_rag_system():
    """
    预加载 RAG 系统的重型组件，以避免首次调用工具时的延迟和冲突。
    """
    if "warmed_up" in rag_state:
        return
    
    try:
        log_mcp_server("正在预热 RAG 系统...")
        log_mcp_server("初始化云端向量存储（OpenAI-only）...")
    except Exception:
        pass
    
    rag_state["warmed_up"] = True
    try:
        log_mcp_server("RAG 系统已预热并准备就绪。")
    except Exception:
        pass


def ensure_converted_docs_directory():
    """确保存在用于存储转换文档的文件夹。"""
    Config.ensure_directories()
    if not os.path.exists(Config.CONVERTED_DOCS_DIR):
        os.makedirs(Config.CONVERTED_DOCS_DIR)
        try:
            log_mcp_server(f"已创建转换文档文件夹: {Config.CONVERTED_DOCS_DIR}")
        except Exception:
            pass


def save_processed_copy(file_path: str, processed_content: str, processing_method: str = "unstructured") -> str:
    """
    保存处理后的文档副本为 Markdown 格式。

    参数：
        file_path: 原始文件路径
        processed_content: 处理后的内容
        processing_method: 使用的处理方法

    返回：
        保存的 Markdown 文件路径
    """
    ensure_converted_docs_directory()
    
    # 获取原始文件名（无扩展名）
    original_filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(original_filename)[0]
    
    # 创建包含方法信息的 Markdown 文件名
    md_filename = f"{name_without_ext}_{processing_method}.md"
    md_filepath = os.path.join(Config.CONVERTED_DOCS_DIR, md_filename)
    
    # 保存内容到 Markdown 文件
    try:
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        try:
            log_mcp_server(f"已保存处理后的副本: {md_filepath}")
        except Exception:
            pass
        return md_filepath
    except Exception as e:
        try:
            log_mcp_server(f"警告: 无法保存处理后的副本: {e}")
        except Exception:
            pass
        return ""


def initialize_rag():
    """
    使用核心初始化 RAG 系统的所有组件。
    """
    if "initialized" in rag_state:
        return

    try:
        log_mcp_server("通过核心初始化 RAG 系统...")
    except Exception:
        pass
    
    # 从云端核心获取向量存储和 QA 链（延后导入以避免 import-time 错误）
    rc = _ensure_rag_core_loaded()
    if rc is None:
        raise RuntimeError("rag_core_openai is unavailable; install optional extras to enable cloud features")
    vector_store = rc.get_vector_store()
    qa_chain = rc.get_qa_chain(vector_store)
    
    rag_state["vector_store"] = vector_store
    rag_state["qa_chain"] = qa_chain
    rag_state["initialized"] = True
    
    # 关于模型状态的信息
    if MODELS_AVAILABLE:
        try:
            log_mcp_server("✅ RAG 系统已初始化，支持结构化模型")
            log_mcp_server("🧠 DocumentModel 和 MetadataModel 可用于高级处理")
        except Exception:
            pass
    else:
        try:
            log_mcp_server("⚠️ RAG 系统已初始化，但未启用结构化模型 (使用字典)")
        except Exception:
            pass
    
    try:
        log_mcp_server("RAG 系统初始化成功。")
    except Exception:
        pass


# --- 注意: 不要在模块导入时自动初始化 RAG 系统 ---
# 初始化（initialize_rag / warm_up_rag_system）应当按需调用，例如在 CLI
# 的 `serve` 子命令或在 `if __name__ == '__main__'` 下调用。自动初始化
# 在缺少可选运行时依赖（openai 等）时会导致导入失败，影响安装和
# 简单的导入检查。

# --- 工具模块的懒配置 ---
def configure_tools():
    """Configure tools' RAG state lazily.

    Call this once during startup (for example from the CLI `serve`
    subcommand) when the runtime dependencies are available.
    """
    try:
        from tools import configure_rag_state, ALL_TOOLS
    except Exception:
        # If tools cannot be imported (missing optional deps), skip configuration.
        return

    try:
        configure_rag_state(
            rag_state=rag_state,
            initialize_rag_func=initialize_rag,
            save_processed_copy_func=save_processed_copy
        )
    except Exception:
        # Best-effort: do not raise during lazy configuration
        pass

# --- Definir las herramientas MCP directamente en el servidor ---
@mcp.tool()
def learn_text(text: str, source_name: str = "manual_input") -> str:
    from tools.document_tools import learn_text as learn_text_logic
    return learn_text_logic(text, source_name)


@mcp.tool()
def learn_document(file_path: str) -> str:
    from tools.document_tools import learn_document as learn_document_logic
    return learn_document_logic(file_path)


@mcp.tool()
def ask_rag(query: str) -> str:
    from tools.search_tools import ask_rag as ask_rag_logic
    return ask_rag_logic(query)


@mcp.tool()
def ask_rag_filtered(query: str, file_type: str = None, min_tables: int = None, min_titles: int = None, processing_method: str = None) -> str:
    from tools.search_tools import ask_rag_filtered as ask_rag_filtered_logic
    return ask_rag_filtered_logic(query, file_type, min_tables, min_titles, processing_method)


@mcp.tool()
def get_knowledge_base_stats() -> str:
    from tools.utility_tools import get_knowledge_base_stats as get_knowledge_base_stats_logic
    return get_knowledge_base_stats_logic()


@mcp.tool()
def get_embedding_cache_stats() -> str:
    from tools.utility_tools import get_embedding_cache_stats as get_embedding_cache_stats_logic
    return get_embedding_cache_stats_logic()


@mcp.tool()
def clear_embedding_cache_tool() -> str:
    from tools.utility_tools import clear_embedding_cache_tool as clear_embedding_cache_tool_logic
    return clear_embedding_cache_tool_logic()


@mcp.tool()
def optimize_vector_database() -> str:
    from tools.utility_tools import optimize_vector_database as optimize_vector_database_logic
    return optimize_vector_database_logic()


@mcp.tool()
def get_vector_database_stats() -> str:
    from tools.utility_tools import get_vector_database_stats as get_vector_database_stats_logic
    return get_vector_database_stats_logic()


@mcp.tool()
def reindex_vector_database(profile: str = 'auto') -> str:
    from tools.utility_tools import reindex_vector_database as reindex_vector_database_logic
    return reindex_vector_database_logic(profile)

# --- 将所有工具函数暴露为 mcp 的方法，方便直接调用（全局作用域，所有函数定义之后） ---
mcp.learn_text = learn_text
mcp.learn_document = learn_document
mcp.ask_rag = ask_rag
mcp.ask_rag_filtered = ask_rag_filtered
mcp.get_knowledge_base_stats = get_knowledge_base_stats
mcp.get_embedding_cache_stats = get_embedding_cache_stats
mcp.clear_embedding_cache_tool = clear_embedding_cache_tool
mcp.optimize_vector_database = optimize_vector_database
mcp.get_vector_database_stats = get_vector_database_stats
mcp.reindex_vector_database = reindex_vector_database

# --- 启动 MCP RAG 服务器 ---
if __name__ == "__main__":
    try:
        log_mcp_server("启动 MCP RAG 服务器...")
    except Exception:
        pass
    warm_up_rag_system()  # 启动时预热系统
    try:
        log_mcp_server("🚀 服务器已启动，运行模式: stdio (如需 Web 服务请设置 host/port)")
    except Exception:
        pass
    # 将所有工具函数暴露为 mcp 的方法，方便直接调用
    mcp.learn_text = learn_text
    mcp.learn_document = learn_document
    mcp.ask_rag = ask_rag
    mcp.ask_rag_filtered = ask_rag_filtered
    mcp.get_knowledge_base_stats = get_knowledge_base_stats
    mcp.get_embedding_cache_stats = get_embedding_cache_stats
    mcp.clear_embedding_cache_tool = clear_embedding_cache_tool
    mcp.optimize_vector_database = optimize_vector_database
    mcp.get_vector_database_stats = get_vector_database_stats
    mcp.reindex_vector_database = reindex_vector_database
    # 如需 Web 服务可改为: mcp.run(host="127.0.0.1", port=8000)
    mcp.run(transport='stdio')
