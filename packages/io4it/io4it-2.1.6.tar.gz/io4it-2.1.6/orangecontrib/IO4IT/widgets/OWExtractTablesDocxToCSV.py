import os
import sys
import docx
import pandas as pd
import re
# Removed: import json

from AnyQt.QtWidgets import QApplication, QPushButton
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output
from Orange.data import Domain, StringVariable, Table, DiscreteVariable


if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file

@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWExtractTablesDocxToCSV(widget.OWWidget):
    """
    Orange Widget qui extrait les tableaux de documents Word (.docx) et les sauvegarde
    en fichiers XLSX distincts (une table Word = un fichier XLSX).
    """
    name = "Docx to XLSX Tables (Full Tables)"
    description = "Extrait toutes les tables de documents Word et les sauvegarde en fichiers XLSX distincts"
    category = "AAIT - TOOLBOX"
    icon = "icons/extract_table.png"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/extract_table.png"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owdocxtocsv.ui")
    want_control_area = False
    priority = 1005

    class Inputs:
        data = Input("Files Table", Table)

    class Outputs:
        data = Output("Processed Files Table", Table)
        status_data = Output("Status Table", Table)

    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(self.gui, self)
        except Exception as e:
            self.warning(f"Impossible de charger le fichier UI. {e}")

            class DummyCheckbox:
                def stateChanged(self, *args): pass

            self.checkBox_alpha_headers = DummyCheckbox()
            self.gui = None

        # Connexion du bouton d'exécution
        self.pushButton_run = self.findChild(QPushButton, "pushButton_run")
        if self.pushButton_run:
            self.pushButton_run.clicked.connect(self.run)

        self.data = None
        self.autorun = True
        self.processed_statuses = []
        self.use_alpha_headers = False
        if self.gui:
            self.checkBox_alpha_headers.stateChanged.connect(self._update_alpha_headers_state)

        self.post_initialized()

    def _update_alpha_headers_state(self, state):
        self.use_alpha_headers = bool(state)

    @Inputs.data
    def set_data(self, in_data: Table | None):
        self.data = in_data
        if self.autorun:
            self.run()

    def run(self):
        if self.data is None:
            self.Outputs.data.send(None)
            self.Outputs.status_data.send(None)
            return

        self.error("")
        try:
            self.data.domain["file_path"]
        except KeyError:
            self.error("Le tableau d'entrée doit contenir une colonne 'file_path'.")
            self.Outputs.data.send(None)
            self.Outputs.status_data.send(None)
            return

        self.progressBarInit()
        self.processed_statuses = []
        self.Outputs.status_data.send(None)

        result_rows = self._process_files(self.data)

        output_domain = Domain([], metas=[
            StringVariable("src_path"),
            StringVariable("output_dir_path"),
            StringVariable("status")
        ])
        result_table = Table.from_list(output_domain, result_rows)
        self.Outputs.data.send(result_table)

        self.progressBarFinished()

    def _process_files(self, in_data: Table) -> list:
        result_rows = []
        file_paths = [str(x) for x in in_data.get_column("file_path")]
        total_files = len(file_paths)

        if not file_paths:
            return []

        for i, full_path in enumerate(file_paths):
            self.progressBarSet((i + 1) / total_files * 100)

            status_short = "ko"
            details = "traitement échoué"
            output_dir_path = ""

            if not full_path.lower().endswith('.docx'):
                status_short = "skipped"
                details = "Fichier ignoré : n'est pas un fichier .docx."
                output_dir_path = "N/A"
                self.processed_statuses.append([full_path, status_short, details])
                self._send_status_table()
                result_rows.append([full_path, output_dir_path, f"{status_short}: {details}"])
                QApplication.processEvents()
                continue

            try:
                tables_found, output_dir_path = self._extraire_et_convertir(full_path)

                if tables_found > 0:
                    status_short = "ok"
                    details = f"{tables_found} table(s) extraite(s) et convertie(s) en XLSX."
                else:
                    status_short = "ko"
                    details = "Aucune table valide trouvée."

            except FileNotFoundError:
                details = "Fichier non trouvé."
            except Exception as e:
                details = f"Une erreur inattendue est survenue : {e}"

            self.processed_statuses.append([full_path, status_short, details])
            self._send_status_table()

            result_rows.append([full_path, output_dir_path, f"{status_short}: {details}"])

            QApplication.processEvents()

        return result_rows

    def _extraire_et_convertir(self, docx_path):
        """
        Extrait les tableaux d'un document Word et sauvegarde chaque table entière en XLSX.
        Retourne (nombre_de_tables_trouvées, chemin_dossier_sortie).
        """
        dir_name, file_name = os.path.split(docx_path)
        base_name, _ = os.path.splitext(file_name)

        output_dir = os.path.join(dir_name, base_name + '_tables_data')
        os.makedirs(output_dir, exist_ok=True)

        doc = docx.Document(docx_path)
        total_tables_found = 0

        for i, table in enumerate(doc.tables):
            raw_data = []
            for row in table.rows:
                # Extraction des données de toute la table
                row_data = [cell.text.strip() for cell in row.cells]
                raw_data.append(row_data)

            # S'assurer qu'il y a des données non vides dans la table
            if not raw_data or not any(row for row in raw_data):
                continue

            # --- PAS DE DÉCOUPAGE ---

            table_index = i + 1
            # Utilisation de 'a' comme suffixe pour le nom de fichier
            table_name = f"table_{table_index}_a"

            df = self._create_dataframe(raw_data)

            if df is not None:
                self._save_sub_table(df, output_dir, table_name)
                total_tables_found += 1

        return total_tables_found, output_dir

    def _create_dataframe(self, data):
        """
        Crée le DataFrame à partir des lignes brutes.
        """
        # Nettoyer les lignes vides
        data = [row for row in data if row and any(cell.strip() for cell in row)]
        if not data:
            return None

        max_cols = max(len(row) for row in data)
        data = [row + [''] * (max_cols - len(row)) for row in data]

        if self.use_alpha_headers:
            # Cas A : En-têtes alphabétiques. Toutes les lignes sont des données.
            headers = [chr(ord('A') + j) for j in range(max_cols)]
            df = pd.DataFrame(data, columns=headers)
        else:
            # Cas B : Première ligne comme en-tête.

            if len(data) == 1:
                # Si le segment n'a qu'une seule ligne, on utilise des en-têtes alphabétiques.
                headers = [chr(ord('A') + j) for j in range(max_cols)]
                df = pd.DataFrame(data, columns=headers)
            else:
                # Cas standard : première ligne = en-tête, reste = données.
                headers = data[0]
                data_rows = data[1:]

                min_cols = min(len(headers), max_cols)

                df = pd.DataFrame(data_rows, columns=headers[:min_cols])

            df.columns = df.columns.astype(str)

        return df

    def _save_sub_table(self, df, output_dir, table_full_name):
        """Sauvegarde le DataFrame exclusivement en XLSX."""

        output_xlsx_path = os.path.join(output_dir, f"{table_full_name}.xlsx")
        try:
            df.to_excel(output_xlsx_path, index=False, engine='openpyxl')
        except Exception as e:
            self.warning(f"Impossible de sauvegarder la table '{table_full_name}' en format XLSX : {e}")

    def _send_status_table(self):
        domain = Domain([], metas=[
            StringVariable("src_path"),
            DiscreteVariable("status", values=["ok", "ko", "skipped"]),
            StringVariable("details")
        ])
        status_table = Table.from_list(domain, self.processed_statuses)
        self.Outputs.status_data.send(status_table)

    def post_initialized(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWExtractTablesDocxToCSV()
    my_widget.show()
    app.exec()