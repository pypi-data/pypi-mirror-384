import io
import paramiko
import pandas as pd
from io import StringIO
import traceback
import logging
import stat
import chardet
import zipfile
import os
from afl_ai_utils.logging_utils import setup_logger, clean_up_logger

logger = setup_logger("afl_ai_utils", log_file="afl_ai_utils.log", level=logging.DEBUG)

class SFTPUtils:
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    def list_files_and_dirs(self, remote_dir:str):
        print(f'Get the list of files from {remote_dir}')
        directory_structure = {}
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        # Get directory structure
        # directory_structure = list_files_and_dirs(sftp, remote_dir)
        for item in sftp.listdir_attr(remote_dir):
            item_path = f"{remote_dir}/{item.filename}"
            # logger.info(directory_structure)
            if stat.S_ISDIR(item.st_mode):
                # Recursive call to list files and dirs in subdirectories
                # print(item_path , "--> ", item.filename)
                directory_structure[item.filename] = self.list_files_and_dirs(remote_dir=item_path)
                # print(directory_structure)
            else:
                if '__files__' not in directory_structure:
                    directory_structure['__files__'] = []
                directory_structure['__files__'].append(item.filename)
        # Close the SFTP session and SSH client
        sftp.close()
        transport.close()
        print('Successfully list out the files from the Path')
        return directory_structure

    def print_directory_structure(self, directory_structure: dict, indent=""):
        for key, value in directory_structure.items():
            if key == '__files__':
                for file in value:
                    logger.info(f"{indent}/{file}")
            else:
                print(f"{indent}/{key}")
                self.print_directory_structure(value, indent + f"/{key}")

    def read_from_sftp_server(self, file_path):
        transport = paramiko.Transport((self.host, int(self.port)))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        df = None

        try:
            if sftp.stat(file_path):
                logger.info(f"Reading the file from SFTP server: {file_path}")

                # Read the file in binary mode
                with sftp.file(file_path, 'rb') as file:
                    file_content = file.read()

                    # Check if the file is a ZIP file
                    if file_path.endswith('.zip'):
                        with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                            # Assuming there's only one file in the ZIP archive
                            zip_info = z.infolist()[0]
                            with z.open(zip_info) as csv_file:
                                df = pd.read_csv(csv_file)
                    else:
                        # Detect the encoding
                        result = chardet.detect(file_content)
                        detected_encoding = result['encoding']
                        logger.info(f"Detected encoding: {detected_encoding}")

                        # Decode the content with the detected encoding
                        decoded_content = file_content.decode(detected_encoding, errors='ignore')
                        buffer = io.StringIO(decoded_content)
                        df = pd.read_csv(buffer)

                    logger.info(f"File read successfully. Number of rows: {len(df)}")
            else:
                logger.info(f"File {file_path} doesn't exist on SFTP server: {file_path}")

        except Exception as e:
            logger.error(f"Error reading file {file_path} from SFTP server: {e}")

        finally:
            sftp.close()
            transport.close()

        return df

    def write_to_sftp_server(self, remote_path: str, dataframe: pd.DataFrame):
        try:
            csv_string = dataframe.to_csv(index=False)
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.host, self.port, self.username, self.password)
            sftp = ssh_client.open_sftp()
            csv_buffer = StringIO(csv_string)
            with sftp.file(remote_path, "w") as file:
                file.write(csv_buffer.getvalue())
            sftp.close()
            ssh_client.close()
            logger.info("Data written successfully to", remote_path)
        except Exception as e:
            print("Error:", str(e), "---> ", traceback.format_exc())

    def delete_sftp_file(self, remote_path: str):
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.remove(remote_path)
            sftp.close()
            transport.close()
            logger.info(f"File has been deleted successfully for {remote_path}")
        except Exception as e:
            print("Error:", str(e), "---> ", traceback.format_exc())



    def delete_file_from_sftp_server(self, remote_path: str):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.host, self.port, self.username, self.password)
            sftp = ssh_client.open_sftp()
            sftp.remove(remote_path)
            sftp.close()
            ssh_client.close()
            logger.info(f"File has been deleted successfully for {remote_path}")
        except Exception as e:
            print("Error:", str(e), "---> ", traceback.format_exc())

    def copy_file_from_sftp_server(self,remote_path:str,dest_path:str):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.host, self.port, self.username, self.password)
            sftp = ssh_client.open_sftp()
            dest_file_path =[]
            for file in sftp.listdir_attr(remote_path):
                if stat.S_ISREG(file.st_mode):
                    file_path = remote_path + "/" + file.filename
                    local_file = dest_path +"/"+ file.filename
                    print(f"Attempting to copy from {file_path} to {dest_path}")
                    sftp.get(remotepath=file_path, localpath=local_file)
                    dest_file_path.append(file.filename)
            sftp.close()
            ssh_client.close()
            return dest_file_path
        except Exception as e:
            print("Error:", str(e), "---> ", traceback.format_exc())

    def copy_particular_files_from_sftp_server(self, remote_file_list: list, remote_folder_path: str, dest_path: str):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.host, self.port, self.username, self.password)
            sftp = ssh_client.open_sftp()

            dest_file_path = []  # initialize list

            for file in remote_file_list:
                file_path = f"{remote_folder_path}/{file}".strip()
                local_file = os.path.join(dest_path, file)
                print(f"Attempting to copy from {file_path} → {local_file}")

                try:
                    sftp.get(remotepath=file_path, localpath=local_file)
                    print(f"✅ Successfully copied {file}")
                    dest_file_path.append(local_file)
                except FileNotFoundError:
                    print(f"❌ File not found on SFTP: {file_path}")
                except Exception as e:
                    print(f"⚠️ Error while downloading {file}: {e}")

            sftp.close()
            ssh_client.close()

            return dest_file_path

        except Exception as e:
            print(f"❌ Connection or general error: {e}")
            return []

    def move_file_within_sftp_server(self, remote_src : str, remote_dest : str):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(self.host, self.port, self.username, self.password)
            sftp = ssh_client.open_sftp()
            print(f"Attempting to move file from {remote_src} to {remote_dest }")
            sftp.rename(oldpath =remote_src, newpath=remote_dest )
            sftp.close()
            ssh_client.close()
        except Exception as e:
            print("Error:", str(e), "---> ", traceback.format_exc())


clean_up_logger(logger=logger)