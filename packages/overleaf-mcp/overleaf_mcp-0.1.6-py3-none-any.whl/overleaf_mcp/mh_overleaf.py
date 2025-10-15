import os, tempfile, subprocess
import shutil
import dotenv


class MHOverleaf:
    def __init__(self, project_id, token, destination="my-overleaf-project"):
        self.project_id = project_id
        self.destination = destination
        self.token = token
        self.loaded = False
        self.clone_project()

    def clone_project(self):
        if os.path.isdir(self.destination):
            shutil.rmtree(self.destination)
        # Create a tiny askpass script that prints the token (no newline)
        helper = tempfile.NamedTemporaryFile("w", delete=False)
        helper.write('#!/bin/sh\nprintf "%s" "$OVERLEAF_TOKEN"\n')
        helper.flush()
        helper_name = helper.name
        helper.close()  # important on Windows; harmless on Unix
        os.chmod(helper_name, 0o700)

        env = os.environ.copy()
        env["GIT_ASKPASS"] = helper_name
        env["OVERLEAF_TOKEN"] = self.token
        env["GIT_TERMINAL_PROMPT"] = "0"  # never block for TTY input

        url = f"https://git@git.overleaf.com/{self.project_id}"

        try:
            subprocess.run(["git", "clone", url, self.destination], check=True, env=env)
        finally:
            try:
                os.remove(helper_name)
            except OSError:
                pass
        self.loaded = True

    def list_files(self):
        """List files in the cloned Overleaf project directory and subdirectories."""
        if not self.loaded:
            raise RuntimeError("Project not loaded. Make sure the project_id and token are correct.")
        file_list = []
        for root, dirs, files in os.walk(self.destination):
            for file in files:
                file_list.append(os.path.relpath(os.path.join(root, file), self.destination))

        file_list = [file for file in file_list if not '.git' in file]
        return file_list
    
    def read_file(self, filename):
        """Read the content of a specific file in the cloned Overleaf project."""
        if not self.loaded:
            raise RuntimeError("Project not loaded. Make sure the project_id and token are correct.")
        file_path = os.path.join(self.destination, filename)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File '{filename}' not found in the project directory.")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
        
    ##  TO-DO: Add a context manager to handle cleanup so that we don't have to rely on __del__
    def __del__(self):
        if self.loaded and os.path.isdir(self.destination):
            shutil.rmtree(self.destination)

if __name__ == "__main__":
    dotenv.load_dotenv()
    project_id = os.getenv("PROJECT_ID")
    token = os.getenv("OVERLEAF_TOKEN")
    overleaf = MHOverleaf(project_id, token)
    files = overleaf.list_files()
    print("Files in project:", files)
    file = overleaf.read_file("main.tex")
    print("Content of main.tex:", file)
