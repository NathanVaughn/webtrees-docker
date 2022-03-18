import os
import subprocess
import sys
import time
from typing import Any, List, Literal, Optional
from urllib import request
from urllib.parse import urlencode

ROOT = "/var/www/webtrees"
CONFIG_FILE = os.path.join(ROOT, "data", "config.ini.php")

os.chdir(ROOT)


def print2(msg: Any) -> None:
    """
    Print a message to stdout.
    """
    print(f"[NV_INIT] {msg}", file=sys.stderr)


def truish(value: Optional[str]) -> bool:
    """
    Check if a value is close enough to true
    """
    if value is None:
        return False

    return value.lower().strip() in ["true", "yes", "1"]


def get_env(
    key: str, default: Optional[Any] = None, alternates: Optional[List[str]] = None
) -> Optional[Any]:
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
            if get_env(a) is not None:
                return a

    # return default value
    print2(f"{key} NOT found in environment variables, using default: {default}")
    return default


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


def perms():
    # set up folder permissions
    print2("Setting up folder permissions for uploads")
    subprocess.check_call(["chown", "-R", "www-data:www-data", "data"])
    subprocess.check_call(["chmod", "-R", "755", "data"])
    subprocess.check_call(["chown", "-R", "www-data:www-data", "media"])
    subprocess.check_call(["chmod", "-R", "755", "media"])

    if os.path.isfile(CONFIG_FILE):
        subprocess.check_call(["chmod", "700", CONFIG_FILE])


def setup_wizard():
    print2("Attempting to automate setup wizard")

    # values with defaults
    lang = get_env("LANG", "en-US")
    db_type = get_env("DB_TYPE", "mysql")
    db_port = get_env("DB_PORT", "3306")
    db_user = get_env("DB_USER", "webtrees", alternates=["MYSQL_USER", "MARIADB_USER"])
    db_name = get_env(
        "DB_NAME", "webtrees", alternates=["MYSQL_DATABASE", "MARIADB_DATABASE"]
    )
    table_prefix = get_env("DB_PREFIX", "wt_")

    # values without defaults
    db_host = get_env("DB_HOST")
    db_pass = get_env("DB_PASS", alternates=["MYSQL_PASSWORD", "MARIADB_PASSWORD"])
    base_url = get_env("BASE_URL")
    wt_name = get_env("WT_NAME")
    wt_user = get_env("WT_USER")
    wt_pass = get_env("WT_PASS")
    wt_email = get_env("WT_EMAIL")

    if os.path.isfile(CONFIG_FILE):
        print2("Config file already exists")

        # make sure all the variables we need are not set to None
        try:
            if db_type in ["mysql", "pgsql"]:
                assert db_host is not None
                assert db_port is not None
                assert db_user is not None
                assert db_pass is not None
            elif db_type == "sqlite":
                assert db_name is not None
                db_host = ""
                db_port = ""
                db_user = ""
                db_pass = ""
            else:
                raise ValueError(f"Unknown database type: {db_type}")

        except AssertionError:
            print2("WARNING: Not all required variables were found for database update")
            return

        print2("Updating config file")
        set_config_value("dbhost", db_host)
        set_config_value("dbport", db_port)
        set_config_value("dbuser", db_user)
        set_config_value("dbpass", db_pass)
        set_config_value("dbname", db_name)
        set_config_value("tblpfx", table_prefix)
        set_config_value("base_url", base_url)

    else:
        print2("Config file does NOT exist")

        # make sure all the variables we need are not set to None
        try:
            assert lang is not None
            assert table_prefix is not None
            assert base_url is not None

            assert wt_name is not None
            assert wt_user is not None
            assert wt_pass is not None
            assert wt_email is not None

            assert db_type is not None
            assert db_name is not None

            if db_type in ["mysql", "pgsql"]:
                assert db_host is not None
                assert db_port is not None
                assert db_user is not None
                assert db_pass is not None
            elif db_type == "sqlite":
                assert db_name is not None
                db_host = ""
                db_port = ""
                db_user = ""
                db_pass = ""
            else:
                raise ValueError(f"Unknown database type: {db_type}")

        except AssertionError:
            print2("WARNING: Not all required variables were found for setup wizard")
            return

        print2("Automating setup wizard")
        print2("Starting Apache in background")
        # set us up to a known HTTP state
        enable_apache_site(["webtrees"])
        # run apache in the background
        apache_proc = subprocess.Popen(["apache2-foreground"])

        # wait until database is ready
        if db_type == "mysql":
            while (
                subprocess.run(
                    ["mysqladmin", "ping", f"-h{db_host}", "--silent"]
                ).returncode
                != 0
            ):
                print2("Waiting for MySQL server to be ready")
                time.sleep(1)

        elif db_type != "sqlite":
            print2("Waiting 10 seconds arbitrarily for database server to be ready")
            time.sleep(10)
        else:
            # let Apache start up
            time.sleep(2)

        # send it
        print2("Sending setup wizard request")
        resp = request.urlopen(
            "http://127.0.0.1:80/",
            urlencode(
                {
                    "lang": lang,
                    "tblpfx": table_prefix,
                    "baseurl": base_url,
                    "dbtype": db_type,
                    "dbhost": db_host,
                    "dbport": db_port,
                    "dbuser": db_user,
                    "dbpass": db_pass,
                    "dbname": db_name,
                    "wtname": wt_name,
                    "wtuser": wt_user,
                    "wtpass": wt_pass,
                    "wtemail": wt_email,
                    "step": "6",
                }
            ).encode("ascii"),
        )

        assert resp.status == 200

        print2("Stopping Apache")
        apache_proc.terminate()


def pretty_urls():
    print2("Configuring pretty URLs")
    value = str(int(truish(get_env("PRETTY_URLS"))))
    set_config_value("rewrite_urls", value)


def https():
    print2("Configuring HTTPS")
    # no https
    if not truish(get_env("HTTPS", alternates=["SSL"])):
        print2("Removing HTTPS")
        enable_apache_site(["webtrees"])
    # https with redirect
    elif truish(get_env("HTTPS_REDIRECT", alternates=["SSL_REDIRECT"])):
        print2("Adding HTTPS, with HTTPS redirect")
        enable_apache_site(["webtrees-ssl", "webtrees-redir"])
    # https no redirect
    else:
        print2("Adding HTTPS, removing HTTPS redirect")
        enable_apache_site(["webtrees", "webtrees-ssl"])


def htaccess():
    htaccess_file = os.path.join(ROOT, "data", ".htaccess")

    if os.path.isfile(htaccess_file):
        return

    print2(f"WARNING: {htaccess_file} does not exist")

    with open(htaccess_file, "w") as fp:
        fp.writelines(["order allow,deny", "deny from all"])

    print2(f"Created {htaccess_file}")


def main():
    perms()
    setup_wizard()
    pretty_urls()
    https()
    htaccess()
    perms()

    print2("Starting Apache")
    subprocess.run(["apache2-foreground"])


if __name__ == "__main__":
    main()
