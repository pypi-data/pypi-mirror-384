from contextlib import contextmanager
from datetime import datetime
from ftplib import FTP, error_perm
from io import BytesIO
from os.path import basename
from typing import Any, Dict, List

import paramiko
from dateutil import parser

from ..core import file_folder

__all__ = ("FTPClient",)


class FTPClient:
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        timeout: int = 20,
        is_sftp: bool = None,
    ):
        """Initialize the RemoteFileClient with connection parameters.

        If `is_sftp` is not provided, port 22 will be assumed as SFTP.
        """
        self.server = server
        self.port = int(port)
        self.username = username
        self.password = password
        self.timeout = timeout
        # If protocol not specified, assume SFTP for port 22
        self.is_sftp = is_sftp if is_sftp is not None else (self.port == 22)

    @contextmanager
    def _connect(self):
        """Context manager that yields an open connection (SFTP or FTP) based
        on the protocol."""
        if self.is_sftp:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.server,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=self.timeout,
            )
            sftp = ssh.open_sftp()
            sftp.get_channel().settimeout(self.timeout)
            try:
                yield sftp
            finally:
                sftp.close()
                ssh.close()
        else:
            ftp = FTP()
            ftp.connect(host=self.server, port=self.port)
            ftp.login(user=self.username, passwd=self.password)
            try:
                yield ftp
            finally:
                ftp.quit()

    def content(self, file_path: str) -> Dict[str, Any]:
        """Retrieve the content of the file and its last modified timestamp."""
        if self.is_sftp:
            with self._connect() as ftp:
                with ftp.open(file_path) as remote_file:
                    # Read entire content; adjust decoding if needed
                    file_content = remote_file.read().decode("utf-8")
                utime = ftp.stat(file_path).st_mtime
                last_modified = datetime.fromtimestamp(utime)
        else:
            with self._connect() as ftp, BytesIO() as r:
                ftp.retrbinary(f"RETR {file_path}", r.write)
                file_content = r.getvalue().decode("utf-8")
                timestamp = ftp.voidcmd(f"MDTM {file_path}")[4:].strip()
                last_modified = parser.parse(timestamp)

        return {
            "name": basename(file_path),
            "last_modified": last_modified,
            "content": file_content,
        }

    def get_last_modified(self, file_path: str) -> Dict[str, Any]:
        """Retrieve only the last modified timestamp for the file."""
        if self.is_sftp:
            with self._connect() as ftp:
                utime = ftp.stat(file_path).st_mtime
                last_modified = datetime.fromtimestamp(utime)
        else:
            with self._connect() as ftp:
                timestamp = ftp.voidcmd(f"MDTM {file_path}")[4:].strip()
                last_modified = parser.parse(timestamp)

        return {
            "name": basename(file_path),
            "last_modified": last_modified,
        }

    def get_folder_list(self, folder_path: str = "") -> List[str]:
        """Retrieve a list of files in the specified folder."""
        if self.is_sftp:
            with self._connect() as ftp:
                file_list = ftp.listdir(path=folder_path)
        else:
            with self._connect() as ftp:
                if folder_path:
                    ftp.cwd(folder_path)
                try:
                    file_list = ftp.nlst()
                except error_perm:
                    file_list = []
        return file_list

    def upload_file(
        self, local_path: str, file_path: str, confirm: bool = True
    ) -> bool:
        """Upload a local file to the remote server."""
        if self.is_sftp:
            with self._connect() as ftp:
                ftp.put(remotepath=file_path, localpath=local_path, confirm=confirm)
        else:
            with self._connect() as ftp, open(local_path, "rb") as file_obj:
                ftp.storbinary(f"STOR {file_path}", file_obj)
        return True

    def download_file(
        self,
        local_path: str,
        file_path: str,
        make_directory: bool = True,
        remove_file: bool = True,
    ) -> bool:
        """Download a remote file to a local path."""
        if make_directory:
            file_folder.make_directory(file_folder.folder_path_of_file(local_path))

        if remove_file:
            file_folder.remove_file(local_path)

        if self.is_sftp:
            with self._connect() as ftp:
                ftp.get(remotepath=file_path, localpath=local_path)
        else:
            with self._connect() as ftp, open(local_path, "wb") as file_obj:
                ftp.retrbinary(f"RETR {file_path}", file_obj.write)
        return True

    def delete_file(self, file_path: str) -> bool:
        """Delete a remote file."""
        if self.is_sftp:
            with self._connect() as ftp:
                ftp.remove(file_path)
        else:
            with self._connect() as ftp:
                ftp.delete(file_path)
        return True

    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename (or move) a remote file."""
        if self.is_sftp:
            with self._connect() as ftp:
                ftp.rename(old_path, new_path)
        else:
            with self._connect() as ftp:
                ftp.rename(old_path, new_path)
        return True

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists on the remote server."""
        if self.is_sftp:
            try:
                with self._connect() as ftp:
                    ftp.stat(file_path)
                return True
            except IOError:
                return False
        else:
            try:
                with self._connect() as ftp:
                    ftp.size(file_path)
                return True
            except error_perm:
                return False

    def create_directory(self, directory: str) -> bool:
        """Create a directory on the remote server."""
        if self.is_sftp:
            with self._connect() as ftp:
                try:
                    ftp.mkdir(directory)
                except IOError:
                    # directory might already exist
                    pass
        else:
            with self._connect() as ftp:
                try:
                    ftp.mkd(directory)
                except error_perm:
                    # directory might already exist
                    pass
        return True
