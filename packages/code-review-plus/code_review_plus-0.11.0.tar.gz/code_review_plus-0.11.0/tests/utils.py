def load_environment_variables(environment_filename: str, source_folder_name: str = ".envs"):
    from pathlib import Path

    from dotenv import load_dotenv

    def find_envs_folder(current_dir: Path):
        env_folder = current_dir / source_folder_name
        if env_folder.exists():
            return env_folder
        return find_envs_folder(current_dir.parent)

    environment_folder = find_envs_folder(Path(__file__).parent)
    environment_file = environment_folder / environment_filename
    load_dotenv(dotenv_path=environment_file)
