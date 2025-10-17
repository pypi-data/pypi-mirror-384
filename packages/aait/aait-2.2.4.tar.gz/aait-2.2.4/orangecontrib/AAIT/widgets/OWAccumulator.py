from orangewidget.widget import OWBaseWidget
import sys
import os

from AnyQt.QtWidgets import QApplication
from Orange.widgets.utils.signals import Input, Output
from Orange.data import Domain, Table

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file

@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWAccumulator(OWBaseWidget):
    name = "Data Accumulator (Flexible Columns)"
    description = "Allows for data accumulation by concatenation, automatically merging non-matching columns."
    priority = 10
    category = "AAIT - TOOLBOX"
    icon = "icons/owaccumulator.png"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owaccumulator.png"

    # Le chemin du fichier .ui
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owaccumulator.ui")
    priority = 1094

    want_main_area = True
    # want_control_area est mis à False pour utiliser l'UI chargée dans mainArea
    want_control_area = False

    class Inputs:
        data = Input("Input Data", Table, auto_summary=False)

    class Outputs:
        sample = Output("Output", Table, auto_summary=False)
        preview = Output("Preview", Table, auto_summary=False)

    def __init__(self):
        super().__init__()

        # --- NOUVEAU : Chargement de l'UI et connexion du bouton ---
        # Charge le contenu du .ui dans l'instance du widget (self)
        uic.loadUi(self.gui, self)

        # Connexion du bouton 'pushButton_send' défini dans le .ui
        self.pushButton_send.clicked.connect(self.push)

        # --- Variables d'état ---
        self.data = None
        self.out_data = None

        # --- Appel à post_initialized pour l'alignement ---
        self.post_initialized()

    def push(self):
        """Sends the accumulated data and resets the accumulator."""
        if self.data is not None:
            self.out_data = self.data.copy()

            # Send the final output
            self.Outputs.sample.send(self.out_data)

            # Purge the accumulator
            self.data = None
            self.Outputs.preview.send(None)  # Clear preview after purge
            self.information("Data sent and accumulator purged.")
        else:
            self.Outputs.sample.send(None)
            self.warning("Accumulator is empty, nothing to send.")

    @Inputs.data
    def set_data(self, dataset):
        """Accumulates incoming data, merging columns if necessary, with robust variable handling."""
        self.error("")  # Clear previous errors
        if dataset is None:
            # If input is cleared, clear the preview output
            if self.data is not None:
                self.data = None
                self.Outputs.preview.send(None)
            return

        # --- LOGIQUE DE FUSION DES COLONNES (CONSERVÉE) ---

        if self.data is None:
            # First data block: initialize the accumulator
            self.data = dataset.copy()

        else:
            try:
                # 1. Collecter TOUTES les variables (attributs réguliers + méta) des deux tables
                current_all_vars = self.data.domain.variables + self.data.domain.metas
                new_all_vars = dataset.domain.variables + dataset.domain.metas

                # Utiliser un dictionnaire pour ne conserver qu'une seule variable par nom
                unique_vars = {}
                for var in current_all_vars + new_all_vars:
                    if var.name not in unique_vars:
                        unique_vars[var.name] = var

                # 2. Identifier les noms d'attributs réguliers et de méta-attributs uniques
                current_regular_names = set(v.name for v in self.data.domain.variables)
                new_regular_names = set(v.name for v in dataset.domain.variables)
                current_metas_names = set(v.name for v in self.data.domain.metas)
                new_metas_names = set(v.name for v in dataset.domain.metas)

                all_vars_names = current_regular_names | new_regular_names
                all_metas_names = current_metas_names | new_metas_names

                # 3. Filtrer les variables uniques pour créer le nouveau domaine
                all_vars = sorted([unique_vars[name] for name in all_vars_names if name not in all_metas_names],
                                  key=lambda x: x.name)
                all_metas = sorted([unique_vars[name] for name in all_metas_names], key=lambda x: x.name)

                # 4. Créer le nouveau domaine
                new_domain = Domain(all_vars, metas=all_metas)

                # 5. Transform (expand) both tables to the new, common domain
                data_expanded = self.data.transform(new_domain)
                dataset_expanded = dataset.transform(new_domain)

                # 6. Concatenate the rows of the two uniformly expanded tables
                self.data = data_expanded.__class__.concatenate((data_expanded, dataset_expanded))

            except Exception as e:
                self.error(f"Data tables could not be aggregated/concatenated. Error: {e}")
                return
        # Send the current accumulated data for preview
        self.Outputs.preview.send(self.data)

    def post_initialized(self):
        """
        Method for post-initialization tasks, aligned with OWChunker structure.
        """
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWAccumulator()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()