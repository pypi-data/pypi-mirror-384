import os

from solidipes.mounters.cloud import Mounter, get_cloud_dir_path
from solidipes.utils import solidipes_logging as logging

################################################################

print = logging.invalidPrint
logger = logging.getLogger()

################################################################


class JuiceFSSQLiteMounter(Mounter):
    """JuiceFS file system, local database."""

    parser_key = "juicefs_local"

    def mount(self, path, mount_info, **kwargs) -> None:
        database_filename = f"{self.mount_id}.db"
        database_path = os.path.join(get_cloud_dir_path(), database_filename)
        database_url = f"sqlite3://{database_path}"
        bucket_url = f"{mount_info['endpoint_url'].rstrip('/')}/{mount_info['bucket_name']}"

        os.environ["AWS_ACCESS_KEY"] = mount_info["access_key_id"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = mount_info["secret_access_key"]

        # Create database file and remote directory if first time mount
        if not os.path.exists(database_path):
            remote_dir_name = mount_info.get("remote_dir_name", self.mount_id)
            cmd = [
                "juicefs",
                "format",
                "--storage",
                "s3",
                "--bucket",
                bucket_url,
                database_url,
                remote_dir_name,
            ]
            self.run_and_check_return(cmd, fail_message="Formatting failed")

        # Mount S3 bucket
        cmd = [
            "juicefs",
            "mount",
            "--background",
            database_url,
            path,
        ]
        self.run_and_check_process(cmd, fail_message="Mounting failed")


################################################################


class JuiceFSPSQLMounter(Mounter):
    """JuiceFS file system, remote psql database."""

    parser_key = "juicefs"

    def mount(self, path, mount_info=None, allow_root=False, **kwargs) -> None:
        # Create mount_id (if necessary), used to find database file

        logger.info(mount_info)
        if mount_info is None:
            mount_info = self.get_existing_mount_info(path)
        logger.info(mount_info)
        # Create directory if it does not exist
        if not os.path.exists(path):
            os.makedirs(path)

        # Create mount_id (if necessary), used to find database file
        # mount_id = get_mount_id(mount_info)
        database_url = mount_info["database_url"]
        if not database_url.startswith("postgres://"):
            raise RuntimeError(f"Inconsistent database url: {database_url}")

        logger.debug(database_url)
        protocol, url = database_url.split("://")
        host = url.split("/")[0]
        # database_name = url.split("/")[1].split("?")[0]
        database_name = "dcsm"
        port = 5432

        if "username" in mount_info:
            username = mount_info["username"]
        elif "DCSM_USERNAME" in os.environ:
            username = os.environ["DCSM_USERNAME"]
        else:
            raise RuntimeError("Cannot find DCSM username")
        database_url = (
            protocol
            + "://"
            + username
            + "@"
            + url
            + "/"
            + database_name
            + f"?sslmode=disable&search_path=juicefs-{self.mount_id}"
        )
        logger.debug(url)
        logger.debug(host)
        logger.debug(database_name)

        if "password" in mount_info:
            psql_password = mount_info["password"]
        elif "DCSM_PASSWORD" in os.environ:
            psql_password = os.environ["DCSM_PASSWORD"]
        else:
            raise RuntimeError("Cannot find DCSM password")

        import argparse

        psql_config = argparse.Namespace(
            database=database_name, host=host, port=port, username=username, password=psql_password
        )
        conn = self.connect_to_postgres(psql_config)
        cursor = conn.cursor()
        from psycopg2 import sql

        if username == "admin":
            mount_info_query = sql.SQL("SELECT * from storage where mount_id = {mount_id}").format(
                mount_id=sql.Literal(f"juicefs-{self.mount_id}")
            )
            logger.debug(mount_info_query)
            cursor.execute(mount_info_query)
            db_mount_info = [i for i in cursor][0]
            logger.debug(db_mount_info)
            _, _, _, _, access_key, secret_key = db_mount_info
        else:
            mount_info_query = sql.SQL("SELECT * from {username}.user_mounts where mount_id = {mount_id}").format(
                username=sql.Identifier(username), mount_id=sql.Literal(f"juicefs-{self.mount_id}")
            )
            logger.debug(mount_info_query)
            cursor.execute(mount_info_query)
            db_mount_info = [i for i in cursor]
            logger.info(db_mount_info)
            db_mount_info = db_mount_info[0]
            logger.debug(db_mount_info)
            _, _, access_key, secret_key = db_mount_info

        env = {"META_PASSWORD": psql_password, "AWS_ACCESS_KEY": access_key, "AWS_SECRET_ACCESS_KEY": secret_key}
        logger.error(env)
        env.update(os.environ)

        cmd = ["juicefs", "mount", "--background"]

        if allow_root:
            cmd += [
                "-o",
                "allow_root",
            ]

        cmd += [
            database_url,
            path,
        ]

        logger.debug(cmd)
        # Mount S3 bucket
        self.run_and_check_return(cmd, fail_message="Mounting failed")

        # Remove keys from database
        cmd = [
            "juicefs",
            "config",
            database_url,
            "--access-key",
            "",
            "--secret-key",
            "",
            "--force",  # Skip keys validation
        ]
        self.run_and_check_return(cmd, fail_message="Failed to remove keys from database")

    def connect_to_postgres(self, psql_config):
        import psycopg2

        database_name = psql_config.database
        HOST = psql_config.host
        PORT = psql_config.port
        ADMIN_USERNAME = psql_config.username
        ADMIN_PASSWORD = psql_config.password

        try:
            connection = psycopg2.connect(
                host=HOST,
                port=PORT,
                user=ADMIN_USERNAME,
                password=ADMIN_PASSWORD,
                database=database_name,
            )
            connection.autocommit = True

        except Exception as e:
            message = f"Error connecting to Postgres: {e}"
            raise RuntimeError(message).with_traceback(e.__traceback__)

        return connection
