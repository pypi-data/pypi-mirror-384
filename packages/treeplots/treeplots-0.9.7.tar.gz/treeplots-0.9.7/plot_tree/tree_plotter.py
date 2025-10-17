import csv
import os
import re
import shutil
from pathlib import Path

import yaml
from anytree import Node, RenderTree
from anytree.exporter import DictExporter, MermaidExporter

from plot_tree.common import ROOT_PATH
from plot_tree.default import COL, CSV_FILE_NAME, OUTPUT_DIR_NAME

CSV_FILE = ROOT_PATH / CSV_FILE_NAME
OUTPUT_DIR = ROOT_PATH / OUTPUT_DIR_NAME


class TreePlotter():
    def __init__(
            self,
            child_id_col=COL.CHILD_ID, parent_id_col=COL.PARENT_ID, child_name_col=COL.CHILD_NAME, as_of_col=COL.AS_OF,
            csv_file=CSV_FILE, output_dir=OUTPUT_DIR
    ):
        self.child_id_col = child_id_col
        self.parent_id_col = parent_id_col
        self.child_name_col = child_name_col
        self.as_of_col = as_of_col
        self.csv_file = csv_file
        self.output_dir = output_dir

        self.nodes: dict[str, Node] = self.__load_nodes()
        self.roots: list[Node] = [node for node in self.nodes.values() if node.is_root]

    def plot(self):
        self.__console_output()

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

        for r in self.roots:
            self.plot_root(r)

    def __console_output(self):
        as_of_list = sorted({r.as_of for r in self.roots})

        for as_of in as_of_list:
            roots_as_of = [r for r in self.roots if r.as_of == as_of]
            print(f'\n\n{as_of}:')
            for r in roots_as_of:
                print(RenderTree(r).by_attr())

            print(f'\nAs of {as_of}, total nodes are {sum(r.size for r in roots_as_of)} and total roots are {len(roots_as_of)}')

    def __load_nodes(self) -> dict[str, Node]:
        nodes: dict[str, Node] = {}

        with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            for row in rows:
                child_id = row[self.child_id_col]
                parent_id = row[self.parent_id_col]
                child_name = row[self.child_name_col]
                as_of = row[self.as_of_col]

                node_id = f'{child_id}|{as_of}'

                nodes[node_id] = Node(f'{child_name} -- {child_id}',
                                      child_name=child_name, child_id=child_id,
                                      parent_id=parent_id, as_of=as_of)
        for node in nodes.values():
            if node.parent_id:
                parent_key = f'{node.parent_id}|{node.as_of}'
                if parent_key in nodes.keys():
                    node.parent = nodes[parent_key]

        return nodes

    def plot_root(self, root: Node):
        self.export_yaml(root)
        # self.export_dotpng(root)
        self.export_mermaid(root)
        self.export_text(root)

    def export_yaml(self, root: Node):
        file_dir = self.__makedir('yaml', root.as_of)
        file_path = file_dir / f'{self.__file_name(root)}.yml'

        exporter = DictExporter(attriter=lambda attrs: [(k, _) for k, _ in attrs if k == 'name'])
        data_dict = exporter.export(root)
        yaml_output = yaml.dump(data_dict, default_flow_style=False, sort_keys=False)

        with open(file_path, 'w') as file:
            file.write(yaml_output)

    # def export_dotpng(self, root: Node):
    # file_dir = self.__makedir('png', root.as_of)
    #
    # exporter = DotExporter(root,
    #                        options=['rankdir=LR'],
    #                        nodeattrfunc=lambda node: 'shape=box')
    #
    # exporter.to_picture(f'{file_dir}{SLASH}{self.__file_name(root)}.png')

    def export_mermaid(self, root: Node):
        file_dir = self.__makedir('mermaid', root.as_of)
        file_path = file_dir / f'{self.__file_name(root)}.md'

        (
            MermaidExporter(root, name='LR')
            .to_file(file_path)
        )

    def export_text(self, root: Node):
        file_dir = self.__makedir('text', root.as_of)
        file_path = file_dir / f'{self.__file_name(root)}.txt'

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(RenderTree(root).by_attr())

    @staticmethod
    def __file_name(node: Node) -> str:
        name = node.child_name
        invalid_chars_pattern = r'[\\/:*?"<>|,]'
        result = re.sub(invalid_chars_pattern, '_', name)

        return result

    def __makedir(self, format_name: str, as_of: str) -> Path:
        file_dir = self.output_dir / format_name / as_of
        os.makedirs(file_dir, exist_ok=True)

        return file_dir


def main():
    plotter = TreePlotter()
    plotter.plot()


if __name__ == '__main__':
    main()
