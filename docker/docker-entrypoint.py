import os
import socket
import subprocess
import sys
import time
import urllib.error
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Literal, Optional, TypeVar, Union, overload
from urllib import request
from urllib.parse import urlencode


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class DBType(Enum):
    mysql = "mysql"
    pgsql = "pgsql"
    sqlite = "sqlite"


@dataclass
class EnvVars:
    prettyurls: bool
    https: bool
    httpsredirect: bool
    sslcertfile: str
    sslcertkeyfile: str
    lang: str
    baseurl: Optional[str]
    dbtype: DBType
    dbhost: Optional[str]
    dbport: str
    dbuser: str
    dbpass: Optional[str]
    dbname: str
    tblpfx: str
    wtuser: Optional[str]
    wtname: Optional[str]
    wtpass: Optional[str]
    wtemail: Optional[str]
    # https://github.com/fisharebest/webtrees/blob/f9a3af650116d75f1a87f454cabff5e9047e43f3/app/Http/Middleware/UseDatabase.php#L71-L82
    dbkey: Optional[str]
    dbcert: Optional[str]
    dbca: Optional[str]
    dbverify: bool
    # php settings
    phpmemorylimit: str
    phpmaxexecutiontime: str
    phppostmaxsize: str
    phpuploadmaxfilesize: str
    # user/group ID
    puid: str
    pgid: str


def truish(value: Optional[str]) -> bool:
    """
    Check if a value is close enough to true
    """
    if value is None:
        return False

    return value.lower().strip() in ["true", "yes", "1"]


def print2(msg: Any) -> None:
    """
    Print a message to stderr.
    """
    print(f"[NV_INIT] {msg}", file=sys.stderr)


T = TypeVar("T")


@overload
def get_environment_variable(
    key: str, default: None = None, alternates: Optional[List[str]] = None
) -> Optional[str]: ...


@overload
def get_environment_variable(
    key: str, default: T = None, alternates: Optional[List[str]] = None
) -> T: ...


def get_environment_variable(
    key: str, default: Optional[T] = None, alternates: Optional[List[str]] = None
) -> Union[Optional[str], T]:
    """
    Try to find the value of an environment variable.
    """
    key = key.upper()

    # try to find variable in env
    if key in os.environ:
        value = os.environ[key]

        print2(f"{key} found in environment variables")
        return value

    # try to find file version of variable
    file_key = f"{key}_FILE"

    if file_key in os.environ:
        # file name does not exist
        if not os.path.isfile(os.environ[file_key]):
            print(f"WARNING: {file_key} is not a file: {os.environ[file_key]}")
            return None

        # read data from file
        with open(os.environ[file_key], "r") as f:
            value = f.read().strip()

        print2(f"{file_key} found in environment variables")
        return value

    # try to find alternate variable
    if alternates is not None:
        for a in alternates:
            a_value = get_environment_variable(a)
            if a_value is not None:
                return a_value

    # return default value
    print2(f"{key} NOT found in environment variables, using default: {default}")
    return default


ENV = EnvVars(
    prettyurls=truish(get_environment_variable("PRETTY_URLS")),
    https=truish(get_environment_variable("HTTPS", alternates=["SSL"])),
    httpsredirect=truish(
        get_environment_variable("HTTPS_REDIRECT", alternates=["SSL_REDIRECT"])
    ),
    sslcertfile=get_environment_variable("SSL_CERT_FILE", "/certs/webtrees.crt"),
    sslcertkeyfile=get_environment_variable("SSL_CERT_KEY_FILE", "/certs/webtrees.key"),
    baseurl=get_environment_variable("BASE_URL"),
    lang=get_environment_variable("LANG", "en-US"),
    dbtype=DBType[get_environment_variable("DB_TYPE", "mysql")],
    dbhost=get_environment_variable("DB_HOST"),
    dbport=get_environment_variable("DB_PORT", "3306"),
    dbuser=get_environment_variable(
        "DB_USER",
        "webtrees",
        alternates=["MYSQL_USER", "MARIADB_USER", "POSTGRES_USER"],
    ),
    dbpass=get_environment_variable(
        "DB_PASS",
        alternates=["MYSQL_PASSWORD", "MARIADB_PASSWORD", "POSTGRES_PASSWORD"],
    ),
    dbname=get_environment_variable(
        "DB_NAME",
        default="webtrees",
        alternates=["MYSQL_DATABASE", "MARIADB_DATABASE", "POSTGRES_DB"],
    ),
    tblpfx=get_environment_variable("DB_PREFIX", "wt_"),
    wtuser=get_environment_variable("WT_USER"),
    wtname=get_environment_variable("WT_NAME"),
    wtpass=get_environment_variable("WT_PASS"),
    wtemail=get_environment_variable("WT_EMAIL"),
    dbkey=get_environment_variable("DB_KEY"),
    dbcert=get_environment_variable("DB_CERT"),
    dbca=get_environment_variable("DB_CA"),
    dbverify=truish(get_environment_variable("DB_VERIFY")),
    phpmemorylimit=get_environment_variable("PHP_MEMORY_LIMIT", "1024M"),
    phpmaxexecutiontime=get_environment_variable("PHP_MAX_EXECUTION_TIME", "90"),
    phppostmaxsize=get_environment_variable("PHP_POST_MAX_SIZE", "50M"),
    phpuploadmaxfilesize=get_environment_variable("PHP_UPLOAD_MAX_FILE_SIZE", "50M"),
    puid=get_environment_variable("PUID", "33"),  # www-data user
    pgid=get_environment_variable("PGID", "33"),
)


ROOT = "/var/www/webtrees"
DATA_DIR = os.path.join(ROOT, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.ini.php")
PHP_INI_FILE = "/usr/local/etc/php/php.ini"

os.chdir(ROOT)


def retry_urlopen(url: str, data: bytes) -> None:
    """
    Retry a request until a postiive repsonse code is reached. Raises error if it fails.
    """
    opener = request.build_opener(NoRedirect)
    request.install_opener(opener)

    for try_ in range(10):
        try:
            # make request
            print2(f"Attempt {try_} for {url}")
            resp = request.urlopen(url, data)
        except urllib.error.HTTPError as e:
            # capture error as well
            resp = e
            print2(f"Recieved HTTP {resp.status} response")

        # check status code
        # 302 is also accpetable in case the user selected something other than port 80
        if resp.status in (200, 302):
            return

        # backoff
        time.sleep(try_)

    raise RuntimeError(f"Could not send a request to {url}")


def add_line_to_file(filename: str, newline: str) -> None:
    """
    Add a new line to a file. If an existing line is found with the same
    starting string, it will be replaced.
    """
    newline += "\n"

    # read file
    with open(filename, "r") as fp:
        lines = fp.readlines()

    key = newline.split("=")[0]

    # replace matching line
    found = False

    for i, line in enumerate(lines):
        if line.startswith(key):
            if line == newline:
                return

            lines[i] = newline
            found = True
            break

    if not found:
        lines.append(newline)

    # write new contents
    with open(filename, "w") as fp:
        fp.writelines(lines)


def set_config_value(key: str, value: Optional[str]) -> None:
    """
    In the config file, make sure the given key is set to the given value.
    """
    if value is None:
        return

    print2(f"Setting value for {key} in config")

    if not os.path.isfile(CONFIG_FILE):
        print2(f"WARNING: {CONFIG_FILE} does not exist")
        return

    add_line_to_file(CONFIG_FILE, f'{key}="{value}"')


def set_php_ini_value(key: str, value: str) -> None:
    """
    In the php.ini file, make sure the given key is set to the given value.
    """
    print2(f"Setting value for {key} in php.ini")
    add_line_to_file(PHP_INI_FILE, f"{key} = {value}")


def enable_apache_site(
    enable_sites: List[Literal["webtrees", "webtrees-redir", "webtrees-ssl"]],
) -> None:
    """
    Enable an Apache site.
    """

    # update ssl apache config with cert path from env
    ssl_site_file = "/etc/apache2/sites-available/webtrees-ssl.conf"

    # make paths absolute
    if not os.path.isabs(ENV.sslcertfile):
        ENV.sslcertfile = os.path.join(DATA_DIR, ENV.sslcertfile)

    if not os.path.isabs(ENV.sslcertkeyfile):
        ENV.sslcertkeyfile = os.path.join(DATA_DIR, ENV.sslcertkeyfile)

    # update file
    with open(ssl_site_file, "r") as fp:
        ssl_site_file_lines = fp.readlines()

    new_ssl_site_file_lines = []
    for line in ssl_site_file_lines:
        if line.strip().startswith("SSLCertificateFile"):
            line = line.replace(line.split()[1], ENV.sslcertfile)
        elif line.strip().startswith("SSLCertificateKeyFile"):
            line = line.replace(line.split()[1], ENV.sslcertkeyfile)

        new_ssl_site_file_lines.append(line)

    with open(ssl_site_file, "w") as fp:
        fp.writelines(new_ssl_site_file_lines)

    all_sites = ["webtrees", "webtrees-redir", "webtrees-ssl"]

    # perl complains about locale to stderr, so disable that

    # disable the other sites
    for s in all_sites:
        if s not in enable_sites:
            print2(f"Disabling site {s}")
            subprocess.check_call(
                ["a2dissite", s], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

    # enable the desired sites
    for s in enable_sites:
        print2(f"Enabling site {s}")
        subprocess.check_call(
            ["a2ensite", s], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def perms() -> None:
    """
    Set up folder permissions
    """

    print2("Setting up folder permissions for uploads")
    # https://github.com/linuxserver/docker-baseimage-alpine/blob/bef0f4cee208396c92c0fdd1426613de02698301/root/etc/s6-overlay/s6-rc.d/init-adduser/run#L4-L9
    subprocess.check_call(["groupmod", "-o", "-g", ENV.pgid, "www-data"])
    subprocess.check_call(["usermod", "-o", "-u", ENV.puid, "www-data"])
    subprocess.check_call(["chown", "-R", "www-data:www-data", DATA_DIR])

    if os.path.isfile(CONFIG_FILE):
        subprocess.check_call(["chmod", "700", CONFIG_FILE])


def php_ini() -> None:
    """
    Update PHP .ini file
    """
    print2("Updating php.ini")

    if not os.path.isfile(PHP_INI_FILE):
        print2("Creating php.ini")

        os.makedirs(os.path.dirname(PHP_INI_FILE), exist_ok=True)
        with open(PHP_INI_FILE, "w") as fp:
            fp.writelines(["[PHP]\n", "\n"])

    set_php_ini_value("memory_limit", ENV.phpmemorylimit)
    set_php_ini_value("max_execution_time", ENV.phpmaxexecutiontime)
    set_php_ini_value("post_max_size", ENV.phppostmaxsize)
    set_php_ini_value("upload_max_filesize", ENV.phpuploadmaxfilesize)

    # https://webtrees.net/admin/performance/
    set_php_ini_value("opcache.enable", "1")
    set_php_ini_value("opcache.revalidate_freq", "60") # re check changed files every 60 seconds
    set_php_ini_value("opcache.revalidate_path", "0")


def check_db_variables() -> bool:
    """
    Check if all required database variables are present
    """
    try:
        assert ENV.dbtype is not None
        assert ENV.dbname is not None
        assert ENV.tblpfx is not None

        if ENV.dbtype == DBType.sqlite:
            ENV.dbhost = ""
            ENV.dbport = ""
            ENV.dbuser = ""
            ENV.dbpass = ""

        assert ENV.dbhost is not None
        assert ENV.dbport is not None
        assert ENV.dbuser is not None
        assert ENV.dbpass is not None

    except AssertionError:
        print2("WARNING: Not all database variables are set")
        return False

    return True


def setup_wizard() -> None:
    """
    Run the setup wizard
    """

    if os.path.isfile(CONFIG_FILE):
        return

    print2("Attempting to automate setup wizard")

    # make sure all the variables we need are not set to None
    if not check_db_variables():
        return

    if any(
        v is None
        for v in [ENV.baseurl, ENV.wtname, ENV.wtuser, ENV.wtpass, ENV.wtemail]
    ):
        print2("WARNING: Not all required variables were found for setup wizard")
        return

    assert ENV.baseurl is not None
    if not ENV.baseurl.startswith("http"):
        print2(
            "WARNING: BASE_URL does not start with 'http'. This is likely not what you want."
        )

    print2("Automating setup wizard")
    print2("Starting Apache in background")
    # set us up to a known HTTP state
    enable_apache_site(["webtrees"])
    # run apache in the background
    apache_proc = subprocess.Popen(["apache2-foreground"], stderr=subprocess.DEVNULL)

    if ENV.dbtype in [DBType.mysql, DBType.pgsql]:
        # for typing, check_db_variables already does this
        assert ENV.dbhost is not None

        # try to resolve the host
        # most common error is wrong hostname
        try:
            socket.gethostbyname(ENV.dbhost)
        except socket.gaierror:
            print2(f"ERROR: Could not resolve database host '{ENV.dbhost}'")
            print2(
                "ERROR: You likely have the DBHOST environment variable set incorrectly."
            )
            print2("ERROR: Exiting.")

            # stop apache
            apache_proc.terminate()
            # die
            sys.exit(1)

        # wait until database is ready
        if ENV.dbtype == DBType.mysql:
            # https://dev.mysql.com/doc/refman/8.0/en/mysqladmin.html#option_mysqladmin_user
            # don't miss the capital P
            cmd = ["mysqladmin", "ping", "-h", ENV.dbhost, "-P", ENV.dbport, "--silent"]
            name = "MySQL"
        elif ENV.dbtype == DBType.pgsql:
            # https://www.postgresql.org/docs/current/app-pg-isready.html
            cmd = ["pg_isready", "-h", ENV.dbhost, "-p", ENV.dbport, "--quiet"]
            name = "PostgreSQL"

        while subprocess.run(cmd).returncode != 0:
            print2(f"Waiting for {name} server {ENV.dbhost}:{ENV.dbport} to be ready")
            time.sleep(1)

    else:
        # sqlite
        # let Apache start up
        time.sleep(2)

    # send it
    url = "http://127.0.0.1:80/"
    print2(f"Sending setup wizard request to {url}")

    retry_urlopen(
        url,
        urlencode(
            {
                "lang": ENV.lang,
                "tblpfx": ENV.tblpfx,
                "baseurl": ENV.baseurl,
                "dbtype": ENV.dbtype.value,
                "dbhost": ENV.dbhost,
                "dbport": ENV.dbport,
                "dbuser": ENV.dbuser,
                "dbpass": ENV.dbpass,
                "dbname": ENV.dbname,
                "wtname": ENV.wtname,
                "wtuser": ENV.wtuser,
                "wtpass": ENV.wtpass,
                "wtemail": ENV.wtemail,
                "step": "6",
            }
        ).encode("ascii"),
    )

    print2("Stopping Apache")
    apache_proc.terminate()


def update_config_file() -> None:
    """
    Update the config file with items set via environment variables
    """
    print2("Updating config file")

    if not os.path.isfile(CONFIG_FILE):
        print2(f"Config file not found at {CONFIG_FILE}. Nothing to update.")
        return

    # update independent values
    set_config_value("rewrite_urls", str(int(ENV.prettyurls)))
    set_config_value("base_url", ENV.baseurl)

    # update database values as a group
    if check_db_variables():
        set_config_value("dbtype", ENV.dbtype.value)
        set_config_value("dbhost", ENV.dbhost)
        set_config_value("dbport", ENV.dbport)
        set_config_value("dbuser", ENV.dbuser)
        set_config_value("dbpass", ENV.dbpass)
        set_config_value("dbname", ENV.dbname)
        set_config_value("tblpfx", ENV.tblpfx)

    # update databases verification values
    if ENV.dbtype == DBType.mysql and all(
        v is not None for v in [ENV.dbkey, ENV.dbcert, ENV.dbca]
    ):
        set_config_value("dbkey", ENV.dbkey)
        set_config_value("dbcert", ENV.dbcert)
        set_config_value("dbca", ENV.dbca)
        set_config_value("dbverify", str(int(ENV.dbverify)))


def https() -> None:
    """
    Configure enabled Apache sites
    """
    print2("Configuring HTTPS")

    # no https
    if not ENV.https:
        print2("Removing HTTPS")
        enable_apache_site(["webtrees"])
    # https with redirect
    elif ENV.httpsredirect:
        print2("Adding HTTPS, with HTTPS redirect")
        enable_apache_site(["webtrees-ssl", "webtrees-redir"])
    # https no redirect
    else:
        print2("Adding HTTPS, removing HTTPS redirect")
        enable_apache_site(["webtrees", "webtrees-ssl"])


def htaccess() -> None:
    """
    Recreate .htaccess file if it ever deletes itself in the /data/ directory
    """
    htaccess_file = os.path.join(DATA_DIR, ".htaccess")

    if os.path.isfile(htaccess_file):
        return

    print2(f"WARNING: {htaccess_file} does not exist")

    with open(htaccess_file, "w") as fp:
        fp.writelines(["order allow,deny", "deny from all"])

    print2(f"Created {htaccess_file}")


def main() -> None:
    # first, set up permissions
    perms()
    # create php config
    php_ini()
    # run the setup wizard if the config file doesn't exist
    setup_wizard()
    # update the config file
    update_config_file()
    # configure https
    https()
    # make sure .htaccess exists
    htaccess()
    # set up permissions again
    perms()

    print2("Starting Apache")
    subprocess.run(["apache2-foreground"], stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
