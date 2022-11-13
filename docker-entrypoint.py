import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, List, Literal, Optional, overload, TypeVar, Union, Dict
from urllib import request
from urllib.parse import urlencode
from enum import Enum


class DBType(Enum):
    mysql = "mysql"
    postgres = "pgsql"
    sqlite = "sqlite"


@dataclass
class EnvVars:
    prettyurls: bool
    https: bool
    httpsredirect: bool
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


def truish(value: Optional[str]) -> bool:
    """
    Check if a value is close enough to true
    """
    if value is None:
        return False

    return value.lower().strip() in ["true", "yes", "1"]


def print2(msg: Any) -> None:
    """
    Print a message to stdout.
    """
    print(f"[NV_INIT] {msg}", file=sys.stderr)


T = TypeVar("T")


@overload
def get_environment_variable(
    key: str, default: None = None, alternates: Optional[List[str]] = None
) -> Optional[str]:
    ...


@overload
def get_environment_variable(
    key: str, default: T = None, alternates: Optional[List[str]] = None
) -> T:
    ...


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
            if get_environment_variable(a) is not None:
                return a

    # return default value
    print2(f"{key} NOT found in environment variables, using default: {default}")
    return default


ENV = EnvVars(
    prettyurls=truish(get_environment_variable("PRETTY_URLS")),
    https=truish(get_environment_variable("HTTPS", alternates=["SSL"])),
    httpsredirect=truish(
        get_environment_variable("HTTPS_REDIRECT", alternates=["SSL_REDIRECT"])
    ),
    baseurl=get_environment_variable("BASE_URL"),
    lang=get_environment_variable("LANG", "en-US"),
    dbtype=DBType[get_environment_variable("DB_TYPE", "mysql")],
    dbhost=get_environment_variable("DB_HOST"),
    dbport=get_environment_variable("DB_PORT", "3306"),
    dbuser=get_environment_variable(
        "DB_USER", "webtrees", alternates=["MYSQL_USER", "MARIADB_USER"]
    ),
    dbpass=get_environment_variable(
        "DB_PASS", alternates=["MYSQL_PASSWORD", "MARIADB_PASSWORD"]
    ),
    dbname=get_environment_variable(
        "DB_NAME",
        default="webtrees",
        alternates=["MYSQL_DATABASE", "MARIADB_DATABASE"],
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
)

ROOT = "/var/www/webtrees"
CONFIG_FILE = os.path.join(ROOT, "data", "config.ini.php")

os.chdir(ROOT)


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

    # read file
    with open(CONFIG_FILE, "r") as fp:
        lines = fp.readlines()

    # replace matching line
    replacement = f'{key}="{value}"\n'
    found = False

    for i, line in enumerate(lines):
        if line.startswith(key):
            if line == replacement:
                return

            lines[i] = replacement
            found = True
            break

    if not found:
        lines.append(replacement)

    # write new contents
    with open(CONFIG_FILE, "w") as fp:
        fp.writelines(lines)


def enable_apache_site(
    enable_sites: List[Literal["webtrees", "webtrees-redir", "webtrees-ssl"]]
) -> None:
    """
    Enable an Apache site.
    """
    # TODO, accept cert path via env
    all_sites = ["webtrees", "webtrees-redir", "webtrees-ssl"]

    # perl complains about locale to stderr, so disable that

    # disable the other sites
    for s in all_sites:
        if s not in enable_sites:
            print2(f"Disabling site {s}")
            subprocess.check_call(["a2dissite", s], stderr=subprocess.DEVNULL)

    # enable the desired sites
    for s in enable_sites:
        print2(f"Enabling site {s}")
        subprocess.check_call(["a2ensite", s], stderr=subprocess.DEVNULL)


def perms() -> None:
    """
    Set up folder permissions
    """

    print2("Setting up folder permissions for uploads")

    subprocess.check_call(["chown", "-R", "www-data:www-data", "data"])
    subprocess.check_call(["chmod", "-R", "755", "data"])
    subprocess.check_call(["chown", "-R", "www-data:www-data", "media"])
    subprocess.check_call(["chmod", "-R", "755", "media"])

    if os.path.isfile(CONFIG_FILE):
        subprocess.check_call(["chmod", "700", CONFIG_FILE])


def check_db_variables() -> bool:
    """
    Check if all required database variables are present
    """
    try:
        assert ENV.dbtype is not None
        assert ENV.dbname is not None
        assert ENV.tblpfx is not None

        if ENV.dbtype in [DBType.mysql, DBType.postgres]:
            assert ENV.dbhost is not None
            assert ENV.dbport is not None
            assert ENV.dbuser is not None
            assert ENV.dbpass is not None

        elif ENV.dbtype ==  DBType.sqlite:
            ENV.dbhost = ""
            ENV.dbport = ""
            ENV.dbuser = ""
            ENV.dbpass = ""

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

    print2("Automating setup wizard")
    print2("Starting Apache in background")
    # set us up to a known HTTP state
    enable_apache_site(["webtrees"])
    # run apache in the background
    apache_proc = subprocess.Popen(["apache2-foreground"])

    # wait until database is ready
    if ENV.dbtype == DBType.mysql:
        while (
            subprocess.run(
                ["mysqladmin", "ping", f"-h{ENV.dbhost}", "--silent"]
            ).returncode
            != 0
        ):
            print2("Waiting for MySQL server to be ready")
            time.sleep(1)

    elif ENV.dbtype == DBType.postgres:
        print2("Waiting 10 seconds arbitrarily for database server to be ready")
        time.sleep(10)
    else:
        # let Apache start up
        time.sleep(2)

    # send it
    print2("Sending setup wizard request")

    resp = request.urlopen(
        # use 127.0.0.1 in case user is using host networking mode
        "http://127.0.0.1:80/",
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

    assert resp.status == 200

    print2("Stopping Apache")
    apache_proc.terminate()


def update_config_file():
    """
    Update the config file with items set via environment variables
    """
    print2("Updating config file")

    if not os.path.isfile(CONFIG_FILE):
        raise FileNotFoundError(
            f"Config file not found at {CONFIG_FILE}. This should not happen."
        )

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


def https():
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


def htaccess():
    """
    Recreate .htaccess file if it ever deletes itself in the /data/ directory
    """
    htaccess_file = os.path.join(ROOT, "data", ".htaccess")

    if os.path.isfile(htaccess_file):
        return

    print2(f"WARNING: {htaccess_file} does not exist")

    with open(htaccess_file, "w") as fp:
        fp.writelines(["order allow,deny", "deny from all"])

    print2(f"Created {htaccess_file}")


def main():
    # first, set up permissions
    perms()
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
    subprocess.run(["apache2-foreground"])


if __name__ == "__main__":
    main()
