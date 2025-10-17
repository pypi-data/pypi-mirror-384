import os
from pathlib import Path
import sys

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
class OWFileSyncChecker(widget.OWWidget):
    name = "File Sync Checker"
    description = 'Verify if the files contained in Data are the same as the files contained in Reference. The verification is done thanks to both the "path" and "file size" columns.'
    category = "AAIT - TOOLBOX"
    icon = "icons/owfilesyncchecker.svg"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owfilesyncchecker.svg"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owfilesyncchecker.ui")
    want_control_area = False
    priority = 1060

    class Inputs:
        data = Input("Data", Orange.data.Table)
        reference = Input("Reference", Orange.data.Table)

    class Outputs:
        data = Output("Files only in Data", Orange.data.Table)
        processed = Output("Files in Data & Reference", Orange.data.Table)

    @Inputs.data
    def set_data(self, in_data):
        self.data = in_data
        if self.autorun:
            self.run()

    @Inputs.reference
    def set_reference(self, in_reference):
        self.reference = in_reference
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
        self.reference = None
        self.autorun = True
        self.thread = None
        self.result = None
        self.post_initialized()

    def run(self):
        self.warning("")
        self.error("")

        # If Thread is already running, interrupt it
        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.safe_quit()

        if self.data is None:
            return

        if self.reference is None:
            self.warning('There is no Reference table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        if "path" not in self.data.domain or "path" not in self.reference.domain:
            self.error('You need a "path" column in both Data and Reference tables.')
            return

        if "file size" not in self.data.domain:
            self.warning('There is no "file size" column in your Data table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        if "file size" not in self.reference.domain:
            self.warning('There is no "file size" column in your Reference table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        # Start progress bar
        self.progressBarInit()

        # Start threading
        self.thread = thread_management.Thread(self.check_for_sync, self.data, self.reference)
        self.thread.progress.connect(self.handle_progress)
        self.thread.result.connect(self.handle_result)
        self.thread.finish.connect(self.handle_finish)
        self.thread.start()


    def check_for_sync(self, table_data, table_reference, progress_callback=None, argself=None):
        """
        Compare two Orange tables (data and reference) and determine which files need to be processed,
        which are common, and which should be removed from the reference.

        This function:
        - Extracts file paths from both tables.
        - Computes a common root directory for each table.
        - Aligns reference paths relative to the data table.
        - Compares file sizes for files that exist in both tables.
        - Identifies files only in data (to be processed) and files only in reference (to be removed).
        - Returns a list of files to process and an updated reference table.

        Parameters
        ----------
        table_data : Orange.data.Table
            The input table containing current file paths.
        table_reference : Orange.data.Table
            The reference table against which data is compared.
        progress_callback : callable, optional
            A function to report progress (value between 0-100), default is None.
        argself : object, optional
            An object with a `stop` attribute to allow interruption, default is None.

        Returns
        -------
        reference : Orange.data.Table
            The updated reference table after removing outdated files.
        files_to_process : list of [pathlib.Path, int]
            A list of files that need processing, with their file sizes.
        """

        # Make copies of input tables to avoid modifying originals
        data = table_data.copy()
        reference = table_reference.copy()

        # Extract file paths from the data table
        paths_data = {Path(str(row["path"].value)).resolve(): row["file size"].value for row in data}

        # Extract file paths and sizes from the reference table
        paths_ref = {Path(str(row["path"].value)).resolve(): row["file size"].value for row in reference}

        # Compute common root directories for both data and reference
        common_path_data = get_common_path(paths_data.keys())
        common_path_ref = get_common_path(paths_ref.keys())
        paths_ref = {common_path_data / path.relative_to(common_path_ref): size
                     for path, size in paths_ref.items()}

        # Align reference paths relative to data's common root
        for row in reference:
            old_path = Path(row["path"].value).resolve()
            try:
                rel = old_path.relative_to(common_path_ref)
                row["path"] = str(common_path_data / rel)
            except ValueError:
                # not under common_path_ref → leave unchanged
                row["path"] = str(old_path)

        # Determine which files are common, only in data, or only in reference
        common = set(paths_data.keys()) & set(paths_ref.keys())  # files present in both
        only_in_data = set(paths_data.keys()) - set(paths_ref.keys())  # new files to process
        only_in_ref = set(paths_ref.keys()) - set(paths_data.keys())  # files to remove from reference

        print("Files in common:", len(common))
        print("Only in data:", len(only_in_data))
        print("Only in ref:", len(only_in_ref))

        files_to_process = []
        # Check sizes of common files and mark for processing if different
        for path in common:
            path = path.resolve()
            filesize = paths_data.get(path)
            reference_size = paths_ref.get(path)
            if int(filesize) != int(reference_size):
                reference = remove_from_table(path, reference)
                files_to_process.append([path, filesize])

        # All files only in data must be processed
        for path in only_in_data:
            path = path.resolve()
            filesize = paths_data.get(path)
            files_to_process.append([path, filesize])

        # Remove files from reference that no longer exist in data
        for path in only_in_ref:
            reference = remove_from_table(path, reference)

        # Create output table
        path_var = StringVariable("path")
        filesize_var = ContinuousVariable("file size")
        dom = Domain([], metas=[path_var, filesize_var])
        out_data = Table.from_list(dom, rows=files_to_process)

        return out_data, reference



    def handle_progress(self, value: float) -> None:
        self.progressBarSet(value)

    def handle_result(self, result):
        data = result[0]
        processed_data = result[1]
        try:
            self.Outputs.data.send(data)
            self.Outputs.processed.send(processed_data)
        except Exception as e:
            print("An error occurred when sending out_data:", e)
            self.Outputs.data.send(None)
            return

    def handle_finish(self):
        self.progressBarFinished()


    def post_initialized(self):
        pass


def remove_from_table(filepath, table):
    """
    Remove rows from the Orange table where 'path' matches the given filepath.
    """
    filepath = Path(filepath).resolve()

    filtered_table = Table.from_list(
        domain=table.domain,
        rows=[row for row in table
              if Path(str(row["path"].value)).resolve() != filepath]
    )
    return filtered_table


def get_common_path(paths):
    """
    Find the common root directory among a list of file paths.

    - If the list contains only one path, the parent directory of that path
      is returned (to ensure the result is always a directory).
    - If the list contains multiple paths, their deepest shared parent
      directory is returned using os.path.commonpath.

    Parameters
    ----------
    paths : list[pathlib.Path] or list[str]
        A list of file or directory paths.

    Returns
    -------
    pathlib.Path
        The common root directory as a Path object.
    """
    paths = [str(p) for p in paths]

    if len(paths) == 1:
        return Path(paths[0]).parent
    else:
        return Path(os.path.commonpath(paths))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWFileSyncChecker()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()
