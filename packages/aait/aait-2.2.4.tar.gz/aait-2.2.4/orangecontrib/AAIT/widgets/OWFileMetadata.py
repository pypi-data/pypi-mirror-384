import os
import sys
from pathlib import Path
import datetime

import Orange.data
from Orange.data import Table, Domain, StringVariable, ContinuousVariable
from AnyQt.QtWidgets import QApplication
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output


if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
    from Orange.widgets.orangecontrib.AAIT.utils import thread_management
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
    from orangecontrib.AAIT.utils import thread_management


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWFileMetadata(widget.OWWidget):
    name = "File Metadata"
    category = "AAIT - TOOLBOX"
    description = 'Get some metadatas on the files contained in the "path" column'
    icon = "icons/owfilemetadata.svg"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owfilemetadata.svg"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owfilemetadata.ui")
    want_control_area = False
    priority = 1060

    class Inputs:
        data = Input("Data", Orange.data.Table)

    class Outputs:
        data = Output("Data", Orange.data.Table)


    @Inputs.data
    def set_data(self, in_data):
        self.data = in_data
        if self.autorun:
            self.run()


    def __init__(self):
        super().__init__()
        # Qt Management
        self.setFixedWidth(470)
        self.setFixedHeight(300)
        uic.loadUi(self.gui, self)

        # Data Management
        self.data = None
        self.result = None
        self.thread = None
        self.autorun = True
        self.post_initialized()

    def run(self):
        self.error("")
        self.warning("")

        if self.data is None:
            return

        if "path" not in self.data.domain:
            self.error('You need a "path" column.')
            return

        # Start progress bar
        self.progressBarInit()

        # Connect and start thread : main function, progress, result and finish
        self.thread = thread_management.Thread(add_metadatas_to_table, self.data)
        self.thread.progress.connect(self.handle_progress)
        self.thread.result.connect(self.handle_result)
        self.thread.finish.connect(self.handle_finish)
        self.thread.start()

    def handle_progress(self, value: float) -> None:
        self.progressBarSet(value)

    def handle_result(self, result):
        try:
            self.result = result
            self.Outputs.data.send(result)
        except Exception as e:
            print("An error occurred when sending out_data:", e)
            self.Outputs.data.send(None)
            return

    def handle_finish(self):
        self.progressBarFinished()

    def post_initialized(self):
        pass


def add_metadatas_to_table(table, progress_callback=None, argself=None):
    data = table.copy()
    attr_dom = list(data.domain.attributes)
    metas_dom = list(data.domain.metas)
    class_dom = list(data.domain.class_vars)

    # Generate embeddings on column named "content"
    rows = []
    for i, row in enumerate(data):
        filepath = row["path"].value
        features = [row[x] for x in attr_dom]
        targets = [row[y] for y in class_dom]
        metas = list(data.metas[i])
        metadata_dict = get_metadata(filepath)
        metas += [metadata_dict["file size"], metadata_dict["creation time"], metadata_dict["modification time"]]
        rows.append(features + targets + metas)
        if progress_callback is not None:
            progress_value = float(100 * (i + 1) / len(data))
            progress_callback(progress_value)
        if argself is not None:
            if argself.stop:
                break

    # Generate new Domain to add to data
    filesize_var = ContinuousVariable("file size")
    ctime_var = StringVariable("creation time")
    mtime_var = StringVariable("modification time")
    domain = Domain(attributes=attr_dom, class_vars=class_dom, metas=metas_dom + [filesize_var, ctime_var, mtime_var])

    # Create and return table
    out_data = Table.from_list(domain=domain, rows=rows)
    return out_data


def get_metadata(filepath):
    """
    Retrieve file metadata: size, creation time, and modification time as strings.

    :param filepath: Path to the file (str or Path).
    :return: Dictionary with keys "file size", "creation time", "modification time".
    """
    metadatas = {}
    path = Path(filepath)

    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    # Get file size
    try:
        metadatas["file size"] = str(path.stat().st_size)
    except Exception as e:
        metadatas["file size"] = str(e)

    # Get creation time
    try:
        ctime = datetime.datetime.fromtimestamp(path.stat().st_ctime)
        metadatas["creation time"] = ctime.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        metadatas["creation time"] = str(e)

    # Get modification time
    try:
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
        metadatas["modification time"] = mtime.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        metadatas["modification time"] = str(e)

    return metadatas




if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWFileMetadata()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()
