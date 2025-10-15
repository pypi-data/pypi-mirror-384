from agentmake import AGENTMAKE_USER_DIR, DEFAULT_TEXT_EDITOR, readTextFile, writeTextFile
from pathlib import Path
from computemate.ui.selection_dialog import TerminalModeDialogs
import os, shutil, pprint

CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.py")
CONFIG_FILE_BACKUP = os.path.join(AGENTMAKE_USER_DIR, "computemate", "config.py")

# NOTE: When add a config item, update both `default_config` and `write_user_config`

# restore config backup after upgrade
default_config = '''banner_title=""
*agent_mode=False
*prompt_engineering=False
*auto_suggestions=True
*max_steps=50
*lite=False
*web_browser=False
*hide_tools_order=True
*skip_connection_check=False
*max_semantic_matches=15
*max_log_lines=2000
*mcp_port=33333
*mcp_timeout=9999999999
*embedding_model="paraphrase-multilingual"
*disabled_tools=[]'''

if readTextFile(CONFIG_FILE).strip() == "":
    just_upgraded = True
    if os.path.isfile(CONFIG_FILE_BACKUP):
        shutil.copy(CONFIG_FILE_BACKUP, CONFIG_FILE)
    else:
        writeTextFile(CONFIG_FILE, default_config.replace("\n*", "\n"))
else:
    just_upgraded = False

from computemate import config

def write_user_config(backup=False):
    """Writes the current configuration to the user's config file."""
    configurations = f"""banner_title="{config.banner_title}"
agent_mode={config.agent_mode}
prompt_engineering={config.prompt_engineering}
auto_suggestions={config.auto_suggestions}
max_steps={config.max_steps}
lite={config.lite}
web_browser={config.web_browser}
hide_tools_order={config.hide_tools_order}
skip_connection_check={config.skip_connection_check}
max_semantic_matches={config.max_semantic_matches}
max_log_lines={config.max_log_lines}
mcp_port={config.mcp_port}
mcp_timeout={config.mcp_timeout}
embedding_model="{config.embedding_model}"
disabled_tools={pprint.pformat(config.disabled_tools)}"""
    writeTextFile(CONFIG_FILE_BACKUP if backup else CONFIG_FILE, configurations)

if just_upgraded:
    changed = False
    for config_item in default_config.split("\n*"):
        key, value = config_item.split("=", 1)
        if not hasattr(config, key):
            exec(f"config.{config_item}", globals())
            changed = True
    if changed:
        write_user_config()

# temporary config
config.current_prompt = ""
config.backup_required = False
config.export_item = ""
config.action_list = {
    # general
    ".ideas": "generate ideas for prompts to try",
    ".exit": "exit current prompt",
    # conversations
    ".new": "new conversation",
    ".trim": "trim conversation",
    ".edit": "edit conversation",
    ".reload": "reload conversation",
    ".import": "import conversation",
    ".export": "export conversation",
    ".backup": "backup conversation",
    ".find": "search conversation",
    # resource information
    ".tools": "list available tools",
    ".plans": "list available plans",
    ".resources": "list available resources",
    # configurations
    ".backend": "configure backend",
    ".mcp": "configure MCP servers",
    ".steps": "configure the maximum number of steps allowed",
    ".matches": "configure the maximum number of semantic matches",
    ".mode": "configure AI mode",
    #".agent": "switch to agent mode",
    #".partner": "switch to partner mode",
    #".chat": "switch to chat mode",
    ".autosuggestions": "toggle auto input suggestions",
    ".promptengineer": "toggle auto prompt engineering",
    ".lite": "toggle lite context",
    # file access
    ".open": "open file or folder",
    #".download": "download data files",
    # help
    ".help": "help page",
}

# copy etextedit plugins
ETEXTEDIT_USER_PULGIN_DIR = os.path.join(os.path.expanduser("~"), "etextedit", "plugins")
if not os.path.isdir(ETEXTEDIT_USER_PULGIN_DIR):
    Path(ETEXTEDIT_USER_PULGIN_DIR).mkdir(parents=True, exist_ok=True)
COMPUTEMATE_ETEXTEDIT_PLUGINS = os.path.join(os.path.dirname(os.path.realpath(__file__)), "etextedit", "plugins")
for file_name in os.listdir(COMPUTEMATE_ETEXTEDIT_PLUGINS):
    full_file_name = os.path.join(COMPUTEMATE_ETEXTEDIT_PLUGINS, file_name)
    if file_name.endswith(".py") and os.path.isfile(full_file_name) and not os.path.isfile(os.path.join(ETEXTEDIT_USER_PULGIN_DIR, file_name)):
        shutil.copy(full_file_name, ETEXTEDIT_USER_PULGIN_DIR)

# constants
AGENTMAKE_CONFIG = {
    "print_on_terminal": False,
    "word_wrap": False,
}
OLLAMA_NOT_FOUND = "`Ollama` is not found! ComputeMate AI uses `Ollama` to generate embeddings for semantic searches. You may install it from https://ollama.com/ so that you can perform semantic searches with ComputeMate AI."
COMPUTEMATE_VERSION = readTextFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt"))
COMPUTEMATE_PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
COMPUTEMATE_USER_DIR = os.path.join(AGENTMAKE_USER_DIR, "computemate")
COMPUTEMATEDATA = os.path.join(AGENTMAKE_USER_DIR, "computemate", "data")
if not os.path.isdir(COMPUTEMATEDATA):
    Path(COMPUTEMATEDATA).mkdir(parents=True, exist_ok=True)
DIALOGS = TerminalModeDialogs()

def fix_string(content):
    return content.replace(" ", " ").replace("‑", "-")

def get_mcp_config_file():
    user_mcp_config = os.path.join(COMPUTEMATE_USER_DIR, "mcp_configurations.py")
    return user_mcp_config if os.path.isfile(user_mcp_config) else os.path.join(COMPUTEMATE_PACKAGE_PATH, "mcp_configurations.py")

def edit_mcp_config_file(mcp_config_file=""):
    if not mcp_config_file:
        mcp_config_file = os.path.join(COMPUTEMATE_USER_DIR, "mcp_configurations.py")
        if not os.path.isfile(mcp_config_file):
            shutil.copy(os.path.join(COMPUTEMATE_PACKAGE_PATH, "mcp_configurations.py"), mcp_config_file)
    os.system(f'''{DEFAULT_TEXT_EDITOR} "{mcp_config_file}"''')