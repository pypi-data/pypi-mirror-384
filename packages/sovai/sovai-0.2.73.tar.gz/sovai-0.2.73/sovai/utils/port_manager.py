# port_manager_utility.py
import random
import socket
import psutil
import os
import time
import errno
from functools import lru_cache
from typing import List, Optional, Dict

class PortManager:
    """
    Manages the allocation of unique network ports for applications.
    Includes robust checks for port availability and can attempt to free ports.
    """
    def __init__(self, min_port: int = 8050, max_port: int = 8099):
        """
        Initializes the PortManager.

        Args:
            min_port (int): The minimum port number in the range to assign.
            max_port (int): The maximum port number in the range to assign.
        """
        self.app_ports: Dict[str, int] = {} # Stores assigned ports for app names
        self.min_port = min_port
        self.max_port = max_port
        self._current_pid = os.getpid() # Store current process PID

    def is_port_in_use(self, port: int) -> bool:
        """
        Checks if a port is currently in use on the system.
        Tries to bind to the port; if it fails, the port is in use.

        Args:
            port (int): The port number to check.

        Returns:
            bool: True if the port is in use, False otherwise.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    # print(f"Debug: Port {port} is already in use (socket bind check).")
                    return True
                # print(f"Debug: Unexpected error checking port {port}: {e}")
                return True # Assume in use on other errors for safety
        # print(f"Debug: Port {port} is free (socket bind check).")
        return False

    def _find_pids_using_port(self, port: int) -> List[int]:
        """
        Finds PIDs of processes using a specific port.

        Args:
            port (int): The port number.

        Returns:
            List[int]: A list of PIDs using the port.
        """
        pids = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    if conn.pid is not None:
                        pids.append(conn.pid)
        except psutil.AccessDenied:
            print(f"Warning (PortManager): Access denied when trying to list network connections for port {port}.")
        except Exception as e:
            print(f"Warning (PortManager): Error listing network connections for port {port}: {e}")
        return list(set(pids))

    def _kill_processes_by_pids(self, pids: List[int]) -> bool:
        """
        Attempts to terminate processes by their PIDs, skipping the current process.

        Args:
            pids (List[int]): A list of PIDs to terminate.

        Returns:
            bool: True if any process was attempted to be killed, False otherwise.
        """
        killed_any = False
        for pid_to_kill in pids:
            if pid_to_kill == self._current_pid:
                print(f"Info (PortManager): Skipping attempt to kill current process (PID: {pid_to_kill}).")
                continue
            try:
                proc = psutil.Process(pid_to_kill)
                proc_name = proc.name()
                print(f"Info (PortManager): Attempting to terminate process '{proc_name}' (PID: {pid_to_kill}) on port.")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    print(f"Warning (PortManager): Process '{proc_name}' (PID: {pid_to_kill}) did not terminate gracefully, forcing kill.")
                    proc.kill()
                    proc.wait(timeout=3)
                print(f"Info (PortManager): Process '{proc_name}' (PID: {pid_to_kill}) terminated.")
                killed_any = True
            except psutil.NoSuchProcess:
                print(f"Info (PortManager): Process (PID: {pid_to_kill}) already terminated.")
            except psutil.AccessDenied:
                print(f"Error (PortManager): Access Denied. Cannot terminate process (PID: {pid_to_kill}). Try with higher privileges.")
            except Exception as e:
                print(f"Error (PortManager): Failed to terminate process (PID: {pid_to_kill}): {e}")
        return killed_any

    def kill_process_on_port(self, port: int) -> bool:
        """
        Finds and kills processes listening on the given port.

        Args:
            port (int): The port number to free up.

        Returns:
            bool: True if any process was attempted to be killed, False otherwise.
        """
        print(f"Info (PortManager): Attempting to free up port {port}...")
        pids_on_port = self._find_pids_using_port(port)

        if not pids_on_port:
            print(f"Info (PortManager): No process found listening on port {port}.")
            return False

        print(f"Info (PortManager): Processes found on port {port}: {pids_on_port}")
        return self._kill_processes_by_pids(pids_on_port)

    def get_unique_port(self, app_name: str) -> int:
        """
        Gets a unique port for the given application name.
        If a port was already assigned to this app_name in this session, tries to reuse it if free.
        Otherwise, finds a new free port in the defined range.

        Args:
            app_name (str): The name of the application requiring a port.

        Returns:
            int: A unique port number.

        Raises:
            RuntimeError: If no free port can be found in the specified range.
        """
        if app_name in self.app_ports:
            potential_port = self.app_ports[app_name]
            if not self.is_port_in_use(potential_port):
                print(f"Info (PortManager): Re-using previously assigned port {potential_port} for app '{app_name}'.")
                return potential_port
            else:
                print(f"Warning (PortManager): Previously assigned port {potential_port} for '{app_name}' is now in use by another process.")
                # Continue to find a new port

        # Ports already assigned by this instance of PortManager for other apps
        used_ports_by_this_manager = set(self.app_ports.values())

        # Try random allocation first
        for _ in range(self.max_port - self.min_port + 10): # Try a reasonable number of times
            port = random.randint(self.min_port, self.max_port)
            if port not in used_ports_by_this_manager and not self.is_port_in_use(port):
                # print(f"Info (PortManager): Found free port {port} for app '{app_name}'.")
                self.app_ports[app_name] = port
                return port
        
        # Fallback: If random attempts fail, iterate sequentially
        print(f"Info (PortManager): Random port allocation failed for '{app_name}', trying sequential scan.")
        for port in range(self.min_port, self.max_port + 1):
            if port not in used_ports_by_this_manager and not self.is_port_in_use(port):
                # print(f"Info (PortManager): Found free port {port} (sequential scan) for app '{app_name}'.")
                self.app_ports[app_name] = port
                return port

        raise RuntimeError(f"Error (PortManager): Could not find a free port for '{app_name}' in range {self.min_port}-{self.max_port} after extensive search.")

    def release_port(self, app_name: str):
        """
        Releases a port associated with an app_name, making it available for reuse by this manager.
        Note: This does not kill any process currently using the port system-wide.

        Args:
            app_name (str): The name of the application whose port is to be released.
        """
        if app_name in self.app_ports:
            port = self.app_ports[app_name]
            del self.app_ports[app_name]
            print(f"Info (PortManager): Port {port} for app '{app_name}' released from manager.")
        else:
            print(f"Warning (PortManager): No port assigned to app '{app_name}' to release.")


@lru_cache(maxsize=None)
def get_port_manager_instance(min_port: int = 8050, max_port: int = 8099) -> PortManager:
    """
    Returns a cached singleton instance of PortManager.
    Allows customization of port range on first call.

    Args:
        min_port (int): The minimum port number for the manager.
        max_port (int): The maximum port number for the manager.
    
    Returns:
        PortManager: The singleton PortManager instance.
    """
    # print("Info (PortManager): Creating/retrieving PortManager instance.")
    return PortManager(min_port=min_port, max_port=max_port)

# Convenience functions that use the singleton PortManager instance
def get_unique_port(app_name: str, min_port: int = 8050, max_port: int = 8099) -> int:
    """
    Gets a unique port for the given application name using the singleton PortManager.
    Port range can be specified, affecting the singleton on its first creation.
    """
    manager = get_port_manager_instance(min_port=min_port, max_port=max_port)
    return manager.get_unique_port(app_name)

def kill_process_on_port(port: int, min_port: int = 8050, max_port: int = 8099) -> bool:
    """
    Finds and kills processes listening on the given port using the singleton PortManager.
    """
    manager = get_port_manager_instance(min_port=min_port, max_port=max_port)
    return manager.kill_process_on_port(port)

def release_port(app_name: str, min_port: int = 8050, max_port: int = 8099):
    """
    Releases a port associated with an app_name using the singleton PortManager.
    """
    manager = get_port_manager_instance(min_port=min_port, max_port=max_port)
    manager.release_port(app_name)

if __name__ == '__main__':
    # Example Usage of the port_manager_utility
    print("--- Port Manager Utility Example ---")

    # Get ports for a couple of apps
    try:
        app1_port = get_unique_port("my_first_app")
        print(f"Port for my_first_app: {app1_port}")

        app2_port = get_unique_port("my_second_app")
        print(f"Port for my_second_app: {app2_port}")

        # Trying to get port for the first app again should return the same one
        app1_port_again = get_unique_port("my_first_app")
        print(f"Port for my_first_app (again): {app1_port_again}")
        assert app1_port == app1_port_again

    except RuntimeError as e:
        print(f"Error during port acquisition: {e}")

    # Simulate a port being busy and try to kill process on it
    # For this test, you might need to manually start a listener on a port (e.g., 8070)
    # On Linux/macOS: nc -l 8070
    # On Windows (PowerShell): $listener = New-Object System.Net.Sockets.TcpListener('127.0.0.1', 8070); $listener.Start()
    test_busy_port = 8070 
    print(f"\n--- Testing Port Killing on Port {test_busy_port} (if something is listening) ---")
    # First, check if it's in use by an external process (this script won't mark it as used yet)
    manager = get_port_manager_instance() # Get the manager instance
    if manager.is_port_in_use(test_busy_port):
        print(f"Port {test_busy_port} is currently in use. Attempting to kill process...")
        if kill_process_on_port(test_busy_port): # Use the convenience function
            print(f"Process on port {test_busy_port} hopefully killed. Waiting a moment...")
            time.sleep(2)
            if not manager.is_port_in_use(test_busy_port):
                print(f"Port {test_busy_port} is now free!")
            else:
                print(f"Port {test_busy_port} is STILL in use. Killing might have failed or another process took it.")
        else:
            print(f"Could not kill process on port {test_busy_port} (or no process was found by manager).")
    else:
        print(f"Port {test_busy_port} is free, no need to kill.")

    # Now try to get this port for an app
    try:
        app3_port = get_unique_port("my_third_app_on_specific_port", min_port=test_busy_port, max_port=test_busy_port)
        if app3_port == test_busy_port:
            print(f"Successfully acquired port {test_busy_port} for my_third_app_on_specific_port.")
        else:
            print(f"Acquired port {app3_port} instead of {test_busy_port} for my_third_app_on_specific_port.")
    except RuntimeError as e:
        print(f"Could not acquire port {test_busy_port} for my_third_app_on_specific_port: {e}")

    # Release a port
    release_port("my_first_app")
    # Try to get it again, should be available for a *new* app or re-assignment
    try:
        new_app_port = get_unique_port("new_app_maybe_on_released_port")
        print(f"Port for new_app_maybe_on_released_port: {new_app_port}")
        # It might get the same port as app1_port if it's the first free one found, or a different one.
    except RuntimeError as e:
        print(f"Error: {e}")

    print("\n--- Port Manager Utility Example End ---")
