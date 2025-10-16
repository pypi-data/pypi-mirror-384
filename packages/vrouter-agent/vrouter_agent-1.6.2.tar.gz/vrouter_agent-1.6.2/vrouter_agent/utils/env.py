import os


def load_env_variables(silent=False):
    try:
        # FIXME dotenv is not working, there is some dotenv plugin for poetry -> solve it more elegantly
        with open(".env") as input_file:
            for line in input_file:
                if not line.strip():  # ignoring empty lines
                    continue
                if line.startswith("#"):  # ignoring comment lines
                    continue
                key, value = line.partition("=")[::2]
                os.environ[key.strip()] = str(value).strip()
                if not silent:
                    print(
                        f"added env variable: {key.strip()}={str(value).strip()} (env reread: {os.environ.get(key.strip())})"
                    )
    except FileNotFoundError:
        print("input env file not present")
