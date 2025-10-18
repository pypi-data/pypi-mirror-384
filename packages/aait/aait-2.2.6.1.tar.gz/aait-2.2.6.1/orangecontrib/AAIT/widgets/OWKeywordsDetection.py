import os
import sys

import Orange
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output
from Orange.data import  ContinuousVariable
from thefuzz import fuzz
from AnyQt.QtWidgets import QApplication

# Import intelligent selon contexte
if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils import thread_management
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils import thread_management
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWKeywordsDetection(widget.OWWidget):
    name = "Keywords Detection"
    description = 'The input Data must contain a column "content". The input Keywords must contain a column "keywords". This widget will count the number of keywords that occur in the content with a fuzzy matching (percentage based on small variations).'
    category = "AAIT - LLM INTEGRATION"
    icon = "icons/owkeywordsdetection.png"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owkeywordsdetection.png"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owkeywordsdetection.ui")
    want_control_area = True
    priority = 1071

    class Inputs:
        data = Input("Data", Orange.data.Table)
        keywords = Input("Keywords", Orange.data.Table)

    class Outputs:
        data = Output("Data", Orange.data.Table)


    @Inputs.data
    def set_data(self, in_data):
        self.data = in_data
        if self.autorun:
            self.run()

    @Inputs.keywords
    def set_keywords(self, in_keywords):
        self.keywords = in_keywords
        if self.autorun:
            self.run()

    def __init__(self):
        super().__init__()
        # Qt Management
        self.setFixedWidth(700)
        self.setFixedHeight(700)
        uic.loadUi(self.gui, self)

        # Data Management
        self.data = None
        self.keywords = None
        self.thread = None
        self.autorun = True
        self.result = None

        # Custom updates
        self.post_initialized()


    def run(self):
        self.error("")
        self.warning("")

        # If Thread is already running, interrupt it
        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.safe_quit()

        if self.data is None:
            self.Outputs.data.send(None)
            return

        if self.keywords is None:
            self.Outputs.data.send(None)
            return

        if "content" not in self.data.domain:
            self.error('You need a "content" column in your input Data.')
            self.Outputs.data.send(None)
            return

        if "keywords" not in self.keywords.domain:
            self.error('You need a "keywords" column in your input Keywords.')
            self.Outputs.data.send(None)
            return


        self.progressBarInit()

        # Connect and start thread : main function, progress, result and finish
        # --> progress is used in the main function to track progress (with a callback)
        # --> result is used to collect the result from main function
        # --> finish is just an empty signal to indicate that the thread is finished
        self.thread = thread_management.Thread(compute_keywords_on_table, self.data, self.keywords)
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
        print("Keywords computation finished !")
        self.progressBarFinished()

    def post_initialized(self):
        pass



def compute_keywords_on_table(table, keywords, progress_callback=None, argself=None):
    """
    Compute fuzzy match scores between table rows and a list of keywords,
    and add them as a new meta column.

    Args:
        table (Orange.data.Table): Input table with a "content" column.
        keywords (Orange.data.Table): Table with a "keywords" column.
        progress_callback (callable, optional): Function called with progress (0–100).
        argself (object, optional): If has attribute `stop=True`, stops processing early.

    Returns:
        Orange.data.Table: Copy of input with a new meta column "Score - Keywords".
    """
    # Make a copy of the table to avoid modifying the original
    data = table.copy()

    # Extract the list of keywords from the 'keywords' table
    keywords_list = [row["keywords"].value for row in keywords]

    scores = []
    # Iterate over each row in the copied table
    for i, row in enumerate(data):
        content = row["content"].value  # Text from the 'content' column
        score = fuzzy_match_score(content, keywords_list)  # Compute similarity score
        scores.append(score)

        # Update progress if a progress callback is provided
        if progress_callback is not None:
            progress_value = float(100 * (i + 1) / len(data))
            progress_callback(progress_value)

        # Stop loop if 'argself' exists and stop flag is set
        if argself is not None:
            if argself.stop:
                break

    # Create a new continuous variable (column) for keyword scores
    score_var = ContinuousVariable("Score - Keywords")
    # Add the scores as a meta attribute to the table
    data = data.add_column(score_var, scores, to_metas=True)

    return data



def fuzzy_match_score(text, keywords_list):
    """
    Checks if keywords are present in text using fuzzy matching
    and returns a global score.

    Args:
        text (str): The full text to search in.
        keywords_list (list): List of keywords to find.

    Returns:
        float: Global match score (0-100).
    """
    keywords_list = list(filter(None, keywords_list))
    if len(keywords_list)==0:
        return 0

    words = text.split(" ")  # Split text into words
    total_score = 0

    for keyword in keywords_list:
        best_score = max(fuzz.ratio(word.lower(), keyword.lower()) for word in words)
        total_score += best_score

    return total_score / len(keywords_list)  # Normalize score



if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWKeywordsDetection()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()

