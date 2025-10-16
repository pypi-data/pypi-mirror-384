import shutil

from plot_tree.common import ROOT_PATH
from plot_tree.default import CSV_FILE_NAME

source_path = ROOT_PATH / 'plot_tree' / 'child_parent_example.csv'
destination_path = ROOT_PATH / CSV_FILE_NAME


def create_example_csv():
    shutil.copy(source_path, destination_path)
    print(f'example csv file created at: {destination_path}')


if __name__ == '__main__':
    create_example_csv(source_path, destination_path)
