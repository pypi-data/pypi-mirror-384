import os
import sys
import argparse
import importlib.metadata

import platform
try:
    from termcolor import colored
except: 
    pass
from npcpy.npc_sysenv import (
    render_markdown,
)
from npcpy.memory.command_history import (
    CommandHistory,
    load_kg_from_db, 
    save_kg_to_db, 
)
from npcpy.npc_compiler import NPC
from npcpy.memory.knowledge_graph import (
    kg_evolve_incremental
)

try:
    import readline
except:
    print('no readline support, some features may not work as desired. ')

try:
    VERSION = importlib.metadata.version("npcsh")
except importlib.metadata.PackageNotFoundError:
    VERSION = "unknown"

from npcsh._state import (
    initial_state, 
    orange,
    ShellState,
    execute_command, 
    make_completer,
    process_result,
    readline_safe_prompt,
    setup_shell, 
    get_multiline_input,
    )


def print_welcome_message():
    print(
            """
___________________________________________          
___________________________________________
___________________________________________

Welcome to \033[1;94mnpc\033[0m\033[1;38;5;202msh\033[0m!
\033[1;94m                    \033[0m\033[1;38;5;202m        _       \\\\
\033[1;94m _ __   _ __    ___ \033[0m\033[1;38;5;202m  ___  | |___    \\\\
\033[1;94m| '_ \\ | '_ \\  / __|\033[0m\033[1;38;5;202m / __/ | |_ _|    \\\\
\033[1;94m| | | || |_) |( |__ \033[0m\033[1;38;5;202m \\_  \\ | | | |    //
\033[1;94m|_| |_|| .__/  \\___|\033[0m\033[1;38;5;202m |___/ |_| |_|   //
       \033[1;94m|🤖|          \033[0m\033[1;38;5;202m               //
       \033[1;94m|🤖|
       \033[1;94m|🤖|
___________________________________________
___________________________________________
___________________________________________

Begin by asking a question, issuing a bash command, or typing '/help' for more information.

            """
        )


def run_repl(command_history: CommandHistory, initial_state: ShellState, router):
    state = initial_state
        
    print_welcome_message()

    render_markdown(f'- Using {state.current_mode} mode. Use /agent, /cmd, or /chat to switch to other modes')
    render_markdown(f'- To switch to a different NPC, type /npc <npc_name> or /n <npc_name> to switch to that NPC.')
    render_markdown('\n- Here are the current NPCs available in your team: ' + ', '.join([npc_name for npc_name in state.team.npcs.keys()]))

    is_windows = platform.system().lower().startswith("win")
    try:
        completer = make_completer(state, router)
        readline.set_completer(completer)
    except:
        pass
    session_scopes = set()

    def exit_shell(current_state: ShellState):
        print("\nGoodbye!")
        print(colored("Processing and archiving all session knowledge...", "cyan"))
        
        engine = command_history.engine

        for team_name, npc_name, path in session_scopes:
            try:
                print(f"  -> Archiving knowledge for: T='{team_name}', N='{npc_name}', P='{path}'")
                
                convo_id = current_state.conversation_id
                all_messages = command_history.get_conversations_by_id(convo_id)
                
                scope_messages = [
                    m for m in all_messages 
                    if m.get('directory_path') == path and m.get('team') == team_name and m.get('npc') == npc_name
                ]
                
                full_text = "\n".join([f"{m['role']}: {m['content']}" for m in scope_messages if m.get('content')])

                if not full_text.strip():
                    print("     ...No content for this scope, skipping.")
                    continue

                current_kg = load_kg_from_db(engine, team_name, npc_name, path)
                
                evolved_kg, _ = kg_evolve_incremental(
                    existing_kg=current_kg,
                    new_content_text=full_text,
                    model=current_state.npc.model,
                    provider=current_state.npc.provider, 
                    npc= current_state.npc,
                    get_concepts=True,
                    link_concepts_facts = True, 
                    link_concepts_concepts = True, 
                    link_facts_facts = True, 
                )
                
                save_kg_to_db(engine,
                              evolved_kg,
                              team_name, 
                              npc_name, 
                              path)

            except Exception as e:
                import traceback
                print(colored(f"Failed to process KG for scope ({team_name}, {npc_name}, {path}): {e}", "red"))
                traceback.print_exc()

        sys.exit(0)

    while True:
        try:
            if len(state.messages) > 20:
                planning_state = {
                    "goal": "ongoing npcsh session", 
                    "facts": [f"Working in {state.current_path}", f"Current mode: {state.current_mode}"], 
                    "successes": [], 
                    "mistakes": [],
                    "todos": [],
                    "constraints": ["Follow user requests", "Use appropriate mode for tasks"]
                }
                compressed_state = state.npc.compress_planning_state(planning_state)
                state.messages = [{"role": "system", "content": f"Session context: {compressed_state}"}]

            try:
                completer = make_completer(state, router)
                readline.set_completer(completer)
            except:
                pass

            display_model = state.chat_model
            if isinstance(state.npc, NPC) and state.npc.model:
                display_model = state.npc.model

            if is_windows:
                cwd_part = os.path.basename(state.current_path)
                if isinstance(state.npc, NPC):
                    prompt_end = f":{state.npc.name}:{display_model}> "
                else:
                    prompt_end = ":npcsh> "
                prompt = f"{cwd_part}{prompt_end}"
            else:
                cwd_colored = colored(os.path.basename(state.current_path), "blue")
                if isinstance(state.npc, NPC):
                    prompt_end = f":🤖{orange(state.npc.name)}:{display_model}> "
                else:
                    prompt_end = f":🤖{colored('npc', 'blue', attrs=['bold'])}{colored('sh', 'yellow')}> "
                prompt = readline_safe_prompt(f"{cwd_colored}{prompt_end}")

            user_input = get_multiline_input(prompt).strip()
          
            if user_input == "\x1a":
                exit_shell(state)

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                if isinstance(state.npc, NPC):
                    print(f"Exiting {state.npc.name} mode.")
                    state.npc = None
                    continue
                else:
                    exit_shell(state)
            
            team_name = state.team.name if state.team else "__none__"
            npc_name = state.npc.name if isinstance(state.npc, NPC) else "__none__"
            session_scopes.add((team_name, npc_name, state.current_path))

            state, output = execute_command(user_input, 
                                            state, 
                                            review = False, 
                                            router=router, 
                                            command_history=command_history)

            process_result(user_input, 
                           state, 
                           output, 
                           command_history, 
                           )
        
        except KeyboardInterrupt:
            print("^C")
            if input("\nExit? (y/n): ").lower().startswith('y'):
                exit_shell(state)
            continue

        except EOFError:
            exit_shell(state)
        except Exception as e:            
            if is_windows and "EOF" in str(e).lower():
                print("\nHint: On Windows, use Ctrl+Z then Enter for EOF, or type 'exit'")
                continue
            raise
        

def main() -> None:
    from npcsh.routes import router
    
    parser = argparse.ArgumentParser(description="npcsh - An NPC-powered shell.")
    parser.add_argument(
        "-v", "--version", action="version", version=f"npcsh version {VERSION}"
    )
    parser.add_argument(
         "-c", "--command", type=str, help="Execute a single command and exit."
    )
    args = parser.parse_args()

    command_history, team, default_npc = setup_shell()
    
    if team and hasattr(team, 'jinxs_dict'):
        for jinx_name, jinx_obj in team.jinxs_dict.items():
            router.register_jinx(jinx_obj)

    initial_state.npc = default_npc 
    initial_state.team = team    
    if args.command:
         state = initial_state
         state.current_path = os.getcwd()
         final_state, output = execute_command(args.command, state, router=router, command_history=command_history)
         if final_state.stream_output:
              for chunk in output: 
                  print(str(chunk), end='')
              print()
         elif output is not None:
              print(output)
    else:
        run_repl(command_history, initial_state, router)
        
if __name__ == "__main__":
    main()