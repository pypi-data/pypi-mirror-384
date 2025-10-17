
from colorama import Fore, Back, Style
from dataclasses import dataclass, field
import filecmp
import os
from pathlib import Path
import platform
try:
    import pty
    import tty
    
    import termios

    import readline
except:
    readline = None
    pty = None
    tty = None

import re
import select
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from typing import Dict, List,  Any, Tuple, Union, Optional
import logging
import textwrap
from termcolor import colored
from npcpy.memory.command_history import (
    start_new_conversation,
)
from npcpy.npc_compiler import NPC, Team


from npcpy.memory.command_history import CommandHistory



import os
import sys
import atexit
import subprocess
import shlex
import re
from datetime import datetime
import importlib.metadata
import textwrap
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
import platform
try:
    from termcolor import colored
except: 
    pass

try:
    import chromadb
except ImportError:
    chromadb = None
import shutil
import sqlite3
import yaml


from npcpy.npc_sysenv import (
    print_and_process_stream_with_markdown,
    render_markdown,
    get_model_and_provider, 
    get_locally_available_models,
    lookup_provider
)

from npcpy.memory.command_history import (
    CommandHistory,
    save_conversation_message,
    load_kg_from_db, 
    save_kg_to_db, 
)
from npcpy.npc_compiler import NPC, Team, load_jinxs_from_directory
from npcpy.llm_funcs import (
    check_llm_command,
    get_llm_response,
    execute_llm_command,
    breathe, 
    
)
from npcpy.memory.knowledge_graph import (
    kg_evolve_incremental, 
    
)
from npcpy.gen.embeddings import get_embeddings

try:
    import readline
except:
    print('no readline support, some features may not work as desired. ')

try:
    VERSION = importlib.metadata.version("npcsh")
except importlib.metadata.PackageNotFoundError:
    VERSION = "unknown"




NPCSH_CHAT_MODEL = os.environ.get("NPCSH_CHAT_MODEL", "gemma3:4b")

NPCSH_CHAT_PROVIDER = os.environ.get("NPCSH_CHAT_PROVIDER", "ollama")

NPCSH_DB_PATH = os.path.expanduser(
    os.environ.get("NPCSH_DB_PATH", "~/npcsh_history.db")
)
NPCSH_VECTOR_DB_PATH = os.path.expanduser(
    os.environ.get("NPCSH_VECTOR_DB_PATH", "~/npcsh_chroma.db")
)


NPCSH_DEFAULT_MODE = os.path.expanduser(os.environ.get("NPCSH_DEFAULT_MODE", "agent"))
NPCSH_VISION_MODEL = os.environ.get("NPCSH_VISION_MODEL", "gemma3:4b")
NPCSH_VISION_PROVIDER = os.environ.get("NPCSH_VISION_PROVIDER", "ollama")
NPCSH_IMAGE_GEN_MODEL = os.environ.get(
    "NPCSH_IMAGE_GEN_MODEL", "runwayml/stable-diffusion-v1-5"
)
NPCSH_IMAGE_GEN_PROVIDER = os.environ.get("NPCSH_IMAGE_GEN_PROVIDER", "diffusers")
NPCSH_VIDEO_GEN_MODEL = os.environ.get(
    "NPCSH_VIDEO_GEN_MODEL", "damo-vilab/text-to-video-ms-1.7b"
)
NPCSH_VIDEO_GEN_PROVIDER = os.environ.get("NPCSH_VIDEO_GEN_PROVIDER", "diffusers")

NPCSH_EMBEDDING_MODEL = os.environ.get("NPCSH_EMBEDDING_MODEL", "nomic-embed-text")
NPCSH_EMBEDDING_PROVIDER = os.environ.get("NPCSH_EMBEDDING_PROVIDER", "ollama")
NPCSH_REASONING_MODEL = os.environ.get("NPCSH_REASONING_MODEL", "deepseek-r1")
NPCSH_REASONING_PROVIDER = os.environ.get("NPCSH_REASONING_PROVIDER", "ollama")
NPCSH_STREAM_OUTPUT = eval(os.environ.get("NPCSH_STREAM_OUTPUT", "0")) == 1
NPCSH_API_URL = os.environ.get("NPCSH_API_URL", None)
NPCSH_SEARCH_PROVIDER = os.environ.get("NPCSH_SEARCH_PROVIDER", "duckduckgo")
NPCSH_BUILD_KG = os.environ.get("NPCSH_BUILD_KG") == "1" 
READLINE_HISTORY_FILE = os.path.expanduser("~/.npcsh_history")



@dataclass
class ShellState:
    npc: Optional[Union[NPC, str]] = None
    team: Optional[Team] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    mcp_client: Optional[Any] = None
    conversation_id: Optional[int] = None
    chat_model: str = NPCSH_CHAT_MODEL
    chat_provider: str = NPCSH_CHAT_PROVIDER
    vision_model: str = NPCSH_VISION_MODEL
    vision_provider: str = NPCSH_VISION_PROVIDER
    embedding_model: str = NPCSH_EMBEDDING_MODEL
    embedding_provider: str = NPCSH_EMBEDDING_PROVIDER
    reasoning_model: str = NPCSH_REASONING_MODEL
    reasoning_provider: str = NPCSH_REASONING_PROVIDER
    search_provider: str = NPCSH_SEARCH_PROVIDER
    image_gen_model: str = NPCSH_IMAGE_GEN_MODEL
    image_gen_provider: str = NPCSH_IMAGE_GEN_PROVIDER
    video_gen_model: str = NPCSH_VIDEO_GEN_MODEL
    video_gen_provider: str = NPCSH_VIDEO_GEN_PROVIDER
    current_mode: str = NPCSH_DEFAULT_MODE
    build_kg: bool = NPCSH_BUILD_KG
    api_key: Optional[str] = None
    api_url: Optional[str] = NPCSH_API_URL
    current_path: str = field(default_factory=os.getcwd)
    stream_output: bool = NPCSH_STREAM_OUTPUT
    attachments: Optional[List[Any]] = None
    turn_count: int =0
    def get_model_for_command(self, model_type: str = "chat"):
        if model_type == "chat":
            return self.chat_model, self.chat_provider
        elif model_type == "vision":
            return self.vision_model, self.vision_provider
        elif model_type == "embedding":
            return self.embedding_model, self.embedding_provider
        elif model_type == "reasoning":
            return self.reasoning_model, self.reasoning_provider
        elif model_type == "image_gen":
            return self.image_gen_model, self.image_gen_provider
        elif model_type == "video_gen":
            return self.video_gen_model, self.video_gen_provider
        else:
            return self.chat_model, self.chat_provider 
CONFIG_KEY_MAP = {
  
    "model": "NPCSH_CHAT_MODEL",
    "chatmodel": "NPCSH_CHAT_MODEL",
    "provider": "NPCSH_CHAT_PROVIDER",
    "chatprovider": "NPCSH_CHAT_PROVIDER",

  
    "vmodel": "NPCSH_VISION_MODEL",
    "visionmodel": "NPCSH_VISION_MODEL",
    "vprovider": "NPCSH_VISION_PROVIDER",
    "visionprovider": "NPCSH_VISION_PROVIDER",

  
    "emodel": "NPCSH_EMBEDDING_MODEL",
    "embeddingmodel": "NPCSH_EMBEDDING_MODEL",
    "eprovider": "NPCSH_EMBEDDING_PROVIDER",
    "embeddingprovider": "NPCSH_EMBEDDING_PROVIDER",

  
    "rmodel": "NPCSH_REASONING_MODEL",
    "reasoningmodel": "NPCSH_REASONING_MODEL",
    "rprovider": "NPCSH_REASONING_PROVIDER",
    "reasoningprovider": "NPCSH_REASONING_PROVIDER",

  
    "igmodel": "NPCSH_IMAGE_GEN_MODEL",
    "imagegenmodel": "NPCSH_IMAGE_GEN_MODEL",
    "igprovider": "NPCSH_IMAGE_GEN_PROVIDER",
    "imagegenprovider": "NPCSH_IMAGE_GEN_PROVIDER",

  
    "vgmodel": "NPCSH_VIDEO_GEN_MODEL",
    "videogenmodel": "NPCSH_VIDEO_GEN_MODEL",
    "vgprovider": "NPCSH_VIDEO_GEN_PROVIDER",
    "videogenprovider": "NPCSH_VIDEO_GEN_PROVIDER",

  
    "sprovider": "NPCSH_SEARCH_PROVIDER",
    "mode": "NPCSH_DEFAULT_MODE",
    "stream": "NPCSH_STREAM_OUTPUT",
    "apiurl": "NPCSH_API_URL",
    "buildkg": "NPCSH_BUILD_KG",
}


def set_npcsh_config_value(key: str, value: str):
    """
    Set NPCSH config values at runtime using shorthand (case-insensitive) or full keys.
    Updates os.environ, globals, and ShellState defaults.
    """
  
    env_key = CONFIG_KEY_MAP.get(key.lower(), key)

  
    os.environ[env_key] = value

  
    if env_key in ["NPCSH_STREAM_OUTPUT", "NPCSH_BUILD_KG"]:
        parsed_val = value.strip().lower() in ["1", "true", "yes"]
    elif env_key.endswith("_PATH"):
        parsed_val = os.path.expanduser(value)
    else:
        parsed_val = value

  
    globals()[env_key] = parsed_val

  
    field_map = {
        "NPCSH_CHAT_MODEL": "chat_model",
        "NPCSH_CHAT_PROVIDER": "chat_provider",
        "NPCSH_VISION_MODEL": "vision_model",
        "NPCSH_VISION_PROVIDER": "vision_provider",
        "NPCSH_EMBEDDING_MODEL": "embedding_model",
        "NPCSH_EMBEDDING_PROVIDER": "embedding_provider",
        "NPCSH_REASONING_MODEL": "reasoning_model",
        "NPCSH_REASONING_PROVIDER": "reasoning_provider",
        "NPCSH_SEARCH_PROVIDER": "search_provider",
        "NPCSH_IMAGE_GEN_MODEL": "image_gen_model",
        "NPCSH_IMAGE_GEN_PROVIDER": "image_gen_provider",
        "NPCSH_VIDEO_GEN_MODEL": "video_gen_model",
        "NPCSH_VIDEO_GEN_PROVIDER": "video_gen_provider",
        "NPCSH_DEFAULT_MODE": "current_mode",
        "NPCSH_BUILD_KG": "build_kg",
        "NPCSH_API_URL": "api_url",
        "NPCSH_STREAM_OUTPUT": "stream_output",
    }
    if env_key in field_map:
        setattr(ShellState, field_map[env_key], parsed_val)
def get_npc_path(npc_name: str, db_path: str) -> str:
    project_npc_team_dir = os.path.abspath("./npc_team")
    project_npc_path = os.path.join(project_npc_team_dir, f"{npc_name}.npc")
    user_npc_team_dir = os.path.expanduser("~/.npcsh/npc_team")
    global_npc_path = os.path.join(user_npc_team_dir, f"{npc_name}.npc")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            query = f"SELECT source_path FROM compiled_npcs WHERE name = '{npc_name}'"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                return result[0]

    except Exception as e:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                query = f"SELECT source_path FROM compiled_npcs WHERE name = {npc_name}"
                cursor.execute(query)
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            print(f"Database query error: {e}")

  
    if os.path.exists(project_npc_path):
        return project_npc_path

    if os.path.exists(global_npc_path):
        return global_npc_path

    raise ValueError(f"NPC file not found: {npc_name}")


def initialize_base_npcs_if_needed(db_path: str) -> None:
    """
    Function Description:
        This function initializes the base NPCs if they are not already in the database.
    Args:
        db_path: The path to the database file.
    Keyword Args:

        None
    Returns:
        None
    """

    if is_npcsh_initialized():
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

  
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS compiled_npcs (
            name TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            compiled_content TEXT
        )
        """
    )

  
    package_dir = os.path.dirname(__file__)
    package_npc_team_dir = os.path.join(package_dir, "npc_team")

    user_npc_team_dir = os.path.expanduser("~/.npcsh/npc_team")

    user_jinxs_dir = os.path.join(user_npc_team_dir, "jinxs")
    user_templates_dir = os.path.join(user_npc_team_dir, "templates")
    os.makedirs(user_npc_team_dir, exist_ok=True)
    os.makedirs(user_jinxs_dir, exist_ok=True)
    os.makedirs(user_templates_dir, exist_ok=True)

    for filename in os.listdir(package_npc_team_dir):
        if filename.endswith(".npc"):
            source_path = os.path.join(package_npc_team_dir, filename)
            destination_path = os.path.join(user_npc_team_dir, filename)
            if not os.path.exists(destination_path) or file_has_changed(
                source_path, destination_path
            ):
                shutil.copy2(source_path, destination_path)
                print(f"Copied NPC {filename} to {destination_path}")
        if filename.endswith(".ctx"):
            source_path = os.path.join(package_npc_team_dir, filename)
            destination_path = os.path.join(user_npc_team_dir, filename)
            if not os.path.exists(destination_path) or file_has_changed(
                source_path, destination_path
            ):
                shutil.copy2(source_path, destination_path)
                print(f"Copied ctx {filename} to {destination_path}")

  
    package_jinxs_dir = os.path.join(package_npc_team_dir, "jinxs")
    if os.path.exists(package_jinxs_dir):
        for filename in os.listdir(package_jinxs_dir):
            if filename.endswith(".jinx"):
                source_jinx_path = os.path.join(package_jinxs_dir, filename)
                destination_jinx_path = os.path.join(user_jinxs_dir, filename)
                if (not os.path.exists(destination_jinx_path)) or file_has_changed(
                    source_jinx_path, destination_jinx_path
                ):
                    shutil.copy2(source_jinx_path, destination_jinx_path)
                    print(f"Copied jinx {filename} to {destination_jinx_path}")

    templates = os.path.join(package_npc_team_dir, "templates")
    if os.path.exists(templates):
        for folder in os.listdir(templates):
            os.makedirs(os.path.join(user_templates_dir, folder), exist_ok=True)
            for file in os.listdir(os.path.join(templates, folder)):
                if file.endswith(".npc"):
                    source_template_path = os.path.join(templates, folder, file)

                    destination_template_path = os.path.join(
                        user_templates_dir, folder, file
                    )
                    if not os.path.exists(
                        destination_template_path
                    ) or file_has_changed(
                        source_template_path, destination_template_path
                    ):
                        shutil.copy2(source_template_path, destination_template_path)
                        print(f"Copied template {file} to {destination_template_path}")
    conn.commit()
    conn.close()
    set_npcsh_initialized()
    add_npcshrc_to_shell_config()

def get_shell_config_file() -> str:
    """

    Function Description:
        This function returns the path to the shell configuration file.
    Args:
        None
    Keyword Args:
        None
    Returns:
        The path to the shell configuration file.
    """
  
    shell = os.environ.get("SHELL", "")

    if "zsh" in shell:
        return os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
      
        if platform.system() == "Darwin":
            return os.path.expanduser("~/.bash_profile")
        else:
            return os.path.expanduser("~/.bashrc")
    else:
      
        return os.path.expanduser("~/.bashrc")


def get_team_ctx_path(team_path: str) -> Optional[str]:
    """Find the first .ctx file in the team directory"""
    team_dir = Path(team_path)
    ctx_files = list(team_dir.glob("*.ctx"))
    return str(ctx_files[0]) if ctx_files else None


def add_npcshrc_to_shell_config() -> None:
    """
    Function Description:
        This function adds the sourcing of the .npcshrc file to the user's shell configuration file.
    Args:
        None
    Keyword Args:
        None
    Returns:
        None
    """

    if os.getenv("NPCSH_INITIALIZED") is not None:
        return
    config_file = get_shell_config_file()
    npcshrc_line = "\n# Source NPCSH configuration\nif [ -f ~/.npcshrc ]; then\n    . ~/.npcshrc\nfi\n"

    with open(config_file, "a+") as shell_config:
        shell_config.seek(0)
        content = shell_config.read()
        if "source ~/.npcshrc" not in content and ". ~/.npcshrc" not in content:
            shell_config.write(npcshrc_line)
            print(f"Added .npcshrc sourcing to {config_file}")
        else:
            print(f".npcshrc already sourced in {config_file}")

def ensure_npcshrc_exists() -> str:
    """
    Function Description:
        This function ensures that the .npcshrc file exists in the user's home directory.
    Args:
        None
    Keyword Args:
        None
    Returns:
        The path to the .npcshrc file.
    """

    npcshrc_path = os.path.expanduser("~/.npcshrc")
    if not os.path.exists(npcshrc_path):
        with open(npcshrc_path, "w") as npcshrc:
            npcshrc.write("# NPCSH Configuration File\n")
            npcshrc.write("export NPCSH_INITIALIZED=0\n")
            npcshrc.write("export NPCSH_DEFAULT_MODE='agent'\n")
            npcshrc.write("export NPCSH_BUILD_KG=1")
            npcshrc.write("export NPCSH_CHAT_PROVIDER='ollama'\n")
            npcshrc.write("export NPCSH_CHAT_MODEL='gemma3:4b'\n")
            npcshrc.write("export NPCSH_REASONING_PROVIDER='ollama'\n")
            npcshrc.write("export NPCSH_REASONING_MODEL='deepseek-r1'\n")
            npcshrc.write("export NPCSH_EMBEDDING_PROVIDER='ollama'\n")
            npcshrc.write("export NPCSH_EMBEDDING_MODEL='nomic-embed-text'\n")
            npcshrc.write("export NPCSH_VISION_PROVIDER='ollama'\n")
            npcshrc.write("export NPCSH_VISION_MODEL='llava7b'\n")
            npcshrc.write(
                "export NPCSH_IMAGE_GEN_MODEL='runwayml/stable-diffusion-v1-5'\n"
            )

            npcshrc.write("export NPCSH_IMAGE_GEN_PROVIDER='diffusers'\n")
            npcshrc.write(
                "export NPCSH_VIDEO_GEN_MODEL='runwayml/stable-diffusion-v1-5'\n"
            )

            npcshrc.write("export NPCSH_VIDEO_GEN_PROVIDER='diffusers'\n")

            npcshrc.write("export NPCSH_API_URL=''\n")
            npcshrc.write("export NPCSH_DB_PATH='~/npcsh_history.db'\n")
            npcshrc.write("export NPCSH_VECTOR_DB_PATH='~/npcsh_chroma.db'\n")
            npcshrc.write("export NPCSH_STREAM_OUTPUT=0")
    return npcshrc_path



def setup_npcsh_config() -> None:
    """
    Function Description:
        This function initializes the NPCSH configuration.
    Args:
        None
    Keyword Args:
        None
    Returns:
        None
    """

    ensure_npcshrc_exists()
    add_npcshrc_to_shell_config()



CANONICAL_ARGS = [
    'model',            
    'provider',         
    'output_file',           
    'attachments',     
    'format',    
    'temperature',
    'top_k',
    'top_p',
    'max_tokens',
    'messages',    
    'npc',
    'team',
    'height',
    'width',
    'num_frames',
    'sprovider',
    'emodel',
    'eprovider',
    'igmodel',
    'igprovider',
    'vmodel',
    'vprovider',
    'rmodel',
    'rprovider',
    'num_npcs',
    'depth',
    'exploration',
    'creativity',
    'port',
    'cors',
    'config_dir',
    'plots_dir',
    'refresh_period',
    'lang',
]

def get_argument_help() -> Dict[str, List[str]]:
    """
    Analyzes CANONICAL_ARGS to generate a map of canonical arguments
    to all their possible shorthands.
    
    Returns -> {'model': ['m', 'mo', 'mod', 'mode'], 'provider': ['p', 'pr', ...]}
    """
    arg_map = {arg: [] for arg in CANONICAL_ARGS}
    
    for arg in CANONICAL_ARGS:
      
        for i in range(1, len(arg)):
            prefix = arg[:i]
            
          
            matches = [canonical for canonical in CANONICAL_ARGS if canonical.startswith(prefix)]
            
          
            if len(matches) == 1 and matches[0] == arg:
                arg_map[arg].append(prefix)

    return arg_map




def normalize_and_expand_flags(parsed_flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expands argument aliases based on the priority order of CANONICAL_ARGS.
    The first matching prefix in the list wins.
    """
    normalized = {}
    for key, value in parsed_flags.items():
        if key in CANONICAL_ARGS:
            if key in normalized:
                print(colored(f"Warning: Argument '{key}' specified multiple times. Using last value.", "yellow"))
            normalized[key] = value
            continue
        first_match = next((arg for arg in CANONICAL_ARGS if arg.startswith(key)), None)
        if first_match:
            if first_match in normalized:
                print(colored(f"Warning: Argument '{first_match}' specified multiple times (via alias '{key}'). Using last value.", "yellow"))
            normalized[first_match] = value
        else:
            normalized[key] = value
    return normalized


BASH_COMMANDS = [
    "npc",
    "npm",
    "npx",
    "open",
    "alias",
    "bg",
    "bind",
    "break",
    "builtin",
    "case",
    "command",
    "compgen",
    "complete",
    "continue",
    "declare",
    "dirs",
    "disown",
    "echo",
    "enable",
    "eval",
    "exec",
    "exit",
    "export",
    "fc",
    "fg",
    "getopts",
    "hash",
    "history",
    "if",
    "jobs",
    "kill",
    "let",
    "local",
    "logout",
    "ollama",
    "popd",
    "printf",
    "pushd",
    "pwd",
    "read",
    "readonly",
    "return",
    "set",
    "shift",
    "shopt",
    "source",
    "suspend",
    "test",
    "times",
    "trap",
    "type",
    "typeset",
    "ulimit",
    "umask",
    "unalias",
    "unset",
    "until",
    "wait",
    "while",
  
    "ls",
    "cp",
    "mv",
    "rm",
    "mkdir",
    "rmdir",
    "touch",
    "cat",
    "less",
    "more",
    "head",
    "tail",
    "grep",
    "find",
    "sed",
    "awk",
    "sort",
    "uniq",
    "wc",
    "diff",
    "chmod",
    "chown",
    "chgrp",
    "ln",
    "tar",
    "gzip",
    "gunzip",
    "zip",
    "unzip",
    "ssh",
    "scp",
    "rsync",
    "wget",
    "curl",
    "ping",
    "netstat",
    "ifconfig",
    "route",
    "traceroute",
    "ps",
    "top",
    "htop",
    "kill",
    "killall",
    "su",
    "sudo",
    "whoami",
    "who",
    "last",
    "finger",
    "uptime",
    "free",
    "df",
    "du",
    "mount",
    "umount",
    "fdisk",
    "mkfs",
    "fsck",
    "dd",
    "cron",
    "at",
    "systemctl",
    "service",
    "journalctl",
    "man",
    "info",
    "whatis",
    "whereis",
    "date",
    "cal",
    "bc",
    "expr",
    "screen",
    "tmux",
    "git",
    "vim",
    "emacs",
    "nano",
    "pip",
]


interactive_commands = {
    "ipython": ["ipython"],
    "python": ["python", "-i"],
    "sqlite3": ["sqlite3"],
    "r": ["R", "--interactive"],
}


def start_interactive_session(command: str) -> int:
    """
    Starts an interactive session. Only works on Unix. On Windows, print a message and return 1.
    """
    ON_WINDOWS = platform.system().lower().startswith("win")
    if ON_WINDOWS or termios is None or tty is None or pty is None or select is None or signal is None or tty is None:
        print("Interactive terminal sessions are not supported on Windows.")
        return 1
  
    old_tty = termios.tcgetattr(sys.stdin)
    try:
      
        master_fd, slave_fd = pty.openpty()

      
        p = subprocess.Popen(
            command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            shell=True,
            preexec_fn=os.setsid,
        )

      
        tty.setraw(sys.stdin.fileno())

        def handle_timeout(signum, frame):
            raise TimeoutError("Process did not terminate in time")

        while p.poll() is None:
            r, w, e = select.select([sys.stdin, master_fd], [], [], 0.1)
            if sys.stdin in r:
                d = os.read(sys.stdin.fileno(), 10240)
                os.write(master_fd, d)
            elif master_fd in r:
                o = os.read(master_fd, 10240)
                if o:
                    os.write(sys.stdout.fileno(), o)
                else:
                    break

      
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(5)
        try:
            p.wait()
        except TimeoutError:
            print("\nProcess did not terminate. Force killing...")
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            time.sleep(1)
            if p.poll() is None:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        finally:
            signal.alarm(0)

    finally:
      
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_tty)

    return p.returncode

def validate_bash_command(command_parts: list) -> bool:
    """
    Function Description:
        Validate if the command sequence is a valid bash command with proper arguments/flags.
    Args:
        command_parts : list : Command parts
    Keyword Args:
        None
    Returns:
        bool : bool : Boolean
    """
    if not command_parts:
        return False

    COMMAND_PATTERNS = {
        "cat": {
            "flags": ["-n", "-b", "-E", "-T", "-s", "--number", "-A", "--show-all"],
            "requires_arg": True,
        },
        "find": {
            "flags": [
                "-name",
                "-type",
                "-size",
                "-mtime",
                "-exec",
                "-print",
                "-delete",
                "-maxdepth",
                "-mindepth",
                "-perm",
                "-user",
                "-group",
            ],
            "requires_arg": True,
        },
        "who": {
            "flags": [
                "-a",
                "-b",
                "-d",
                "-H",
                "-l",
                "-p",
                "-q",
                "-r",
                "-s",
                "-t",
                "-u",
                "--all",
                "--count",
                "--heading",
            ],
            "requires_arg": False,
        },
        "open": {
            "flags": ["-a", "-e", "-t", "-f", "-F", "-W", "-n", "-g", "-h"],
            "requires_arg": True,
        },
        "ls": {
            "flags": [
                "-a",
                "-l",
                "-h",
                "-R",
                "-t",
                "-S",
                "-r",
                "-d",
                "-F",
                "-i",
                "--color",
            ],
            "requires_arg": False,
        },
        "cp": {
            "flags": [
                "-r",
                "-f",
                "-i",
                "-u",
                "-v",
                "--preserve",
                "--no-preserve=mode,ownership,timestamps",
            ],
            "requires_arg": True,
        },
        "mv": {
            "flags": ["-f", "-i", "-u", "-v", "--backup", "--no-clobber"],
            "requires_arg": True,
        },
        "rm": {
            "flags": ["-f", "-i", "-r", "-v", "--preserve-root", "--no-preserve-root"],
            "requires_arg": True,
        },
        "mkdir": {
            "flags": ["-p", "-v", "-m", "--mode", "--parents"],
            "requires_arg": True,
        },
        "rmdir": {
            "flags": ["-p", "-v", "--ignore-fail-on-non-empty"],
            "requires_arg": True,
        },
        "touch": {
            "flags": ["-a", "-c", "-m", "-r", "-d", "--date"],
            "requires_arg": True,
        },
        "grep": {
            "flags": [
                "-i",
                "-v",
                "-r",
                "-l",
                "-n",
                "-c",
                "-w",
                "-x",
                "--color",
                "--exclude",
                "--include",
            ],
            "requires_arg": True,
        },
        "sed": {
            "flags": [
                "-e",
                "-f",
                "-i",
                "-n",
                "--expression",
                "--file",
                "--in-place",
                "--quiet",
                "--silent",
            ],
            "requires_arg": True,
        },
        "awk": {
            "flags": [
                "-f",
                "-v",
                "--file",
                "--source",
                "--assign",
                "--posix",
                "--traditional",
            ],
            "requires_arg": True,
        },
        "sort": {
            "flags": [
                "-b",
                "-d",
                "-f",
                "-g",
                "-i",
                "-n",
                "-r",
                "-u",
                "--check",
                "--ignore-case",
                "--numeric-sort",
            ],
            "requires_arg": False,
        },
        "uniq": {
            "flags": ["-c", "-d", "-u", "-i", "--check-chars", "--skip-chars"],
            "requires_arg": False,
        },
        "wc": {
            "flags": ["-c", "-l", "-w", "-m", "-L", "--bytes", "--lines", "--words"],
            "requires_arg": False,
        },
        "pwd": {
            "flags": ["-L", "-P"],
            "requires_arg": False,
        },
        "chmod": {
            "flags": ["-R", "-v", "-c", "--reference"],
            "requires_arg": True,
        },

    }

    base_command = command_parts[0]

    if base_command == 'which':
        return False 


  
    INTERACTIVE_COMMANDS = ["ipython", "python", "sqlite3", "r"]
    TERMINAL_EDITORS = ["vim", "nano", "emacs"]
    if base_command in TERMINAL_EDITORS or base_command in INTERACTIVE_COMMANDS:
        return True

    if base_command not in COMMAND_PATTERNS and base_command not in BASH_COMMANDS:
        return False 

    pattern = COMMAND_PATTERNS.get(base_command)
    if not pattern:
        return True

    args = []
    flags = []

    for i in range(1, len(command_parts)):
        part = command_parts[i]
        if part.startswith("-"):
            flags.append(part)
            if part not in pattern["flags"]:
                return False
        else:
            args.append(part)

  
    if base_command == "who" and args:
        return False
  
    if pattern.get("requires_arg", False) and not args:
        return False

    return True


def is_npcsh_initialized() -> bool:
    """
    Function Description:
        This function checks if the NPCSH initialization flag is set.
    Args:
        None
    Keyword Args:
        None
    Returns:
        A boolean indicating whether NPCSH is initialized.
    """

    return os.environ.get("NPCSH_INITIALIZED", None) == "1"


def execute_set_command(command: str, value: str) -> str:
    """
    Function Description:
        This function sets a configuration value in the .npcshrc file.
    Args:
        command: The command to execute.
        value: The value to set.
    Keyword Args:
        None
    Returns:
        A message indicating the success or failure of the operation.
    """

    config_path = os.path.expanduser("~/.npcshrc")

  
    var_map = {
        "model": "NPCSH_CHAT_MODEL",
        "provider": "NPCSH_CHAT_PROVIDER",
        "db_path": "NPCSH_DB_PATH",
    }

    if command not in var_map:
        return f"Unknown setting: {command}"

    env_var = var_map[command]

  
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []

  
    property_exists = False
    for i, line in enumerate(lines):
        if line.startswith(f"export {env_var}="):
            lines[i] = f"export {env_var}='{value}'\n"
            property_exists = True
            break

    if not property_exists:
        lines.append(f"export {env_var}='{value}'\n")

  
    with open(config_path, "w") as f:
        f.writelines(lines)

    return f"{command.capitalize()} has been set to: {value}"


def set_npcsh_initialized() -> None:
    """
    Function Description:
        This function sets the NPCSH initialization flag in the .npcshrc file.
    Args:
        None
    Keyword Args:
        None
    Returns:

        None
    """

    npcshrc_path = ensure_npcshrc_exists()

    with open(npcshrc_path, "r+") as npcshrc:
        content = npcshrc.read()
        if "export NPCSH_INITIALIZED=0" in content:
            content = content.replace(
                "export NPCSH_INITIALIZED=0", "export NPCSH_INITIALIZED=1"
            )
            npcshrc.seek(0)
            npcshrc.write(content)
            npcshrc.truncate()

  
    os.environ["NPCSH_INITIALIZED"] = "1"
    print("NPCSH initialization flag set in .npcshrc")



def file_has_changed(source_path: str, destination_path: str) -> bool:
    """
    Function Description:
        This function compares two files to determine if they are different.
    Args:
        source_path: The path to the source file.
        destination_path: The path to the destination file.
    Keyword Args:
        None
    Returns:
        A boolean indicating whether the files are different
    """

  
    return not filecmp.cmp(source_path, destination_path, shallow=False)


def list_directory(args: List[str]) -> None:
    """
    Function Description:
        This function lists the contents of a directory.
    Args:
        args: The command arguments.
    Keyword Args:
        None
    Returns:
        None
    """
    directory = args[0] if args else "."
    try:
        files = os.listdir(directory)
        for f in files:
            print(f)
    except Exception as e:
        print(f"Error listing directory: {e}")



def change_directory(command_parts: list, messages: list) -> dict:
    """
    Function Description:
        Changes the current directory.
    Args:
        command_parts : list : Command parts
        messages : list : Messages
    Keyword Args:
        None
    Returns:
        dict : dict : Dictionary

    """

    try:
        if len(command_parts) > 1:
            new_dir = os.path.expanduser(command_parts[1])
        else:
            new_dir = os.path.expanduser("~")
        os.chdir(new_dir)
        return {
            "messages": messages,
            "output": f"Changed directory to {os.getcwd()}",
        }
    except FileNotFoundError:
        return {
            "messages": messages,
            "output": f"Directory not found: {new_dir}",
        }
    except PermissionError:
        return {"messages": messages, "output": f"Permission denied: {new_dir}"}


def orange(text: str) -> str:
    """
    Function Description:
        Returns orange text.
    Args:
        text : str : Text
    Keyword Args:
        None
    Returns:
        text : str : Text

    """
    return f"\033[38;2;255;165;0m{text}{Style.RESET_ALL}"


def get_npcshrc_path_windows():
    return Path.home() / ".npcshrc"


def read_rc_file_windows(path):
    """Read shell-style rc file"""
    config = {}
    if not path.exists():
        return config

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
              
                match = re.match(r'^([A-Z_]+)\s*=\s*[\'"](.*?)[\'"]$', line)
                if match:
                    key, value = match.groups()
                    config[key] = value
    return config


def get_setting_windows(key, default=None):
  
    if env_value := os.getenv(key):
        return env_value

  
    config = read_rc_file_windows(get_npcshrc_path_windows())
    return config.get(key, default)


def setup_readline() -> str:
    import readline
    if readline is None:
        return None
    try:
        readline.read_history_file(READLINE_HISTORY_FILE)
        readline.set_history_length(1000)
        readline.parse_and_bind("set enable-bracketed-paste on")
        readline.parse_and_bind(r'"\e[A": history-search-backward')
        readline.parse_and_bind(r'"\e[B": history-search-forward')
        readline.parse_and_bind(r'"\C-r": reverse-search-history')
        readline.parse_and_bind(r'\C-e: end-of-line')
        readline.parse_and_bind(r'\C-a: beginning-of-line')
        if sys.platform == "darwin":
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        return READLINE_HISTORY_FILE
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"Warning: Could not read readline history file {READLINE_HISTORY_FILE}: {e}")

def save_readline_history():
    if readline is None:
        return
    try:
        readline.write_history_file(READLINE_HISTORY_FILE)
    except OSError as e:
        print(f"Warning: Could not write readline history file {READLINE_HISTORY_FILE}: {e}")



TERMINAL_EDITORS = ["vim", "emacs", "nano"]
EMBEDDINGS_DB_PATH = os.path.expanduser("~/npcsh_chroma.db")
HISTORY_DB_DEFAULT_PATH = os.path.expanduser("~/npcsh_history.db")
READLINE_HISTORY_FILE = os.path.expanduser("~/.npcsh_readline_history")
DEFAULT_NPC_TEAM_PATH = os.path.expanduser("~/.npcsh/npc_team/")
PROJECT_NPC_TEAM_PATH = "./npc_team/"


try:
    chroma_client = chromadb.PersistentClient(path=EMBEDDINGS_DB_PATH) if chromadb else None
except Exception as e:
    print(f"Warning: Failed to initialize ChromaDB client at {EMBEDDINGS_DB_PATH}: {e}")
    chroma_client = None




def get_path_executables() -> List[str]:
    """Get executables from PATH (cached for performance)"""
    if not hasattr(get_path_executables, '_cache'):
        executables = set()
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for path_dir in path_dirs:
            if os.path.isdir(path_dir):
                try:
                    for item in os.listdir(path_dir):
                        item_path = os.path.join(path_dir, item)
                        if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                            executables.add(item)
                except (PermissionError, OSError):
                    continue
        get_path_executables._cache = sorted(list(executables))
    return get_path_executables._cache


import logging


completion_logger = logging.getLogger('npcsh.completion')
completion_logger.setLevel(logging.WARNING)


if not completion_logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(name)s] %(message)s')
    handler.setFormatter(formatter)
    completion_logger.addHandler(handler)

def make_completer(shell_state: ShellState, router: Any):
    def complete(text: str, state_index: int) -> Optional[str]:
        """Main completion function"""
        try:
            buffer = readline.get_line_buffer()
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            
            completion_logger.debug(f"text='{text}', buffer='{buffer}', begidx={begidx}, endidx={endidx}, state_index={state_index}")
            
            matches = []
            
          
            if begidx > 0 and buffer[begidx-1] == '/':
                completion_logger.debug(f"Slash command completion - text='{text}'")
                slash_commands = get_slash_commands(shell_state, router)
                completion_logger.debug(f"Available slash commands: {slash_commands}")
                
                if text == '':
                    matches = [cmd[1:] for cmd in slash_commands]
                else:
                    full_text = '/' + text
                    matching_commands = [cmd for cmd in slash_commands if cmd.startswith(full_text)]
                    matches = [cmd[1:] for cmd in matching_commands]
                
                completion_logger.debug(f"Slash command matches: {matches}")
                
            elif is_command_position(buffer, begidx):
                completion_logger.debug("Command position detected")
                bash_matches = [cmd for cmd in BASH_COMMANDS if cmd.startswith(text)]
                matches.extend(bash_matches)
                
                interactive_matches = [cmd for cmd in interactive_commands.keys() if cmd.startswith(text)]
                matches.extend(interactive_matches)
                
                if len(text) >= 1:
                    path_executables = get_path_executables()
                    exec_matches = [cmd for cmd in path_executables if cmd.startswith(text)]
                    matches.extend(exec_matches[:20])
            else:
                completion_logger.debug("File completion")
                matches = get_file_completions(text)
            
            matches = sorted(list(set(matches)))
            completion_logger.debug(f"Final matches: {matches}")
            
            if state_index < len(matches):
                result = matches[state_index]
                completion_logger.debug(f"Returning: '{result}'")
                return result
            else:
                completion_logger.debug(f"No match for state_index {state_index}")
            
        except Exception as e:
            completion_logger.error(f"Exception in completion: {e}")
            completion_logger.debug("Exception details:", exc_info=True)
        
        return None
    
    return complete

def get_slash_commands(state: ShellState, router: Any) -> List[str]:
    """Get available slash commands from the provided router and team"""
    commands = []
    
    if router and hasattr(router, 'routes'):
        router_cmds = [f"/{cmd}" for cmd in router.routes.keys()]
        commands.extend(router_cmds)
        completion_logger.debug(f"Router commands: {router_cmds}")
    
  
    if state.team and hasattr(state.team, 'jinxs_dict'):
        jinx_cmds = [f"/{jinx}" for jinx in state.team.jinxs_dict.keys()]
        commands.extend(jinx_cmds)
        completion_logger.debug(f"Jinx commands: {jinx_cmds}")
    
  
    if state.team and hasattr(state.team, 'npcs'):
        npc_cmds = [f"/{npc}" for npc in state.team.npcs.keys()]
        commands.extend(npc_cmds)
        completion_logger.debug(f"NPC commands: {npc_cmds}")
    
  
    mode_cmds = ['/cmd', '/agent', '/chat']
    commands.extend(mode_cmds)
    completion_logger.debug(f"Mode commands: {mode_cmds}")
    
    result = sorted(commands)
    completion_logger.debug(f"Final slash commands: {result}")
    return result
def get_file_completions(text: str) -> List[str]:
    """Get file/directory completions"""
    try:
        if text.startswith('/'):
            basedir = os.path.dirname(text) or '/'
            prefix = os.path.basename(text)
        elif text.startswith('./') or text.startswith('../'):
            basedir = os.path.dirname(text) or '.'
            prefix = os.path.basename(text)
        else:
            basedir = '.'
            prefix = text
        
        if not os.path.exists(basedir):
            return []
        
        matches = []
        try:
            for item in os.listdir(basedir):
                if item.startswith(prefix):
                    full_path = os.path.join(basedir, item)
                    if basedir == '.':
                        completion = item
                    else:
                        completion = os.path.join(basedir, item)
                    
                  
                    matches.append(completion)
        except (PermissionError, OSError):
            pass
        
        return sorted(matches)
    except Exception:
        return []
def is_command_position(buffer: str, begidx: int) -> bool:
    """Determine if cursor is at a command position"""
  
    before_word = buffer[:begidx]
    
  
    parts = re.split(r'[|;&]', before_word)
    current_command_part = parts[-1].strip()
    
  
  
    return len(current_command_part) == 0


def readline_safe_prompt(prompt: str) -> str:
    ansi_escape = re.compile(r"(\033\[[0-9;]*[a-zA-Z])")
    return ansi_escape.sub(r"\001\1\002", prompt)

def print_jinxs(jinxs):
    output = "Available jinxs:\n"
    for jinx in jinxs:
        output += f"  {jinx.jinx_name}\n"
        output += f"   Description: {jinx.description}\n"
        output += f"   Inputs: {jinx.inputs}\n"
    return output

def open_terminal_editor(command: str) -> str:
    try:
        os.system(command)
        return 'Terminal editor closed.'
    except Exception as e:
        return f"Error opening terminal editor: {e}"

def get_multiline_input(prompt: str) -> str:
    lines = []
    current_prompt = prompt
    while True:
        try:
            line = input(current_prompt)
            if line.endswith("\\"):
                lines.append(line[:-1])
                current_prompt = readline_safe_prompt("> ")
            else:
                lines.append(line)
                break
        except EOFError:
            print("Goodbye!")
            sys.exit(0)
    return "\n".join(lines)

def split_by_pipes(command: str) -> List[str]:
    parts = []
    current = ""
    in_single_quote = False
    in_double_quote = False
    escape = False

    for char in command:
        if escape:
            current += char
            escape = False
        elif char == '\\':
            escape = True
            current += char
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current += char
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_single_quote
            current += char
        elif char == '|' and not in_single_quote and not in_double_quote:
            parts.append(current.strip())
            current = ""
        else:
            current += char

    if current:
        parts.append(current.strip())
    return parts

def parse_command_safely(cmd: str) -> List[str]:
    try:
        return shlex.split(cmd)
    except ValueError as e:
        if "No closing quotation" in str(e):
            if cmd.count('"') % 2 == 1:
                cmd += '"'
            elif cmd.count("'") % 2 == 1:
                cmd += "'"
            try:
                return shlex.split(cmd)
            except ValueError:
                return cmd.split()
        else:
            return cmd.split()

def get_file_color(filepath: str) -> tuple:
    if not os.path.exists(filepath):
         return "grey", []
    if os.path.isdir(filepath):
        return "blue", ["bold"]
    elif os.access(filepath, os.X_OK) and not os.path.isdir(filepath):
        return "green", ["bold"]
    elif filepath.endswith((".zip", ".tar", ".gz", ".bz2", ".xz", ".7z")):
        return "red", []
    elif filepath.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")):
        return "magenta", []
    elif filepath.endswith((".py", ".pyw")):
        return "yellow", []
    elif filepath.endswith((".sh", ".bash", ".zsh")):
        return "green", []
    elif filepath.endswith((".c", ".cpp", ".h", ".hpp")):
        return "cyan", []
    elif filepath.endswith((".js", ".ts", ".jsx", ".tsx")):
        return "yellow", []
    elif filepath.endswith((".html", ".css", ".scss", ".sass")):
        return "magenta", []
    elif filepath.endswith((".md", ".txt", ".log")):
        return "white", []
    elif os.path.basename(filepath).startswith("."):
        return "cyan", []
    else:
        return "white", []

def format_file_listing(output: str) -> str:
    colored_lines = []
    current_dir = os.getcwd()
    for line in output.strip().split("\n"):
        parts = line.split()
        if not parts:
            colored_lines.append(line)
            continue

        filepath_guess = parts[-1]
        potential_path = os.path.join(current_dir, filepath_guess)

        color, attrs = get_file_color(potential_path)
        colored_filepath = colored(filepath_guess, color, attrs=attrs)

        if len(parts) > 1 :
           
             colored_line = " ".join(parts[:-1] + [colored_filepath])
        else:
           
             colored_line = colored_filepath

        colored_lines.append(colored_line)

    return "\n".join(colored_lines)

def wrap_text(text: str, width: int = 80) -> str:
    lines = []
    for paragraph in text.split("\n"):
        if len(paragraph) > width:
             lines.extend(textwrap.wrap(paragraph, width=width, replace_whitespace=False, drop_whitespace=False))
        else:
             lines.append(paragraph)
    return "\n".join(lines)



def setup_readline() -> str:
    """Setup readline with history and completion"""
    try:
        readline.read_history_file(READLINE_HISTORY_FILE)
        readline.set_history_length(1000)
        
      
        readline.parse_and_bind("tab: complete")
        
        readline.parse_and_bind("set enable-bracketed-paste on")
        readline.parse_and_bind(r'"\C-r": reverse-search-history')
        readline.parse_and_bind(r'"\C-e": end-of-line')
        readline.parse_and_bind(r'"\C-a": beginning-of-line')
        
        return READLINE_HISTORY_FILE
        
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"Warning: Could not read readline history file {READLINE_HISTORY_FILE}: {e}")


def save_readline_history():
    try:
        readline.write_history_file(READLINE_HISTORY_FILE)
    except OSError as e:
        print(f"Warning: Could not write readline history file {READLINE_HISTORY_FILE}: {e}")
        
def store_command_embeddings(command: str, output: Any, state: ShellState):
    if not chroma_client or not state.embedding_model or not state.embedding_provider:
        if not chroma_client: print("Warning: ChromaDB client not available for embeddings.", file=sys.stderr)
        return
    if not command and not output:
        return

    try:
        output_str = str(output) if output else ""
        if not command and not output_str: return 

        texts_to_embed = [command, output_str]

        embeddings = get_embeddings(
            texts_to_embed,
            state.embedding_model,
            state.embedding_provider,
        )

        if not embeddings or len(embeddings) != 2:
             print(f"Warning: Failed to generate embeddings for command: {command[:50]}...", file=sys.stderr)
             return

        timestamp = datetime.now().isoformat()
        npc_name = state.npc.name if isinstance(state.npc, NPC) else state.npc

        metadata = [
            {
                "type": "command", "timestamp": timestamp, "path": state.current_path,
                "npc": npc_name, "conversation_id": state.conversation_id,
            },
            {
                "type": "response", "timestamp": timestamp, "path": state.current_path,
                "npc": npc_name, "conversation_id": state.conversation_id,
            },
        ]

        collection_name = f"{state.embedding_provider}_{state.embedding_model}_embeddings"
        try:
            collection = chroma_client.get_or_create_collection(collection_name)
            ids = [f"cmd_{timestamp}_{hash(command)}", f"resp_{timestamp}_{hash(output_str)}"]

            collection.add(
                embeddings=embeddings,
                documents=texts_to_embed,
                metadatas=metadata,
                ids=ids,
            )
        except Exception as e:
            print(f"Warning: Failed to add embeddings to collection '{collection_name}': {e}", file=sys.stderr)

    except Exception as e:
        print(f"Warning: Failed to store embeddings: {e}", file=sys.stderr)


def handle_interactive_command(cmd_parts: List[str], state: ShellState) -> Tuple[ShellState, str]:
    command_name = cmd_parts[0]
    print(f"Starting interactive {command_name} session...")
    try:
      
        full_command_str = " ".join(cmd_parts)
        return_code = start_interactive_session(full_command_str)
        output = f"Interactive {command_name} session ended with return code {return_code}"
    except Exception as e:
        output = f"Error starting interactive session {command_name}: {e}"
    return state, output

def handle_cd_command(cmd_parts: List[str], state: ShellState) -> Tuple[ShellState, str]:
    original_path = os.getcwd()
    target_path = cmd_parts[1] if len(cmd_parts) > 1 else os.path.expanduser("~")
    try:
        os.chdir(target_path)
        state.current_path = os.getcwd()
        output = f"Changed directory to {state.current_path}"
    except FileNotFoundError:
        output = colored(f"cd: no such file or directory: {target_path}", "red")
    except Exception as e:
        output = colored(f"cd: error changing directory: {e}", "red")
        os.chdir(original_path) 

    return state, output


def handle_bash_command(
    cmd_parts: List[str],
    cmd_str: str,
    stdin_input: Optional[str],
    state: ShellState,
) -> Tuple[bool, str]:
    try:
        process = subprocess.Popen(
            cmd_parts,
            stdin=subprocess.PIPE if stdin_input is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=state.current_path
        )
        stdout, stderr = process.communicate(input=stdin_input)

        if process.returncode != 0:
            return False, stderr.strip() if stderr else f"Command '{cmd_str}' failed with return code {process.returncode}."

        if stderr.strip():
            print(colored(f"stderr: {stderr.strip()}", "yellow"), file=sys.stderr)
        
        if cmd_parts[0] in ["ls", "find", "dir"]:
            return True, format_file_listing(stdout.strip())

        return True, stdout.strip()

    except FileNotFoundError:
        return False, f"Command not found: {cmd_parts[0]}"
    except PermissionError:
        return False, f"Permission denied: {cmd_str}"

def _try_convert_type(value: str) -> Union[str, int, float, bool]:
    """Helper to convert string values to appropriate types."""
    if value.lower() in ['true', 'yes']:
        return True
    if value.lower() in ['false', 'no']:
        return False
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    return value

def parse_generic_command_flags(parts: List[str]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parses a list of command parts into a dictionary of keyword arguments and a list of positional arguments.
    Handles: -f val, --flag val, --flag=val, flag=val, --boolean-flag
    """
    parsed_kwargs = {}
    positional_args = []
    i = 0
    while i < len(parts):
        part = parts[i]
        
        if part.startswith('--'):
            key_part = part[2:]
            if '=' in key_part:
                key, value = key_part.split('=', 1)
                parsed_kwargs[key] = _try_convert_type(value)
            else:
              
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    parsed_kwargs[key_part] = _try_convert_type(parts[i + 1])
                    i += 1 
                else:
                    parsed_kwargs[key_part] = True 
        
        elif part.startswith('-'):
            key = part[1:]
          
            if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                parsed_kwargs[key] = _try_convert_type(parts[i + 1])
                i += 1 
            else:
                parsed_kwargs[key] = True 
        
        elif '=' in part and not part.startswith('-'):
             key, value = part.split('=', 1)
             parsed_kwargs[key] = _try_convert_type(value)
        
        else:
            positional_args.append(part)
        
        i += 1
        
    return parsed_kwargs, positional_args


def should_skip_kg_processing(user_input: str, assistant_output: str) -> bool:
    """Determine if this interaction is too trivial for KG processing"""
    
  
    if len(user_input.strip()) < 10:
        return True
    
    simple_bash = {'ls', 'pwd', 'cd', 'mkdir', 'touch', 'rm', 'mv', 'cp'}
    first_word = user_input.strip().split()[0] if user_input.strip() else ""
    if first_word in simple_bash:
        return True
    
    if len(assistant_output.strip()) < 20:
        return True
    
    if "exiting" in assistant_output.lower() or "exited" in assistant_output.lower():
        return True
    
    return False




def execute_slash_command(command: str, 
                          stdin_input: Optional[str], 
                          state: ShellState, 
                          stream: bool, 
                          router) -> Tuple[ShellState, Any]:
    """Executes slash commands using the router or checking NPC/Team jinxs."""
    all_command_parts = shlex.split(command)
    command_name = all_command_parts[0].lstrip('/')
    
    if command_name in ['n', 'npc']:
        npc_to_switch_to = all_command_parts[1] if len(all_command_parts) > 1 else None
        if npc_to_switch_to and state.team and npc_to_switch_to in state.team.npcs:
            state.npc = state.team.npcs[npc_to_switch_to]
            return state, {"output": f"Switched to NPC: {npc_to_switch_to}", "messages": state.messages}
        else:
            available_npcs = list(state.team.npcs.keys()) if state.team else []
            return state, {"output": colored(f"NPC '{npc_to_switch_to}' not found. Available NPCs: {', '.join(available_npcs)}", "red"), "messages": state.messages}
    
    handler = router.get_route(command_name)
    if handler:
        parsed_flags, positional_args = parse_generic_command_flags(all_command_parts[1:])
        normalized_flags = normalize_and_expand_flags(parsed_flags)

        handler_kwargs = {
            'stream': stream,
            'team': state.team,
            'messages': state.messages,
            'api_url': state.api_url,
            'api_key': state.api_key,
            'stdin_input': stdin_input,
            'positional_args': positional_args,
            'plonk_context': state.team.shared_context.get('PLONK_CONTEXT') if state.team and hasattr(state.team, 'shared_context') else None,
            
            'model': state.npc.model if isinstance(state.npc, NPC) and state.npc.model else state.chat_model,
            'provider': state.npc.provider if isinstance(state.npc, NPC) and state.npc.provider else state.chat_provider,
            'npc': state.npc,
            
            'sprovider': state.search_provider,
            'emodel': state.embedding_model,
            'eprovider': state.embedding_provider,
            'igmodel': state.image_gen_model,
            'igprovider': state.image_gen_provider,
            'vgmodel': state.video_gen_model, 
            'vgprovider': state.video_gen_provider,
            'vmodel': state.vision_model,
            'vprovider': state.vision_provider,
            'rmodel': state.reasoning_model,
            'rprovider': state.reasoning_provider,
        }
        
        if len(normalized_flags) > 0:
            kwarg_part = 'with kwargs: \n    -' + '\n    -'.join(f'{key}={item}' for key, item in normalized_flags.items())
        else:
            kwarg_part = ''

        render_markdown(f'- Calling {command_name} handler {kwarg_part} ')
        
        if 'model' in normalized_flags and 'provider' not in normalized_flags:
            inferred_provider = lookup_provider(normalized_flags['model'])
            if inferred_provider:
                handler_kwargs['provider'] = inferred_provider
                print(colored(f"Info: Inferred provider '{inferred_provider}' for model '{normalized_flags['model']}'.", "cyan"))
        
        if 'provider' in normalized_flags and 'model' not in normalized_flags:
            current_provider = lookup_provider(handler_kwargs['model'])
            if current_provider != normalized_flags['provider']:
                prov = normalized_flags['provider']
                print(f'Please specify a model for the provider: {prov}')
        
        handler_kwargs.update(normalized_flags)
        
        try:
            result = handler(command=command, **handler_kwargs)
            
            if isinstance(result, dict):
                state.messages = result.get("messages", state.messages)
                return state, result
            elif isinstance(result, str):
                return state, {"output": result, "messages": state.messages}
            else:
                return state, {"output": str(result), "messages": state.messages}
                
        except Exception as e:
            import traceback
            print(f"Error executing slash command '{command_name}':", file=sys.stderr)
            traceback.print_exc()
            return state, {"output": colored(f"Error executing slash command '{command_name}': {e}", "red"), "messages": state.messages}

    active_npc = state.npc if isinstance(state.npc, NPC) else None
    jinx_to_execute = None
    executor = None
    
    if active_npc and hasattr(active_npc, 'jinxs_dict') and command_name in active_npc.jinxs_dict:
        jinx_to_execute = active_npc.jinxs_dict[command_name]
        executor = active_npc
    elif state.team and hasattr(state.team, 'jinxs_dict') and command_name in state.team.jinxs_dict:
        jinx_to_execute = state.team.jinxs_dict[command_name]
        executor = state.team
    if jinx_to_execute:
        args = all_command_parts[1:]
        try:
            input_values = {}
            if hasattr(jinx_to_execute, 'inputs') and jinx_to_execute.inputs:
                for i, input_name in enumerate(jinx_to_execute.inputs):
                    if i < len(args):
                        input_values[input_name] = args[i]
            
            if isinstance(executor, NPC):
                jinx_output = jinx_to_execute.execute(
                    input_values=input_values,
                    jinxs_dict=executor.jinxs_dict if hasattr(executor, 'jinxs_dict') else {},
                    npc=executor,
                    messages=state.messages
                )
            else:
                jinx_output = jinx_to_execute.execute(
                    input_values=input_values,
                    jinxs_dict=executor.jinxs_dict if hasattr(executor, 'jinxs_dict') else {},
                    npc=active_npc or state.npc,
                    messages=state.messages
                )
            if isinstance(jinx_output, dict) and 'messages' in jinx_output:
                state.messages = jinx_output['messages']
                return state, jinx_output
            elif isinstance(jinx_output, dict):
                return state, jinx_output
            else:
                return state, {"output": str(jinx_output), "messages": state.messages}
            
        except Exception as e:
            import traceback
            print(f"Error executing jinx '{command_name}':", file=sys.stderr)
            traceback.print_exc()
            return state, {"output": colored(f"Error executing jinx '{command_name}': {e}", "red"), "messages": state.messages}
    
    if state.team and command_name in state.team.npcs:
        new_npc = state.team.npcs[command_name]
        state.npc = new_npc
        return state, {"output": f"Switched to NPC: {new_npc.name}", "messages": state.messages}

    return state, {"output": colored(f"Unknown slash command, jinx, or NPC: {command_name}", "red"), "messages": state.messages}


def process_pipeline_command(
    cmd_segment: str,
    stdin_input: Optional[str],
    state: ShellState,
    stream_final: bool, 
    review = False, 
    router = None,
    ) -> Tuple[ShellState, Any]:
    '''
    Processing command 
    '''

    if not cmd_segment:
        return state, stdin_input

    available_models_all = get_locally_available_models(state.current_path)
    available_models_all_list = [item for key, item in available_models_all.items()]

    model_override, provider_override, cmd_cleaned = get_model_and_provider(
        cmd_segment, available_models_all_list
    )
    cmd_to_process = cmd_cleaned.strip()
    if not cmd_to_process:
         return state, stdin_input

    npc_model = state.npc.model if isinstance(state.npc, NPC) and state.npc.model else None
    npc_provider = state.npc.provider if isinstance(state.npc, NPC) and state.npc.provider else None

    exec_model = model_override or npc_model or state.chat_model
    exec_provider = provider_override or npc_provider or state.chat_provider

    if cmd_to_process.startswith("/"):
        return execute_slash_command(cmd_to_process, 
                                     stdin_input, 
                                     state, 
                                     stream_final, 
                                     router)
    
    cmd_parts = parse_command_safely(cmd_to_process)
    if not cmd_parts:
        return state, stdin_input

    command_name = cmd_parts[0]

    if command_name == "cd":
        return handle_cd_command(cmd_parts, state)
    
    if command_name in interactive_commands:
        return handle_interactive_command(cmd_parts, state)
    if command_name in TERMINAL_EDITORS:
        print(f"Starting interactive editor: {command_name}...")
        full_command_str = " ".join(cmd_parts)
        output = open_terminal_editor(full_command_str)
        return state, output

    if validate_bash_command(cmd_parts):
        success, result = handle_bash_command(cmd_parts, cmd_to_process, stdin_input, state)
        if success:
            return state, result
        else:
            print(colored(f"Bash command failed: {result}. Asking LLM for a fix...", "yellow"), file=sys.stderr)
            fixer_prompt = f"The command '{cmd_to_process}' failed with the error: '{result}'. Provide the correct command."
            response = execute_llm_command(
                fixer_prompt, 
                model=exec_model,
                provider=exec_provider,
                npc=state.npc, 
                stream=stream_final, 
                messages=state.messages
            )
            state.messages = response['messages']     
            return state, response['response']
    else:
        full_llm_cmd = f"{cmd_to_process} {stdin_input}" if stdin_input else cmd_to_process
        path_cmd = 'The current working directory is: ' + state.current_path
        ls_files = 'Files in the current directory (full paths):\n' + "\n".join([os.path.join(state.current_path, f) for f in os.listdir(state.current_path)]) if os.path.exists(state.current_path) else 'No files found in the current directory.'
        platform_info = f"Platform: {platform.system()} {platform.release()} ({platform.machine()})"
        info = path_cmd + '\n' + ls_files + '\n' + platform_info + '\n' 
        state.messages.append({'role':'user', 'content':full_llm_cmd})
        
        
        llm_result = check_llm_command(
            full_llm_cmd,
            model=exec_model,      
            provider=exec_provider, 
            api_url=state.api_url,
            api_key=state.api_key,
            npc=state.npc,
            team=state.team,
            messages=state.messages,
            images=state.attachments,
            stream=stream_final,
            context=info,
        )
      
        
        if not review:
            if isinstance(llm_result, dict):
                state.messages = llm_result.get("messages", state.messages)
                output = llm_result.get("output")
                return state, output
            else:
                return state, llm_result        
            
        else:
            return review_and_iterate_command(
                original_command=full_llm_cmd,
                initial_result=llm_result,
                state=state,
                exec_model=exec_model,
                exec_provider=exec_provider,
                stream_final=stream_final,
                info=info
            )
def review_and_iterate_command(
    original_command: str,
    initial_result: Any,
    state: ShellState,
    exec_model: str,
    exec_provider: str,
    stream_final: bool,
    info: str,
    max_iterations: int = 2
) -> Tuple[ShellState, Any]:
    """
    Simple iteration on LLM command result to improve quality.
    """
    
  
    if isinstance(initial_result, dict):
        current_output = initial_result.get("output")
        current_messages = initial_result.get("messages", state.messages)
    else:
        current_output = initial_result
        current_messages = state.messages
    
  
    refinement_prompt = f"""
The previous response to "{original_command}" was:
{current_output}

Please review and improve this response if needed. Provide a better, more complete answer.
"""
    
  
    refined_result = check_llm_command(
        refinement_prompt,
        model=exec_model,      
        provider=exec_provider, 
        api_url=state.api_url,
        api_key=state.api_key,
        npc=state.npc,
        team=state.team,
        messages=current_messages,
        images=state.attachments,
        stream=stream_final,
        context=info,
    )
    
  
    if isinstance(refined_result, dict):
        state.messages = refined_result.get("messages", current_messages)
        return state, refined_result.get("output", current_output)
    else:
        state.messages = current_messages
        return state, refined_result
def check_mode_switch(command:str , state: ShellState):
    if command in ['/cmd', '/agent', '/chat',]:
        state.current_mode = command[1:]
        return True, state     
    return False, state

def execute_command(
    command: str,
    state: ShellState,
    review = False, 
    router = None,
    command_history = None,
    ) -> Tuple[ShellState, Any]:

    if not command.strip():
        return state, ""
    
    mode_change, state = check_mode_switch(command, state)
    if mode_change:
        return state, 'Mode changed.'

    npc_name = state.npc.name if isinstance(state.npc, NPC) else "__none__"
    team_name = state.team.name if state.team else "__none__"
    

    original_command_for_embedding = command
    commands = split_by_pipes(command)

    stdin_for_next = None
    final_output = None
    current_state = state 
    npc_model = state.npc.model if isinstance(state.npc, NPC) and state.npc.model else None
    npc_provider = state.npc.provider if isinstance(state.npc, NPC) and state.npc.provider else None
    active_model = npc_model or state.chat_model
    active_provider = npc_provider or state.chat_provider
    if state.current_mode == 'agent':
      
      
        for i, cmd_segment in enumerate(commands):
            render_markdown(f'- Executing command {i+1}/{len(commands)}')
            is_last_command = (i == len(commands) - 1)
            stream_this_segment = state.stream_output and not is_last_command 
            try:
                current_state, output = process_pipeline_command(
                    cmd_segment.strip(),
                    stdin_for_next,
                    current_state, 
                    stream_final=stream_this_segment, 
                    review=review,
                    router= router
                )
                if is_last_command:
                    return current_state, output
                if isinstance(output, str):
                    stdin_for_next = output
                elif not isinstance(output, str):
                    try:
                        if stream_this_segment:
                            full_stream_output = print_and_process_stream_with_markdown(output, 
                                                                                        state.npc.model, 
                                                                                        state.npc.provider, 
                                                                                        show=True)
                            stdin_for_next = full_stream_output
                            if is_last_command: 
                                final_output = full_stream_output
                    except:
                        if output is not None:  
                            try: 
                                stdin_for_next = str(output)
                            except Exception:
                                print(f"Warning: Cannot convert output to string for piping: {type(output)}", file=sys.stderr)
                                stdin_for_next = None
                        else: 
                            stdin_for_next = None
            except Exception as pipeline_error:
                import traceback
                traceback.print_exc()
                error_msg = colored(f"Error in pipeline stage {i+1} ('{cmd_segment[:50]}...'): {pipeline_error}", "red")
                return current_state, error_msg

        if final_output is not None and isinstance(final_output,str):
            store_command_embeddings(original_command_for_embedding, final_output, current_state)

        return current_state, final_output


    elif state.current_mode == 'chat':
      
        cmd_parts = parse_command_safely(command)
        is_probably_bash = (
            cmd_parts
            and (
                cmd_parts[0] in interactive_commands
                or cmd_parts[0] in BASH_COMMANDS
                or command.strip().startswith("./")
                or command.strip().startswith("/")
            )
        )
        if is_probably_bash:
            try:
                command_name = cmd_parts[0]
                if command_name in interactive_commands:
                    return handle_interactive_command(cmd_parts, state)
                elif command_name == "cd":
                    return handle_cd_command(cmd_parts, state)
                else:
                    try:
                        bash_state, bash_output = handle_bash_command(cmd_parts, command, None, state)
                        return state, bash_output
                    except Exception as bash_err:
                        return state, colored(f"Bash execution failed: {bash_err}", "red")
            except Exception:
                pass

      
        response = get_llm_response(
            command, 
            model=active_model,          
            provider=active_provider,    
            npc=state.npc,
            stream=state.stream_output,
            messages=state.messages
        )
        state.messages = response['messages']
        return state, response['response']

    elif state.current_mode == 'cmd':

        response = execute_llm_command(command, 
                                        model=active_model,          
                                        provider=active_provider,  
                                                 npc = state.npc, 
                                                 stream = state.stream_output, 
                                                 messages = state.messages) 
        state.messages = response['messages']     
        return state, response['response']

def setup_shell() -> Tuple[CommandHistory, Team, Optional[NPC]]:
    setup_npcsh_config()

    db_path = os.getenv("NPCSH_DB_PATH", HISTORY_DB_DEFAULT_PATH)
    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    command_history = CommandHistory(db_path)

    if not is_npcsh_initialized():
        print("Initializing NPCSH...")
        initialize_base_npcs_if_needed(db_path)
        print("NPCSH initialization complete. Restart or source ~/.npcshrc.")

    try:
        history_file = setup_readline()
        atexit.register(save_readline_history)
        atexit.register(command_history.close)
    except:
        pass

    project_team_path = os.path.abspath(PROJECT_NPC_TEAM_PATH)
    global_team_path = os.path.expanduser(DEFAULT_NPC_TEAM_PATH)
    team_dir = None
    default_forenpc_name = None

    if os.path.exists(project_team_path):
        team_dir = project_team_path
        default_forenpc_name = "forenpc"
    else:
        if not os.path.exists('.npcsh_global'):
            resp = input(f"No npc_team found in {os.getcwd()}. Create a new team here? [Y/n]: ").strip().lower()
            if resp in ("", "y", "yes"):
                team_dir = project_team_path
                os.makedirs(team_dir, exist_ok=True)
                default_forenpc_name = "forenpc"
                forenpc_directive = input(
                    f"Enter a primary directive for {default_forenpc_name} (default: 'You are the forenpc of the team...'): "
                ).strip() or "You are the forenpc of the team, coordinating activities between NPCs on the team, verifying that results from NPCs are high quality and can help to adequately answer user requests."
                forenpc_model = input("Enter a model for your forenpc (default: llama3.2): ").strip() or "llama3.2"
                forenpc_provider = input("Enter a provider for your forenpc (default: ollama): ").strip() or "ollama"
                
                with open(os.path.join(team_dir, f"{default_forenpc_name}.npc"), "w") as f:
                    yaml.dump({
                        "name": default_forenpc_name, "primary_directive": forenpc_directive,
                        "model": forenpc_model, "provider": forenpc_provider
                    }, f)
                
                ctx_path = os.path.join(team_dir, "team.ctx")
                folder_context = input("Enter a short description for this project/team (optional): ").strip()
                team_ctx_data = {
                    "forenpc": default_forenpc_name, 
                    "model": forenpc_model,
                    "provider": forenpc_provider, 
                    "context": folder_context if folder_context else None
                }
                use_jinxs = input("Use global jinxs folder (g) or copy to this project (c)? [g/c, default: g]: ").strip().lower()
                if use_jinxs == "c":
                    global_jinxs_dir = os.path.expanduser("~/.npcsh/npc_team/jinxs")
                    if os.path.exists(global_jinxs_dir):
                        shutil.copytree(global_jinxs_dir, team_dir, dirs_exist_ok=True)
                else:
                    team_ctx_data["use_global_jinxs"] = True

                with open(ctx_path, "w") as f:
                    yaml.dump(team_ctx_data, f)
            else:
                render_markdown('From now on, npcsh will assume you will use the global team when activating from this folder. \n If you change your mind and want to initialize a team, use /init from within npcsh, `npc init` or `rm .npcsh_global` from the current working directory.')
                with open(".npcsh_global", "w") as f:
                    pass
                team_dir = global_team_path
                default_forenpc_name = "sibiji"  
        elif os.path.exists(global_team_path):
            team_dir = global_team_path
            default_forenpc_name = "sibiji"            
        
    team_ctx = {}
    team_ctx_path = get_team_ctx_path(team_dir)
    if team_ctx_path:
        try:
            with open(team_ctx_path, "r") as f:
                team_ctx = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load context file {os.path.basename(team_ctx_path)}: {e}")
    forenpc_name = team_ctx.get("forenpc", default_forenpc_name)
  
    print('forenpc_name:', forenpc_name)

    forenpc_path = os.path.join(team_dir, f"{forenpc_name}.npc")
    print('forenpc_path:', forenpc_path)

    team = Team(team_path=team_dir, db_conn=command_history.engine)
    
    forenpc_obj = team.forenpc if hasattr(team, 'forenpc') and team.forenpc else None

    for npc_name, npc_obj in team.npcs.items():
        if not npc_obj.model:
            npc_obj.model = initial_state.chat_model
        if not npc_obj.provider:
            npc_obj.provider = initial_state.chat_provider

    if team.forenpc and isinstance(team.forenpc, NPC):
        if not team.forenpc.model:
            team.forenpc.model = initial_state.chat_model
        if not team.forenpc.provider:
            team.forenpc.provider = initial_state.chat_provider
    
    team_name_from_ctx = team_ctx.get("name")
    if team_name_from_ctx:
        team.name = team_name_from_ctx
    elif team_dir:
        normalized_dir = os.path.normpath(team_dir)
        basename = os.path.basename(normalized_dir)
        if basename and basename != 'npc_team':
            team.name = basename
        else:
            team.name = "npcsh"
    else:
        team.name = "npcsh"

    return command_history, team, forenpc_obj

def initialize_router_with_jinxs(team, router):
    """Load global and team Jinxs into router"""
    global_jinxs_dir = os.path.expanduser("~/.npcsh/npc_team/jinxs")
    router.load_jinx_routes(global_jinxs_dir)
    
    if team and team.team_path:
        team_jinxs_dir = os.path.join(team.team_path, "jinxs")
        if os.path.exists(team_jinxs_dir):
            router.load_jinx_routes(team_jinxs_dir)
    
    return router
                
from npcpy.memory.memory_processor import  memory_approval_ui
from npcpy.ft.memory_trainer import MemoryTrainer
from npcpy.llm_funcs import get_facts

def get_relevant_memories(
    command_history: CommandHistory,
    npc_name: str,
    team_name: str,
    path: str,
    query: Optional[str] = None,
    max_memories: int = 10,
    state: Optional[ShellState] = None
) -> List[Dict]:
    
    engine = command_history.engine
    
    all_memories = command_history.get_memories_for_scope(
        npc=npc_name,
        team=team_name,
        directory_path=path,
        status='human-approved'
    )
    
    if not all_memories:
        return []
    
    if len(all_memories) <= max_memories and not query:
        return all_memories
    
    if query:
        query_lower = query.lower()
        keyword_matches = [
            m for m in all_memories 
            if query_lower in (m.get('final_memory') or m.get('initial_memory') or '').lower()
        ]
        
        if keyword_matches:
            return keyword_matches[:max_memories]

    if state and state.embedding_model and state.embedding_provider:
        try:
            from npcpy.gen.embeddings import get_embeddings
            
            search_text = query if query else "recent context"
            query_embedding = get_embeddings(
                [search_text],
                state.embedding_model,
                state.embedding_provider
            )[0]
            
            memory_texts = [
                m.get('final_memory', '') for m in all_memories
            ]
            memory_embeddings = get_embeddings(
                memory_texts,
                state.embedding_model,
                state.embedding_provider
            )
            
            import numpy as np
            similarities = []
            for mem_emb in memory_embeddings:
                similarity = np.dot(query_embedding, mem_emb) / (
                    np.linalg.norm(query_embedding) * 
                    np.linalg.norm(mem_emb)
                )
                similarities.append(similarity)
            
            sorted_indices = np.argsort(similarities)[::-1]
            return [all_memories[i] for i in sorted_indices[:max_memories]]
            
        except Exception as e:
            print(colored(
                f"RAG search failed, using recent: {e}", 
                "yellow"
            ))
    
    return all_memories[-max_memories:]


def search_kg_facts(
    self,
    npc: str,
    team: str,
    directory_path: str,
    query: str
) -> List[Dict]:
    
    kg = load_kg_from_db(
        self.engine, 
        team, 
        npc, 
        directory_path
    )
    
    if not kg or 'facts' not in kg:
        return []
    
    query_lower = query.lower()
    matching_facts = []
    
    for fact in kg['facts']:
        statement = fact.get('statement', '').lower()
        if query_lower in statement:
            matching_facts.append(fact)
    
    return matching_facts

def format_memory_context(memory_examples):
    if not memory_examples:
        return ""
    
    context_parts = []
    
    approved_examples = memory_examples.get("approved", [])
    rejected_examples = memory_examples.get("rejected", [])
    
    if approved_examples:
        context_parts.append("EXAMPLES OF GOOD MEMORIES:")
        for ex in approved_examples[:5]:
            final = ex.get("final_memory") or ex.get("initial_memory")
            context_parts.append(f"- {final}")
    
    if rejected_examples:
        context_parts.append("\nEXAMPLES OF POOR MEMORIES TO AVOID:")
        for ex in rejected_examples[:3]:
            context_parts.append(f"- {ex.get('initial_memory')}")
    
    if context_parts:
        context_parts.append("\nLearn from these examples to generate similar high-quality memories.")
        return "\n".join(context_parts)
    
    return ""

def process_memory_approvals(command_history, memory_queue):
    pending_memories = memory_queue.get_approval_batch(max_items=5)
    
    if not pending_memories:
        return
        
    print(f"\n🧠 Processing {len(pending_memories)} memories...")
    
    try:
        trainer = MemoryTrainer()
        auto_processed = []
        need_human_review = []
        
        for memory in pending_memories:
            result = trainer.auto_approve_memory(
                memory['content'], 
                memory['context'],
                confidence_threshold=0.85
            )
            
            if result['auto_processed']:
                auto_processed.append((memory, result))
            else:
                need_human_review.append(memory)
        
        for memory, result in auto_processed:
            command_history.update_memory_status(
                memory['memory_id'], 
                result['action']
            )
            print(f"  Auto-{result['action']}: {memory['content'][:50]}... (confidence: {result['confidence']:.2f})")
        
        if need_human_review:
            approvals = memory_approval_ui(need_human_review)
            
            for approval in approvals:
                command_history.update_memory_status(
                    approval['memory_id'],
                    approval['decision'],
                    approval.get('final_memory')
                )
    
    except Exception as e:
        print(f"Auto-approval failed: {e}")
        approvals = memory_approval_ui(pending_memories)
        
        for approval in approvals:
            command_history.update_memory_status(
                approval['memory_id'],
                approval['decision'], 
                approval.get('final_memory')
            )

def process_result(
    user_input: str,
    result_state: ShellState,
    output: Any,
    command_history: CommandHistory,
):
    team_name = result_state.team.name if result_state.team else "npcsh"
    npc_name = result_state.npc.name if isinstance(result_state.npc, NPC) else "npcsh"
    
    active_npc = result_state.npc if isinstance(result_state.npc, NPC) else NPC(
        name="default", 
        model=result_state.chat_model, 
        provider=result_state.chat_provider, 
        db_conn=command_history.engine
    )
    
    save_conversation_message(
        command_history,
        result_state.conversation_id,
        "user",
        user_input,
        wd=result_state.current_path,
        model=active_npc.model,
        provider=active_npc.provider,
        npc=npc_name,
        team=team_name,
        attachments=result_state.attachments,
    )
    result_state.attachments = None

    final_output_str = None
    
    if isinstance(output, dict):
        output_content = output.get('output')
        model_for_stream = output.get('model', active_npc.model)
        provider_for_stream = output.get('provider', active_npc.provider)
    else:
        output_content = output
        model_for_stream = active_npc.model
        provider_for_stream = active_npc.provider

    print('\n')
    if user_input == '/help':
        if isinstance(output_content, str):
            render_markdown(output_content)
        else:
            render_markdown(str(output_content))
    elif result_state.stream_output:
        final_output_str = print_and_process_stream_with_markdown(
            output_content, 
            model_for_stream, 
            provider_for_stream, 
            show=True
        )
    elif output_content is not None:
        final_output_str = str(output_content)
        render_markdown(final_output_str)

    if final_output_str:
        if result_state.messages:
            if not result_state.messages or result_state.messages[-1].get("role") != "assistant":
                result_state.messages.append({
                    "role": "assistant", 
                    "content": final_output_str
                })
        
        save_conversation_message(
            command_history,
            result_state.conversation_id,
            "assistant",
            final_output_str,
            wd=result_state.current_path,
            model=active_npc.model,
            provider=active_npc.provider,
            npc=npc_name,
            team=team_name,
        )

        result_state.turn_count += 1

        if result_state.turn_count % 10 == 0:
            approved_facts = []
            
            conversation_turn_text = f"User: {user_input}\nAssistant: {final_output_str}"
            engine = command_history.engine

            memory_examples = command_history.get_memory_examples_for_context(
                npc=npc_name,
                team=team_name, 
                directory_path=result_state.current_path
            )
            
            memory_context = format_memory_context(memory_examples)
            
            try:
                facts = get_facts(
                    conversation_turn_text,
                    model=active_npc.model,
                    provider=active_npc.provider,
                    npc=active_npc,
                    context=memory_context + 'Memories should be fully self contained. They should not use vague pronouns or words like that or this or it.  Do not generate more than 1-2 memories at a time.'
                )
                
                if facts:
                    num_memories = len(facts)
                    print(colored(
                        f"\nThere are {num_memories} potential memories. Do you want to review them now?", 
                        "cyan"
                    ))
                    review_choice = input("[y/N]: ").strip().lower()
                    
                    if review_choice == 'y':
                        memories_for_approval = []
                        for i, fact in enumerate(facts):
                            memories_for_approval.append({
                                "memory_id": f"temp_{i}",
                                "content": fact['statement'],
                                "context": f"Type: {fact.get('type', 'unknown')}, Source: {fact.get('source_text', '')}",
                                "npc": npc_name,
                                "fact_data": fact
                            })
                        
                        approvals = memory_approval_ui(memories_for_approval)
                        
                        for approval in approvals:
                            fact_data = next(
                                m['fact_data'] for m in memories_for_approval 
                                if m['memory_id'] == approval['memory_id']
                            )
                            
                            command_history.add_memory_to_database(
                                message_id=f"{result_state.conversation_id}_{len(result_state.messages)}",
                                conversation_id=result_state.conversation_id,
                                npc=npc_name,
                                team=team_name,
                                directory_path=result_state.current_path,
                                initial_memory=fact_data['statement'],
                                status=approval['decision'],
                                model=active_npc.model,
                                provider=active_npc.provider,
                                final_memory=approval.get('final_memory')
                            )
                            
                            if approval['decision'] in ['human-approved', 'human-edited']:
                                approved_fact = {
                                    'statement': approval.get('final_memory') or fact_data['statement'],
                                    'source_text': fact_data.get('source_text', ''),
                                    'type': fact_data.get('type', 'explicit'),
                                    'generation': 0
                                }
                                approved_facts.append(approved_fact)
                    else:
                        for i, fact in enumerate(facts):
                            command_history.add_memory_to_database(
                                message_id=f"{result_state.conversation_id}_{len(result_state.messages)}",
                                conversation_id=result_state.conversation_id,
                                npc=npc_name,
                                team=team_name,
                                directory_path=result_state.current_path,
                                initial_memory=fact['statement'],
                                status='skipped',
                                model=active_npc.model,
                                provider=active_npc.provider,
                                final_memory=None
                            )
                        
                        print(colored(
                            f"Marked {num_memories} memories as skipped.", 
                            "yellow"
                        ))
                    
            except Exception as e:
                print(colored(f"Memory generation error: {e}", "yellow"))

            if result_state.build_kg and approved_facts:
                try:
                    if not should_skip_kg_processing(user_input, final_output_str):
                        npc_kg = load_kg_from_db(
                            engine, 
                            team_name, 
                            npc_name, 
                            result_state.current_path
                        )
                        evolved_npc_kg, _ = kg_evolve_incremental(
                            existing_kg=npc_kg, 
                            new_facts=approved_facts,
                            model=active_npc.model, 
                            provider=active_npc.provider, 
                            npc=active_npc,
                            get_concepts=True,
                            link_concepts_facts=False, 
                            link_concepts_concepts=False, 
                            link_facts_facts=False,                         
                        )
                        save_kg_to_db(
                            engine,
                            evolved_npc_kg, 
                            team_name, 
                            npc_name, 
                            result_state.current_path
                        )
                except Exception as e:
                    print(colored(
                        f"Error during real-time KG evolution: {e}", 
                        "red"
                    ))

            print(colored(
                "\nChecking for potential team improvements...", 
                "cyan"
            ))
            try:
                summary = breathe(
                    messages=result_state.messages[-20:], 
                    npc=active_npc
                )
                characterization = summary.get('output')

                if characterization and result_state.team:
                    team_ctx_path = get_team_ctx_path(
                        result_state.team.team_path
                    )
                    if not team_ctx_path:
                        team_ctx_path = os.path.join(
                            result_state.team.team_path, 
                            "team.ctx"
                        )
                    
                    ctx_data = {}
                    if os.path.exists(team_ctx_path):
                        with open(team_ctx_path, 'r') as f:
                            ctx_data = yaml.safe_load(f) or {}
                    
                    current_context = ctx_data.get('context', '')

                    prompt = f"""Based on this characterization: {characterization},
                    suggest changes (additions, deletions, edits) to the team's context. 
                    Additions need not be fully formed sentences and can simply be equations, relationships, or other plain clear items.
                    
                    Current Context: "{current_context}". 
                    
                    Respond with JSON: {{"suggestion": "Your sentence."}}"""
                    
                    response = get_llm_response(
                        prompt, 
                        npc=active_npc, 
                        format="json"
                    )
                    suggestion = response.get("response", {}).get("suggestion")

                    if suggestion:
                        new_context = (
                            current_context + " " + suggestion
                        ).strip()
                        print(colored(
                            f"{npc_name} suggests updating team context:", 
                            "yellow"
                        ))
                        print(
                            f"  - OLD: {current_context}\n  + NEW: {new_context}"
                        )
                        
                        choice = input(
                            "Apply? [y/N/e(dit)]: "
                        ).strip().lower()
                        
                        if choice == 'y':
                            ctx_data['context'] = new_context
                            with open(team_ctx_path, 'w') as f:
                                yaml.dump(ctx_data, f)
                            print(colored("Team context updated.", "green"))
                        elif choice == 'e':
                            edited_context = input(
                                f"Edit context [{new_context}]: "
                            ).strip()
                            if edited_context:
                                ctx_data['context'] = edited_context
                            else:
                                ctx_data['context'] = new_context
                            with open(team_ctx_path, 'w') as f:
                                yaml.dump(ctx_data, f)
                            print(colored(
                                "Team context updated with edits.", 
                                "green"
                            ))
                        else:
                            print("Suggestion declined.")
            except Exception as e:
                import traceback
                print(colored(
                    f"Could not generate team suggestions: {e}", 
                    "yellow"
                ))
                traceback.print_exc()
                
initial_state = ShellState(
    conversation_id=start_new_conversation(),
    stream_output=NPCSH_STREAM_OUTPUT,
    current_mode=NPCSH_DEFAULT_MODE,
    chat_model=NPCSH_CHAT_MODEL,
    chat_provider=NPCSH_CHAT_PROVIDER,
    vision_model=NPCSH_VISION_MODEL, 
    vision_provider=NPCSH_VISION_PROVIDER,
    embedding_model=NPCSH_EMBEDDING_MODEL, 
    embedding_provider=NPCSH_EMBEDDING_PROVIDER,
    reasoning_model=NPCSH_REASONING_MODEL, 
    reasoning_provider=NPCSH_REASONING_PROVIDER,
    image_gen_model=NPCSH_IMAGE_GEN_MODEL, 
    image_gen_provider=NPCSH_IMAGE_GEN_PROVIDER,
    video_gen_model=NPCSH_VIDEO_GEN_MODEL,
    video_gen_provider=NPCSH_VIDEO_GEN_PROVIDER,
    build_kg=NPCSH_BUILD_KG, 
    api_url=NPCSH_API_URL,
)
