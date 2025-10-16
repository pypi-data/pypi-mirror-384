import shutil
from pathlib import Path

from plot_tree.common import ROOT_PATH
from plot_tree.default import CSV_FILE_NAME

source_path = ROOT_PATH / 'plot_tree' / 'child_parent_example.csv'

def create_example_csv(destination_dir: Path = Path.cwd()) -> None:
    destination_path = destination_dir / CSV_FILE_NAME

    shutil.copy(source_path, destination_path)
    print(f'example csv file created at: {destination_path}')


if __name__ == '__main__':
    create_example_csv(ROOT_PATH)
