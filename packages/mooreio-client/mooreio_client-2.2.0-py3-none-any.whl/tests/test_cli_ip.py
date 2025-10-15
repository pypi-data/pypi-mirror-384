# Copyright 2020-2024 Datum Technology Corporation
# All rights reserved.
#######################################################################################################################
import os
import tarfile
from pathlib import Path
from unittest import SkipTest

import pytest
import shutil

import mio_client.cli
from .common import OutputCapture, TestBase


class TestCliIp(TestBase):
    @pytest.fixture(autouse=True)
    def setup(self):
        mio_client.cli.TEST_MODE = True

    def reset_workspace(self):
        p1_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p1"))
        p2_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p2"))
        p3_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p3"))
        p4_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p4"))
        self.remove_directory(p1_path / ".mio")
        self.remove_directory(p2_path / ".mio")
        self.remove_directory(p3_path / ".mio")
        self.remove_directory(p4_path / ".mio")
        self.remove_directory(p1_path / "sim")
        self.remove_directory(p2_path / "sim")
        self.remove_directory(p3_path / "sim")
        self.remove_directory(p4_path / "sim")

    @pytest.mark.core
    def test_cli_list_ip(self, capsys):
        self.reset_workspace()
        test_project_path = os.path.join(os.path.dirname(__file__), "data", "project", "valid_local_simplest")
        result = self.run_cmd(capsys, [f'--wd={test_project_path}', '--dbg', 'list'])
        assert result.return_code == 0
        assert "Found 3" in result.text

    @pytest.mark.core_single
    def test_cli_package_ip(self, capsys):
        self.reset_workspace()
        p1_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p1"))
        wd_path = Path(os.path.join(os.path.dirname(__file__), "wd"))
        self.package_ip(capsys, p1_path, "a_vlib", Path(wd_path / "a_vlib.tgz"))

    def cli_publish_sim_ip(self, capsys, app: str):
        self.reset_workspace()
        p1_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p1"))
        p2_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p2"))
        p3_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p3"))
        p4_path = Path(os.path.join(os.path.dirname(__file__), "data", "integration", "p4"))

        # 1. Login
        self.login(capsys, 'admin', 'admin')

        # 2. Publish A from P1
        self.publish_ip(capsys, p1_path, 'a_vlib')
        self.check_ip_database(1)

        # 3. Install A from P2
        self.install_ip(capsys, p2_path, 'a_vlib')
        self.check_ip_database(2)

        # 4. Publish B from P2
        self.publish_ip(capsys, p2_path, 'b_agent', 'acme')
        self.check_ip_database(2)

        # 5. Install * from P3
        self.install_ip(capsys, p3_path)
        self.check_ip_database(2)

        # 6. Publish C from P3
        self.publish_ip(capsys, p3_path, 'c_block')
        self.check_ip_database(2)

        # 7. Publish D from P3
        self.publish_ip(capsys, p3_path, 'd_lib')
        self.check_ip_database(2)

        # 8. Install A from P4
        self.install_ip(capsys, p4_path, 'a_vlib')
        self.check_ip_database(4)

        # 9. Install E from P4
        self.install_ip(capsys, p4_path, 'e_ss')
        self.check_ip_database(6)

        # 10. Install * from P4
        self.logout(capsys)
        self.login(capsys, 'user1', 'MioNumber1!')
        self.install_ip(capsys, p4_path)
        self.check_ip_database(7)

        # 11. Simulate P4
        self.one_shot_sim_ip(capsys, p4_path, app, 'g_tb', 'smoke', 1)
        self.check_ip_database(7)

        # 12. Uninstall E from P4
        self.uninstall_ip(capsys, p4_path, 'e_ss')
        self.check_ip_database(5)

        # 13. Uninstall * from P4
        self.uninstall_ip(capsys, p4_path)
        self.check_ip_database(3)

        # 14. Clean all IP
        self.clean_ip(capsys, p1_path, 'a_vlib')
        self.clean_ip(capsys, p2_path, 'b_agent')
        self.clean_ip(capsys, p3_path, 'c_block')
        self.clean_ip(capsys, p3_path, 'd_lib')
        self.clean_ip(capsys, p4_path, 'e_ss')
        self.clean_ip(capsys, p4_path, 'f_fpga')
        self.clean_ip(capsys, p4_path, 'g_tb')

        # 13. Logout from P1
        self.logout(capsys)

    #@pytest.mark.integration
    def test_cli_publish_sim_ip_dsim(self, capsys):
        self.cli_publish_sim_ip(capsys, 'dsim')

    @pytest.mark.integration
    @pytest.mark.skip(reason="Vivado licensing not available yet")
    def test_cli_publish_sim_ip_vivado(self, capsys):
        self.cli_publish_sim_ip(capsys, 'vivado')
