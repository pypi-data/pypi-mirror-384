import venv
import os

def create_venv_unix_like(env_name="venv"):
    """
    Creates a Python virtual environment with the same behavior as
    'python -m venv <env_name>' on Unix-like systems (Linux/macOS).
    It ensures pip is installed and uses symbolic links.
    If the environment already exists, it skips creation.
    """
    env_path = os.path.join(os.getcwd(), env_name)

    if os.path.exists(env_path):
        print(f"Environment '{env_name}' already exists at {env_path}. Skipping creation.")
    else:
        print(f"Creating virtual environment '{env_name}' at {env_path}...")
        try:
            # with_pip=True: Ensures pip (and setuptools/wheel) are installed.
            # symlinks=True: Uses symbolic links for efficiency (default on non-Windows).
            builder = venv.EnvBuilder(with_pip=True, symlinks=True)
            builder.create(env_path)
            print(f"Environment '{env_name}' created successfully.")
        except Exception as e:
            print(f"Error creating environment: {e}")
