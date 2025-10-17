import os
import sys
from pathlib import Path

from AnyQt.QtWidgets import QApplication
from AnyQt.QtCore import pyqtSignal
from Orange.data import Domain, StringVariable, Table, DiscreteVariable
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output

# --- Ajout pour l'écriture Excel ---
from openpyxl import Workbook
import pypdf

# Les imports sont adaptés pour correspondre au style de l'autre script
if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.IO4IT.utils import utils_md
    from Orange.widgets.orangecontrib.AAIT.utils.thread_management import Thread
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
else:
    from orangecontrib.IO4IT.utils import utils_md
    from orangecontrib.AAIT.utils.thread_management import Thread
    from orangecontrib.AAIT.utils.import_uic import uic


class OWPdfType(widget.OWWidget):
    name = "PDF Type"
    description = "Checks if a PDF is text-based or image-based"
    category = "AAIT - TOOLBOX"
    icon = "icons/check_pdf.png"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/check_pdf.png"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owpdftype.ui")
    want_control_area = False
    priority = 1002

    MAX_PAGES_TO_CHECK = 5

    # New signal to send single status updates from the thread
    status_update_signal = pyqtSignal(list)

    class Inputs:
        data = Input("PDF Table", Table)

    class Outputs:
        text_data = Output("Text PDF Table", Table)
        image_data = Output("Image PDF Table", Table)
        status_data = Output("Status Table", Table)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(470)
        self.setFixedHeight(300)
        uic.loadUi(self.gui, self)

        self.data = None
        self.thread = None
        self.autorun = True
        self.result = None
        self.processed_statuses = []
        self.post_initialized()

    @Inputs.data
    def set_data(self, in_data: Table | None):
        self.data = in_data
        if self.autorun:
            self.run()

    def run(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.safe_quit()

        if self.data is None:
            self.Outputs.text_data.send(None)
            self.Outputs.image_data.send(None)
            self.Outputs.status_data.send(None)
            QApplication.quit()
            return

        self.error("")
        try:
            self.data.domain["file_path"]
        except KeyError:
            self.error("You need a 'file_path' column in input data.")
            QApplication.quit()
            return

        if type(self.data.domain["file_path"]).__name__ != 'StringVariable':
            self.error("'file_path' column needs to be a Text.")
            QApplication.quit()
            return

        self.progressBarInit()
        self.processed_statuses = []
        self.status_update_signal.connect(self.handle_status_update)
        self.thread = Thread(self._process_pdfs, self.data, status_callback=self.status_update_signal.emit)
        self.thread.progress.connect(self.handle_progress)
        self.thread.result.connect(self.handle_result)
        self.thread.finish.connect(self.handle_finish)
        self.thread.start()

    def _process_pdfs(self, in_data: Table, progress_callback: callable, status_callback: callable) -> tuple[
        Table | None, Table | None]:

        paths = [str(x) for x in in_data.get_column("file_path")]

        excel_output_dir = Path.cwd() / "pdf_check_results"
        if paths:
            first_file_path = Path(paths[0])
            excel_output_dir = first_file_path.parent / "pdf_check_results"

        excel_output_dir.mkdir(parents=True, exist_ok=True)

        base_name = "pdf_check_results"
        excel_path = excel_output_dir / f"{base_name}.xlsx"
        counter = 1
        while excel_path.exists():
            excel_path = excel_output_dir / f"{base_name}_{counter}.xlsx"
            counter += 1

        wb = Workbook()
        ws = wb.active
        ws.title = "PDF Check Results"
        headers = ["file_path", "status", "details"]
        ws.append(headers)

        text_indices = []
        image_indices = []

        total_files = len(paths)
        for i, p in enumerate(paths):
            progress_callback(i / total_files * 100)
            fp = Path(p)
            result_row = [p, "", ""]

            if not fp.exists() or fp.suffix.lower() != ".pdf":
                result_row[1] = "ko"
                result_row[2] = "Invalid file or not a PDF"
                status_callback(result_row)
                ws.append(result_row)
                wb.save(excel_path)
                continue

            try:
                # Vérification de l'attribut is_encrypted de PyPDF avant de traiter le fichier.
                reader = pypdf.PdfReader(fp)
                if reader.is_encrypted:
                    result_row[1] = "ko"
                    result_row[2] = "Error: PDF is password protected."
                else:
                    is_text = utils_md.is_pdf_text_based(fp)
                    if is_text:
                        text_indices.append(i)
                        result_row[1] = "ok"
                        result_row[2] = "Text-based PDF"
                    else:
                        image_indices.append(i)
                        result_row[1] = "ok"
                        result_row[2] = "Image-based PDF"
            except Exception as e:
                result_row[1] = "ko"
                result_row[2] = f"Error: {str(e)}"
            finally:
                status_callback(result_row)
                ws.append(result_row)
                wb.save(excel_path)

        progress_callback(100)

        if not text_indices:
            text_table = None
        else:
            text_table = in_data[text_indices]

        if not image_indices:
            image_table = None
        else:
            image_table = in_data[image_indices]

        return text_table, image_table

    def handle_progress(self, value: float) -> None:
        self.progressBarSet(value)

    def handle_status_update(self, new_status: list):
        self.processed_statuses.append(new_status)
        status_domain = Domain(
            [],
            metas=[
                StringVariable("file_path"),
                DiscreteVariable("status", values=["ok", "ko"]),
                StringVariable("details")
            ]
        )
        status_table = Table.from_list(status_domain, self.processed_statuses)
        self.Outputs.status_data.send(status_table)

    def handle_result(self, result):
        try:
            text_table, image_table = result
            self.Outputs.text_data.send(text_table)
            self.Outputs.image_data.send(image_table)
        except Exception as e:
            print("An error occurred when sending out_data:", e)
            self.Outputs.text_data.send(None)
            self.Outputs.image_data.send(None)

    def handle_finish(self):
        print("PDF Type check finished")
        self.progressBarFinished()

    def post_initialized(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWPdfType()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()