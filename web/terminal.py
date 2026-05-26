"""Terminal emulator backend using PTY for web UI."""

import os, pty, select, threading, struct, fcntl, termios, signal

class WebTerminal:
    """PTY-based terminal that communicates via SocketIO."""

    def __init__(self, sid, socketio, work_dir="/sdcard/Documents"):
        self.sid = sid
        self.socketio = socketio
        self.work_dir = work_dir
        self.pid = None
        self.master_fd = None
        self.slave_fd = None
        self._running = False
        self._reader = None

    def start(self, cols=80, rows=24):
        """Start a new PTY terminal process."""
        if self._running:
            return

        pid, master_fd = pty.openpty()
        if pid == 0:
            # Child process
            os.chdir(self.work_dir)
            shell = os.environ.get("SHELL", "/data/data/com.termux/files/usr/bin/bash")
            if not os.path.exists(shell):
                shell = "/bin/sh"
            os.execvpe(shell, [shell], {
                "TERM": "xterm-256color",
                "HOME": os.path.expanduser("~"),
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "SHELL": shell,
                "LANG": "en_US.UTF-8",
            })
        else:
            # Parent process
            self.pid = pid
            self.master_fd = master_fd
            self._running = True

            # Set terminal size
            self.resize(cols, rows)

            # Start reader thread
            self._reader = threading.Thread(target=self._read_loop, daemon=True)
            self._reader.start()

    def resize(self, cols, rows):
        """Resize the terminal."""
        if self.master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass

    def write(self, data):
        """Write data to the terminal (user input)."""
        if self.master_fd is not None and self._running:
            try:
                os.write(self.master_fd, data.encode("utf-8") if isinstance(data, str) else data)
            except OSError:
                self.stop()

    def _read_loop(self):
        """Read output from PTY and send to client."""
        while self._running and self.master_fd is not None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if r:
                    data = os.read(self.master_fd, 4096)
                    if data:
                        self.socketio.emit("term_output", {"data": data.decode("utf-8", errors="replace")}, to=self.sid)
                    else:
                        break
            except (OSError, ValueError):
                break
        self._running = False
        self.socketio.emit("term_exit", {}, to=self.sid)

    def stop(self):
        """Stop the terminal."""
        self._running = False
        if self.pid is not None:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(self.pid, os.WNOHANG)
            except ChildProcessError:
                pass
            self.pid = None
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

    @property
    def is_running(self):
        return self._running


# Global terminal instances per session
_terminals = {}

def get_terminal(sid, socketio, work_dir="/sdcard/Documents"):
    """Get or create a terminal for a session."""
    if sid in _terminals and _terminals[sid].is_running:
        return _terminals[sid]
    # Clean up old terminal if exists
    if sid in _terminals:
        _terminals[sid].stop()
    term = WebTerminal(sid, socketio, work_dir)
    term.start()
    _terminals[sid] = term
    return term

def close_terminal(sid):
    """Close terminal for a session."""
    if sid in _terminals:
        _terminals[sid].stop()
        del _terminals[sid]
