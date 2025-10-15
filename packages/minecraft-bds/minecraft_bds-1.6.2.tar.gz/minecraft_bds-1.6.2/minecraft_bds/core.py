import asyncio
import json
import subprocess
import sys
from pathlib import Path
from .installer import ensure_bds_installed

class MinecraftBDS:
    _instances = {}

    def __new__(cls, base_path: Path | None = None):
        # Singleton per base_path to allow multiple servers
        base_path = Path(base_path) if base_path else Path("./server")
        if str(base_path.resolve()) not in cls._instances:
            cls._instances[str(base_path.resolve())] = super().__new__(cls)
        return cls._instances[str(base_path.resolve())]

    def __init__(self, base_path: Path | None = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        # Server folder
        self.base_path = Path(base_path) if base_path else Path("./server")
        self.server_path = ensure_bds_installed(self.base_path)

        # Determine executable
        self.bds_path = self.server_path / (
            "bedrock_server.exe" if sys.platform.startswith("win") else "bedrock_server"
        )

        # Process & event handling
        self.bds_process: subprocess.Popen | None = None
        self.event_handlers: dict[str, list] = {}

    # ----------------------
    # Event decorator
    # ----------------------
    def event(self, func):
        """Register an async event handler. Event name = function name."""
        name = func.__name__
        if name not in self.event_handlers:
            self.event_handlers[name] = []
        self.event_handlers[name].append(func)
        return func

    async def _dispatch_event(self, event_name: str, data: dict):
        handlers = self.event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                print(f"[BDS] Error in event handler {handler.__name__}: {e}")

    # ----------------------
    # Send Minecraft command
    # ----------------------
    async def RunCommand(self, command: str):
        if self.bds_process and self.bds_process.stdin:
            try:
                self.bds_process.stdin.write((command + "\n").encode())
                self.bds_process.stdin.flush()
            except Exception as e:
                print(f"[BDS] Failed to send command: {e}")
        else:
            print("[BDS] Server not running.")

    # ----------------------
    # Start server
    # ----------------------
    async def start(self):
        if self.bds_process:
            print("[BDS] Server already running.")
            return

        print(f"[BDS] Starting server at {self.server_path} …")

        # Windows: detach console properly
        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NEW_CONSOLE

        self.bds_process = subprocess.Popen(
            [str(self.bds_path)],
            cwd=str(self.server_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            bufsize=1,
            universal_newlines=True,
        )

        # Start log watcher
        loop = asyncio.get_running_loop()
        loop.create_task(self._watch_logs())
        print("[BDS] Server started.")

    # ----------------------
    # Stop server
    # ----------------------
    async def stop(self):
        if not self.bds_process:
            return
        print("[BDS] Stopping server …")
        self.bds_process.terminate()
        await asyncio.sleep(1)
        if self.bds_process.poll() is None:
            self.bds_process.kill()
        self.bds_process = None
        print("[BDS] Server stopped.")

    # ----------------------
    # Watch logs (non-blocking, JSON parsing)
    # ----------------------
    async def _watch_logs(self):
        if not self.bds_process or not self.bds_process.stdout:
            return

        loop = asyncio.get_running_loop()
        reader = self.bds_process.stdout

        while self.bds_process and self.bds_process.poll() is None:
            # Read a line in a thread to avoid blocking
            line = await loop.run_in_executor(None, reader.readline)
            if not line:
                await asyncio.sleep(0.05)
                continue
            line = line.strip()
            print(f"[BDS LOG] {line}")

            # Detect JSON from scripting logs
            if "[Scripting]" in line:
                try:
                    json_start = line.index("{")
                    data = json.loads(line[json_start:])
                    event_name = data.get("event")
                    if event_name:
                        # Convert spaces to underscores for Python handlers
                        event_name = event_name.replace(" ", "_")
                        await self._dispatch_event(event_name, data)
                except Exception as e:
                    print(f"[BDS] Failed to parse JSON log: {e}")

# ----------------------
# Singleton instance for easy import
# ----------------------
BDS = MinecraftBDS()
