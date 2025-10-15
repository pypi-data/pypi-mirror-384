from io import BytesIO
from pathlib import Path

import pandas as pd
import panel as pn
from ruamel.yaml import YAML

from sofastats.ui.conf import SharedKey
from sofastats.ui.state import data_labels_param, got_data_param, shared

yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)

pn.extension('tabulator')

shared[SharedKey.DF_CSV] = pd.DataFrame()


class Data:

    @staticmethod
    def set_data_labels(yaml_bytes):
        try:
            data_label_mappings = yaml.load(BytesIO(yaml_bytes)) if yaml_bytes else {}
            data_labels_param.value = data_label_mappings
        except FileNotFoundError:
            data_labels_param.value = {}

    @staticmethod
    def display_csv(csv_bytes, data_labels_value):
        if csv_bytes:
            got_data_param.value = True
            df = pd.read_csv(BytesIO(csv_bytes))
            shared[SharedKey.DF_CSV] = df.copy()  ## so we can decide what options to display in config forms
            cwd = Path(__file__).parent
            csv_fpath = cwd / 'data.csv'
            with open(csv_fpath, 'wb') as f:
                f.write(csv_bytes)
            shared[SharedKey.CSV_FPATH] = csv_fpath  ## so we can supply csv path to stats calc (TODO: enable passing of actual CSV as an option alongside dbapi2 cursor or csv_fpath)
            ## apply any labels
            col_name_vals = []
            for i, col in enumerate(df.columns):
                col_name_vals.append((col, df[col]))
                if col in data_labels_value.keys():
                    val_mapping = data_labels_value.get(col, {}).get('value_labels', {})
                    if val_mapping:
                        col_name_vals.append((f"{col}<br>(labelled)", df[col].apply(lambda num_val: val_mapping.get(num_val, num_val))))
            df_labelled = pd.DataFrame(dict(col_name_vals))
            table_df = pn.widgets.Tabulator(df_labelled, page_size=10, disabled=True)
            table_df.value = df_labelled
            return table_df
        else:
            return None

    @staticmethod
    def next_step(selected_csv_fpath: Path):
        if selected_csv_fpath:
            next_step_msg = "Click on the Tables & Charts tab or the Statistics tab and get some output results ..."
        else:
            next_step_msg = "Select a CSV file containing the data you want to understand ..."
        return pn.pane.Alert(next_step_msg, alert_type='info')

    def __init__(self):
        self.data_title = pn.pane.Markdown(f"## Start here - select a CSV", styles={'color': "#0072b5"})
        self.csv_file_input = pn.widgets.FileInput(accept='.csv')
        self.next_step_or_none = pn.bind(Data.next_step, self.csv_file_input.param.filename)
        self.data_table_or_none = pn.bind(
            Data.display_csv, self.csv_file_input.param.value, data_labels_param.param.value)
        self.labels_title = pn.pane.Markdown(f"## Apply labels to your data (if you have a YAML file)", styles={'color': "#0072b5"})
        self.labels_file_input = pn.widgets.FileInput(accept='.yaml,.yml')
        self.data_label_setter = pn.bind(Data.set_data_labels, self.labels_file_input.param.value)

    def ui(self):
        data_column = pn.Column(
            self.data_title, self.csv_file_input, self.data_table_or_none,
            self.labels_title, self.labels_file_input, self.data_label_setter,
            self.next_step_or_none,
        )
        return data_column
