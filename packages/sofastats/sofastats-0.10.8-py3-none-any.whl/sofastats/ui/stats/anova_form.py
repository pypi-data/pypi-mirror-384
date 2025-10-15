import datetime
from typing import Any

import panel as pn

from sofastats_lib.conf.main import DEFAULT_OUTPUT_FOLDER
from sofastats_lib.output.stats import anova
from sofastats.ui.conf import SharedKey
from sofastats.ui.state import (
    Text,
    data_labels_param, give_output_tab_focus_param, html_param,
    shared, show_output_saved_msg_param, show_output_tab_param)
from sofastats.ui.utils import get_unlabelled

pn.extension('modal')

class ANOVAForm:

    @staticmethod
    def var_restoration_fn_from_var_from_option(var: Any) -> Any:
        """
        E.g. If variable is country, and we extract '1' from option 'nz (1)' then we want int() to restore to 1
        If variable is name, and we extract 'Grant' from 'Grant' then str('Grant') will return (what would already have been) the correct result
        """
        dtype = dict(shared[SharedKey.DF_CSV].dtypes.items())[var]
        if dtype in ('int64', ):
            return int
        elif dtype in ('float64', ):
            return float
        else:
            return str

    @staticmethod
    def get_measure_options() -> list[str]:
        measure_cols = []
        for name, dtype in shared[SharedKey.DF_CSV].dtypes.items():
            has_val_labels = bool(data_labels_param.value.get(name, {}).get('value_labels'))
            if dtype in ('int64', 'float64') and not has_val_labels:
                measure_cols.append(name)
        measure_options = []
        for measure_col in measure_cols:
            measure_var_lbl = data_labels_param.value.get(measure_col, {}).get('variable_label')
            measure_option = f"{measure_var_lbl} ({measure_col})" if measure_var_lbl else measure_col  ## e.g. 'Height (height)'
            measure_options.append(measure_option)
        return sorted(measure_options)

    @staticmethod
    def get_grouping_options() -> list[str]:
        grouping_options = []
        for grouping_col in shared[SharedKey.DF_CSV].columns:
            grouping_var_lbl = data_labels_param.value.get(grouping_col, {}).get('variable_label')
            grouping_option = f"{grouping_var_lbl} ({grouping_col})" if grouping_var_lbl else grouping_col  ## e.g. ['Sport (sport)', ]
            grouping_options.append(grouping_option)
        return sorted(grouping_options)

    @staticmethod
    def get_value_options(grouping_variable: str) -> list[str]:
        vals = sorted(shared[SharedKey.DF_CSV][grouping_variable].unique())
        value_label_mappings = data_labels_param.value.get(grouping_variable, {}).get('value_labels', {})
        value_options = []
        for val in vals:
            val_lbl = value_label_mappings.get(val)
            val_option = f"{val_lbl} ({val})" if val_lbl else val  ## e.g. ['Archery (1)', 'Badminton (2)', 'Basketball (3)']
            value_options.append(val_option)
        return value_options

    def get_values_multiselect_or_none(self, grouping_variable_str: str):
        if not grouping_variable_str:
            return None
        value_options = ANOVAForm.get_value_options(grouping_variable_str)
        group_value_selector = pn.widgets.CheckButtonGroup(name='Group Values',
            options=value_options, orientation='vertical', button_type='primary', button_style='outline',
        )
        self.group_value_selector = group_value_selector
        return group_value_selector

    def set_grouping_variable(self, grouping_variable_option: str):
        grouping_variable = get_unlabelled(grouping_variable_option)
        self.grouping_variable_var.value = grouping_variable

    def __init__(self, btn_close: pn.widgets.Button):
        """
        Args:
            btn_close: passed in so we can set its on_click event to closing this modal from the outside
        """
        self.user_msg_var = Text(value=None)
        self.grouping_variable_var = Text(value=None)
        self.group_value_selector = None
        self.user_msg_or_none = pn.bind(self.set_user_msg, self.user_msg_var.param.value)
        ## Measure Variable
        measure_options = ANOVAForm.get_measure_options()
        self.measure = pn.widgets.Select(name='Measure',
            description='Measure which varies between different groups ...',
            options=measure_options,
        )
        ## Grouping Variable
        grouping_options = ANOVAForm.get_grouping_options()
        self.select_grouping_variable = pn.widgets.Select(name='Grouping Variable',
            description='Variable containing the groups ...',
            options=grouping_options,
        )
        self.set_grouping_var = pn.bind(self.set_grouping_variable, self.select_grouping_variable.param.value)  ## set to a variable I can access when returning the item which goes in the template (thus making the param work)
        ## Group Values
        self.values_multiselect_or_none = pn.bind(
            self.get_values_multiselect_or_none, self.grouping_variable_var.param.value)
        ## Buttons
        self.btn_run_analysis = pn.widgets.Button(name="Get ANOVA Results", button_type='primary')
        self.btn_run_analysis.on_click(self.run_analysis)
        self.btn_close = btn_close

    def run_analysis(self, _event):
        show_output_saved_msg_param.value = False  ## have to wait for Save Output button to be clicked again now
        ## validate
        selected_values = self.group_value_selector.value
        if len(selected_values) < 2:
            self.user_msg_var.value = ("Please select at least two grouping values "
                "so the ANOVA has enough groups to compare average values by group.")
            return
        self.user_msg_var.value = None
        grouping_variable_name = get_unlabelled(self.select_grouping_variable.value)
        var_restoration_fn = ANOVAForm.var_restoration_fn_from_var_from_option(grouping_variable_name)
        group_vals = [var_restoration_fn(get_unlabelled(val)) for val in selected_values]
        ## get HTML
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        anova_design = anova.AnovaDesign(
            measure_field_name=get_unlabelled(self.measure.value),
            grouping_field_name=get_unlabelled(self.select_grouping_variable.value),
            group_values=group_vals,
            csv_file_path=shared[SharedKey.CSV_FPATH],
            data_label_mappings=data_labels_param.value,
            show_in_web_browser=False,
            output_file_path=DEFAULT_OUTPUT_FOLDER / f"ANOVA Report generated at {now}.html"
        )
        show_output_tab_param.value = True
        # store HTML
        html_design = anova_design.to_html_design()
        html_param.value = html_design.html_item_str
        give_output_tab_focus_param.value = True
        ## clear and hide stats config
        open_stats_config_modal = shared[SharedKey.ACTIVE_STATS_CONFIG_MODAL]
        # open_stats_config_modal.clear()
        open_stats_config_modal.hide()
        shared[SharedKey.ACTIVE_STATS_CONFIG_MODAL] = None
        ## clear and hide stats chooser if open
        if shared.get(SharedKey.ACTIVE_STATS_CHOOSER_MODAL):
            open_stats_chooser_modal = shared[SharedKey.ACTIVE_STATS_CHOOSER_MODAL]
            # open_stats_chooser_modal.clear()  ## TODO: don't wipe - just reinitialise it
            open_stats_chooser_modal.hide()
            shared[SharedKey.ACTIVE_STATS_CHOOSER_MODAL] = None
        ## store location to save output (if user wants to)
        shared[SharedKey.CURRENT_OUTPUT_FPATH] = anova_design.output_file_path  ## can access later if they want to save the result

    @staticmethod
    def set_user_msg(msg: str):
        if msg:
            alert = pn.pane.Alert(msg, alert_type='warning')
        else:
            alert = None
        return alert

    def ui(self):
        form = pn.layout.WidgetBox(
            pn.pane.Markdown("## Configure ANOVA then get results"),
            self.user_msg_or_none,
            self.measure,
            self.select_grouping_variable,
            "Click values to select them (must select more than one)",
            self.values_multiselect_or_none,
            self.btn_run_analysis, self.btn_close,
            self.set_grouping_var, self.group_value_selector,
            name=f"ANOVA Design", margin=20,
        )
        return form
