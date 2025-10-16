# chuk_mcp/mcp_client/host/server_manager.py
import os
import asyncio
import anyio

# mcp imports - import from messages layer, not transport layer
from chuk_mcp.protocol.messages.initialize.send_messages import send_initialize


def run_command(command_func, config_file, server_names, user_specified=None):
    """Run a command with the specified servers by managing server connections."""

    async def _run_clients():
        server_streams = []
        server_info = []  # For intelligent routing.
        context_managers = []
        clean_exit = False

        # Import dependencies here to avoid circular imports
        from chuk_mcp.transports.stdio.stdio_client import stdio_client
        from chuk_mcp.config import load_config

        # Create all server connections.
        for sname in server_names:
            try:
                server_params = await load_config(config_file, sname)
                cm = stdio_client(server_params)
                streams = await cm.__aenter__()
                context_managers.append((cm, streams))

                r_stream, w_stream = streams

                # Initialize this server.
                init_result = await send_initialize(r_stream, w_stream)
                if not init_result:
                    print(f"Server initialization failed for {sname}")
                    try:
                        await cm.__aexit__(None, None, None)
                    except Exception as e:
                        print(f"Error closing connection to {sname}: {e}")
                    context_managers.pop()
                    continue

                server_streams.append(streams)
                server_info.append(
                    {
                        "name": sname,
                        "streams": streams,
                        "user_specified": sname in (user_specified or []),
                    }
                )
            except Exception as e:
                print(f"Error connecting to server {sname}: {e}")
                continue

        try:
            if server_streams:
                is_interactive = command_func.__name__ == "interactive_mode"
                is_chat = command_func.__name__ == "chat_run"

                if is_interactive or is_chat:
                    try:
                        result = await command_func(
                            server_streams, server_info=server_info
                        )
                    except TypeError:
                        result = await command_func(server_streams)
                    if result is True:
                        clean_exit = True
                else:
                    await command_func(server_streams)
            else:
                print("No valid server connections established")
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected, cleaning up...")
        except Exception as e:
            print(f"\nError in command: {e}")
        finally:
            should_log = not clean_exit
            for i, (cm, _) in enumerate(list(context_managers)):
                try:
                    close_task = asyncio.create_task(cm.__aexit__(None, None, None))
                    try:
                        await asyncio.wait_for(close_task, timeout=2.0)
                    except asyncio.TimeoutError:
                        if should_log:
                            print(
                                f"Connection cleanup {i+1}/{len(context_managers)} timed out"
                            )
                    except (asyncio.CancelledError, RuntimeError):
                        pass
                except Exception as e:
                    if should_log and not isinstance(
                        e, (asyncio.CancelledError, RuntimeError)
                    ):
                        print(
                            f"Error during server shutdown {i+1}/{len(context_managers)}: {e}"
                        )

    os.system("cls" if os.name == "nt" else "clear")

    try:
        anyio.run(_run_clients)
    except KeyboardInterrupt:
        print("\nOperation interrupted. Exiting...")
    except Exception as e:
        print(f"\nError: {e}")
