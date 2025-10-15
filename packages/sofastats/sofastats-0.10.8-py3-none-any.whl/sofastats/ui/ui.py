"""
c && cd ~/projects/sofastats/src/sofastats/ui && panel serve ui.py
"""
import html

import panel as pn

from sofastats.ui.conf import SharedKey
from sofastats.ui.data import Data
from sofastats.ui.charts_and_tables import get_charts_and_tables_main
from sofastats.ui.state import (data_toggle, give_output_tab_focus_param, got_data_param, html_param, shared,
    show_output_saved_msg_param, show_output_tab_param)
from sofastats.ui.stats.stats_tab import get_stats_main

pn.extension('modal')
pn.extension('tabulator')

## look in main css for template used to see what controls sidebar
## https://community.retool.com/t/how-to-open-a-modal-component-in-full-screen/18720/4
css = """
#main {
    border-left: solid grey 3px;
}
"""
pn.extension(raw_css=[css])

data_col = Data().ui()
charts_and_tables_col = get_charts_and_tables_main()
stats_col = get_stats_main()

def save_output(_event):
    html_text = html_param.value
    SharedKey.CURRENT_OUTPUT_FPATH.parent.mkdir(exist_ok=True)  ## only make as required - minimise messing with user's file system
    with open(shared[SharedKey.CURRENT_OUTPUT_FPATH], 'w') as f:
        f.write(html_text)
    show_output_saved_msg_param.value = True

def show_output(html_value: str, show_output_saved_msg_value):
    if html_value:
        btn_save_output = pn.widgets.Button(
            name="Save Results", description="Save results so you can share them e.g. email as an attachment")
        btn_save_output.on_click(save_output)
        escaped_html = html.escape(html_value)
        iframe_html = f'<iframe srcdoc="{escaped_html}" style="height:100%; width:100%" frameborder="0"></iframe>'
        html_output_widget = pn.pane.HTML(iframe_html, sizing_mode='stretch_both')
        if show_output_saved_msg_value:
            saved_msg = f"Saved output to '{shared[SharedKey.CURRENT_OUTPUT_FPATH]}'"
            saved_alert = pn.pane.Alert(saved_msg, alert_type='info')
            html_col = pn.Column(btn_save_output, saved_alert, html_output_widget)
        else:
            html_col = pn.Column(btn_save_output, html_output_widget)
    else:
        html_output_widget = pn.pane.HTML('Waiting for some output to be generated ...',
            sizing_mode="stretch_both")
        html_col = pn.Column(html_output_widget)
    return html_col

html_output = pn.bind(show_output, html_param.param.value, show_output_saved_msg_param.param.value)

def get_tabs(show_output_tab_value, give_output_tab_focus_value, got_data_value):

    if not got_data_value:
        return None

    if show_output_tab_value:
        tabs = pn.layout.Tabs(
            ("Charts & Tables", charts_and_tables_col),
            ("Stats Test", stats_col),
            ("Results", html_output),
        )
    else:
        tabs = pn.layout.Tabs(
            ("Charts & Tables", charts_and_tables_col),
            ("Stats Test", stats_col),
        )

    def allow_user_to_set_tab_focus(_current_active_tab):
        give_output_tab_focus_param.value = False

    user_tab_focus = pn.bind(allow_user_to_set_tab_focus, tabs.param.active)

    if give_output_tab_focus_value:
        tabs.active = 2
    return pn.Column(tabs, user_tab_focus)

output_tabs = pn.bind(get_tabs,
    show_output_tab_param.param.value, give_output_tab_focus_param.param.value, got_data_param.param.value)

def get_btn_data_toggle(got_data_value):
    if not got_data_value:
        return None
    btn_data_toggle = pn.widgets.Button(  ## seems like we must define in same place as you are watching it
        name="🞀 Close Data Window",
        description="Close uploaded data window",
        button_type="light", button_style='solid',
        styles={
            'margin-left': '-20px', 'margin-bottom': '20px', 'margin-right': '20px',
            'border': '2px solid grey',
            'border-radius': '5px',
        })

    @pn.depends(btn_data_toggle, watch=True)
    def _update_main(_):
        data_toggle.value = not data_toggle.value

        if not data_toggle.value:
            btn_data_toggle.name = "Open Data Window 🞂"
            btn_data_toggle.description = "See your uploaded data again"
        else:
            btn_data_toggle.name = "🞀 Close Data Window"
            btn_data_toggle.description = "Close uploaded data window"

    return btn_data_toggle

btn_data_toggle_or_none = pn.bind(get_btn_data_toggle, got_data_param.param.value)

pn.template.VanillaTemplate(
    title='SOFA Stats',
    sidebar_width=750,
    sidebar=[data_col, ],
    main=[btn_data_toggle_or_none, data_toggle, output_tabs, ],
).servable()
