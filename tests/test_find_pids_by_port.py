"""Tests for the /proc socket lookup that `cyber-kill` falls back to when lsof, ss and fuser are missing."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import cyber_tools

TCP_HEADER = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"


def tcp_row(local: str, remote: str, state: str, inode: str) -> str:
    return f"   0: {local} {remote} {state} 00000000:00000000 00:00000000 00000000  1000        0 {inode} 1 0 0 10 0\n"


class FakeProcTest(unittest.TestCase):
    """A hand-built /proc tree, so the parsing is checked on every OS."""

    def setUp(self):
        if not hasattr(os, "symlink"):
            self.skipTest("os.symlink is not available")
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "net"))
        self.write_table(
            "tcp",
            # 127.0.0.1:8123 listening (inode 111), and a client connection whose *remote* port is 8123 (inode 222)
            tcp_row("0100007F:1FBB", "00000000:0000", "0A", "111")
            + tcp_row("0100007F:D431", "0100007F:1FBB", "01", "222")
            # a TIME_WAIT entry on 8123 has no owner (inode 0)
            + tcp_row("0100007F:1FBB", "0100007F:D432", "06", "0"),
        )
        self.write_table("tcp6", tcp_row("00000000000000000000000000000000:1FBB", "00000000000000000000000000000000:0000", "0A", "333"))
        self.write_table("udp", tcp_row("00000000:1FBC", "00000000:0000", "07", "444"))
        try:
            self.add_process(100, ["socket:[111]", "/dev/null"])  # real owner, IPv4
            self.add_process(200, ["socket:[222]"])  # client talking *to* 8123
            self.add_process(300, ["/dev/null", "pipe:[8123]"])  # decoy, e.g. `sleep 8123`
            self.add_process(400, ["socket:[333]"])  # real owner, IPv6
            self.add_process(500, ["socket:[444]"])  # UDP 8124
        except OSError as exc:  # e.g. Windows without symlink rights
            self.skipTest(f"cannot create symlinks: {exc}")

    def tearDown(self):
        self.tmp.cleanup()

    def write_table(self, name, rows):
        with open(os.path.join(self.root, "net", name), "w", encoding="ascii") as f:
            f.write(TCP_HEADER + rows)

    def add_process(self, pid, targets):
        fd_dir = os.path.join(self.root, str(pid), "fd")
        os.makedirs(fd_dir)
        for fd, target in enumerate(targets):
            os.symlink(target, os.path.join(fd_dir, str(fd)))

    def test_inodes_are_read_for_the_local_port_only(self):
        self.assertEqual(cyber_tools.proc_socket_inodes(8123, self.root), {"111", "333"})
        self.assertEqual(cyber_tools.proc_socket_inodes(8124, self.root), {"444"})
        self.assertEqual(cyber_tools.proc_socket_inodes(80, self.root), set())

    def test_only_socket_owners_are_returned(self):
        self.assertEqual(cyber_tools.find_pids_by_port_proc(8123, self.root), [100, 400])
        self.assertEqual(cyber_tools.find_pids_by_port_proc(8124, self.root), [500])

    def test_no_socket_means_no_pids(self):
        self.assertEqual(cyber_tools.find_pids_by_port_proc(80, self.root), [])

    def test_missing_proc_tables_mean_no_pids(self):
        self.assertEqual(cyber_tools.find_pids_by_port_proc(8123, os.path.join(self.root, "missing")), [])


@unittest.skipUnless(sys.platform.startswith("linux"), "needs a real /proc")
class RealProcTest(unittest.TestCase):
    """`find_pids_by_port` with lsof, ss and fuser hidden, against real processes."""

    def setUp(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.port = self.server.getsockname()[1]
        # A process that has the port number in its command line but owns no socket on it.
        self.decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", str(self.port)])
        time.sleep(0.2)

    def tearDown(self):
        self.decoy.kill()
        self.decoy.wait()
        self.server.close()

    def test_fallback_returns_the_owner_and_not_the_decoy(self):
        with mock.patch.object(cyber_tools, "OS_NAME", "Linux"), mock.patch.object(
            cyber_tools.shutil, "which", return_value=None
        ):
            pids = cyber_tools.find_pids_by_port(self.port)
        self.assertIn(os.getpid(), pids)
        self.assertNotIn(self.decoy.pid, pids)


if __name__ == "__main__":
    unittest.main()
