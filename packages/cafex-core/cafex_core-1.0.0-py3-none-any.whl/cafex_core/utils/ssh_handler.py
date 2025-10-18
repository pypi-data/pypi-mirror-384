"""This file contains the SSH_Handler class which is used for connecting
to a remote machine using SSH and perform operations like command execution
"""
import re

import paramiko

from cafex_core.utils.core_security import Security
from cafex_core.utils.exceptions import CoreExceptions


class SshHandler:
    """
    Description:
        |  SSH_Handler class contains methods for below operations
        |  1.Establishing the connection
        |  2.Command execution
        |  3.Download file from remote
        |  4.Upload file to remote
        |  5.Close the SSH connection

    """

    def __init__(self):
        self.__exceptions_generic = CoreExceptions()
        self.security = Security()

    def establish_ssh_connection(
            self, server_name: str, username: str = None, password: str = None, pem_file: str = None
    ) -> paramiko.SSHClient:
        """This method is used for connecting to a remote machine using SSH.

        Args:
            server_name (str): Server name or IP address.
            username (str, optional): Username.
            password (str, optional): Password.
            pem_file (str, optional): Filepath of the PEM authentication file.

        Returns:
            object: SSH object.

        Examples:
            1. Using the PEM file:
                SSHClient = ssh_obj.establish_SSH_Connection('ip_address', username=
                'username', pem_file='/path/key.pem')
            2. Using the password:
                SSHClient = ssh_obj.establish_SSH_Connection('ip_address', username=
                'username', password='password')

        Warning:
            Either password or PEM file is allowed.
        """
        try:
            ssh_client = self.security.establish_ssh_connection(
                server_name, username, password, pem_file
            )
            return ssh_client
        except Exception as e:
            error_description = f"An error occurred while establishing the SSH connection: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def __ssh_client(
            self,
            client: paramiko.SSHClient,
            in_buffer: int,
            out_buffer: int,
            width: int = 80,
            height: int = 24,
            width_pixels: int = 0,
            height_pixels: int = 0,
            term: str = "vt100",
            environment: str = None,
    ):
        try:
            shell = (
                client.invoke_shell(term, width, height, width_pixels, height_pixels, environment)
                if width
                else client.invoke_shell()
            )
            stdin = (
                shell.makefile("wb", in_buffer)
                if in_buffer and in_buffer > 0
                else shell.makefile("wb")
            )
            stdout = (
                shell.makefile("r", out_buffer)
                if out_buffer and out_buffer > 0
                else shell.makefile("r")
            )
            return shell, stdin, stdout
        except Exception as e:
            error_description = f"An error occurred while creating the SSH client: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def __execute_command(
            self,
            client: paramiko.SSHClient,
            command,
            maintain_channel=True,
            shell=None,
            stdin=None,
            stdout=None,
            in_buffer=None,
            out_buffer=None,
            vt_width=None,
    ):
        try:
            if not maintain_channel:
                shell = (
                    client.invoke_shell("vt100", vt_width, 24, 0, 0, None)
                    if vt_width
                    else client.invoke_shell()
                )
                stdin = (
                    shell.makefile("wb", in_buffer)
                    if in_buffer and in_buffer > 0
                    else shell.makefile("wb")
                )
                stdout = (
                    shell.makefile("r", out_buffer)
                    if out_buffer and out_buffer > 0
                    else shell.makefile("r")
                )
            stdin.write(command + "\n")
            finish = "End of the command execution"
            echo_cmd = f"echo {finish} $?"
            stdin.write(echo_cmd + "\n")
            stdin.flush()
            output = []
            error = []
            capture = False
            exit_status = 0

            for line in stdout:
                if (re.findall(r"\[.*?\]\$", line) or re.findall(r"\[.*?\]#", line)) \
                        and not capture:
                    capture = True
                if capture:
                    if line.startswith(finish):
                        exit_status = int(line.rsplit(maxsplit=1)[1])
                        if exit_status:
                            error = output
                            output = []
                        break
                    output.append(
                        re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
                        .sub("", line)
                        .replace("\b", "")
                        .replace("\r", "")
                    )
                    if output and echo_cmd in output[-1]:
                        output.pop()
            return exit_status, error if error else output
        except Exception as e:
            error_description = f"An error occurred while executing the command: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def execute(
            self,
            ssh_client: paramiko.SSHClient,
            commands: list,
            filepath: str = None,
            maintain_channel: bool = True,
            in_buffer: int = None,
            out_buffer: int = None,
            vt_width: int = None,
    ):
        """This method executes the given commands and will return a list of
        results and also saves the output to a text file if given.

        Note:
            Buffer size depends on the available memory but for efficient use of the
            buffer size specify as much as
            needed (do not give excessive buffer size for small tasks).

        Args:
            ssh_client (object): SSH Object returned by the establish_connection method.
            commands (list): A list of commands that need to be executed.
            filepath (str, optional): Text file path to store the command outputs.
            maintain_channel (bool, optional): Default is True.
            in_buffer (int, optional): Size for input buffer.
            out_buffer (int, optional): Size for output buffer.
            vt_width (int, optional): Width for virtual terminal.

        Returns:
            list: List of command outputs.

        Examples:
            1. With one command:
                >> ssh_obj.execute(SSHClient, ['sudo su -'])
            2. With multiple commands:
                >> ssh_obj.execute(SSHClient, ['sudo su -', 'ls', 'cd folder'])
            3. With multiple commands and without channel maintenance:
                >> ssh_obj.execute(SSHClient, ['sudo su -', 'ls', 'cd folder'],
                maintain_channel=False)
            4. With multiple commands and save to text file:
                >> ssh_obj.execute(SSHClient, ['sudo su -', 'ls', 'cd folder'],
                pstr_filepath="/path/output.txt")
            5. With input and output buffers:
                >> ssh_obj.execute(SSHClient, ['sudo su -', 'ls', 'cd folder'],
                in_buffer=1024, out_buffer=1024)
            6. With input, output buffers and virtual terminal width:
                >> ssh_obj.execute(SSHClient, ['sudo su -', 'ls', 'cd folder'],
                in_buffer=1024, out_buffer=1024,
                 vt_width=200)
        """
        try:
            if filepath and not filepath.strip().endswith(".txt"):
                raise ValueError("Only text files are allowed")
            if ssh_client is None:
                raise ValueError("The SSH client passed is None, please check the connection "
                                 "object")
            if not isinstance(commands, list):
                raise TypeError("Commands should be of type list")
            command_output = []

            if maintain_channel:
                shell, stdin, stdout = self.__ssh_client(
                    ssh_client, in_buffer, out_buffer, vt_width
                )
            else:
                shell, stdin, stdout = None, None, None

            for command in commands:
                if maintain_channel:
                    output = self.__execute_command(
                        ssh_client, command, shell=shell, stdin=stdin, stdout=stdout
                    )
                else:
                    output = self.__execute_command(
                        ssh_client,
                        command,
                        maintain_channel,
                        in_buffer=in_buffer,
                        out_buffer=out_buffer,
                        vt_width=vt_width,
                    )
                command_output += output

            if filepath:
                with open(filepath.strip(), "w", encoding='utf-8') as writefile:
                    for data in command_output:
                        writefile.write(data)
            return command_output
        except Exception as e:
            error_description = f"An error occurred while executing the command: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def download_file_from_remote(self, ssh_client: paramiko.SSHClient, remote_path: str, local_path: str) -> None:
        """
        Downloads a file from a remote server to a local machine.

        Args:
            ssh_client (paramiko.SSHClient): The SSH client object.
            remote_path (str): Full path of the file on the remote server (including filename).
            local_path (str): Full path where the file will be saved locally (including filename).

        Returns:
            None

        Raises:
            ValueError: If the ssh_client is None.
            Exception: If any error occurs during the file transfer.
        """
        try:
            if not ssh_client:
                raise ValueError("The ssh client is none, please check the connection object")

            if not remote_path or not local_path:
                raise ValueError("Both remote_path and local_path must be provided and valid")

            ftp_client = ssh_client.open_sftp()
            try:
                ftp_client.get(remote_path, local_path)
            finally:
                ftp_client.close()

        except Exception as e:
            error_description = f"An error occurred while downloading the file from remote: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def upload_file_to_remote(self, ssh_client: paramiko.SSHClient, local_path: str, remote_path: str) -> None:
        """
        Uploads a file from a local machine to a remote server.

        Args:
            ssh_client (paramiko.SSHClient): The SSH client object.
            local_path (str): Full path of the file on the local machine (including filename).
            remote_path (str): Full path where the file will be saved on the remote server (including filename).

        Returns:
            None

        Raises:
            ValueError: If the ssh_client is None or paths are invalid.
            Exception: If any error occurs during the file transfer.
        """
        try:
            if not ssh_client:
                raise ValueError("The ssh client is None, please check the connection object")

            if not local_path or not remote_path:
                raise ValueError("Both local_path and remote_path must be provided and valid")

            ftp_client = ssh_client.open_sftp()
            try:
                ftp_client.put(local_path, remote_path)
            finally:
                ftp_client.close()

        except Exception as e:
            error_description = f"An error occurred while uploading the file to remote: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e

    def close_ssh_connection(self, ssh_client: paramiko.SSHClient) -> None:
        """This method is used to close the SSH connection.

        Args:
            ssh_client (object): The object returned by the establish_connection method.

        Returns:
            None
        """
        try:
            ssh_client.close()
        except Exception as e:
            error_description = f"An error occurred while closing the SSH connection: {str(e)}"
            self.__exceptions_generic.raise_generic_exception(
                message=error_description,
                insert_report=True,
                trim_log=True,
                log_local=True,
                fail_test=False,
            )
            raise e
