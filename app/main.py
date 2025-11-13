from utils import abspath
import subprocess


def run():
  subprocess.run(["streamlit", "run", abspath("app.py")])


if __name__ == "__main__":
  run()
