import panel as pn

from sofastats.ui.conf import SharedKey, StatsOption
from sofastats.ui.state import shared
from sofastats.ui.stats.anova_form import ANOVAForm

pn.extension('modal')


def get_stats_config_modal(stats_test: StatsOption, btn_close: pn.widgets.Button):
    if stats_test == StatsOption.ANOVA:
        anova_form_obj=ANOVAForm(btn_close)
        form = anova_form_obj.ui()
    else:
        form = pn.pane.Markdown("Under construction")
    stats_config_modal = pn.layout.Modal(
        form,
        background_close=True,
    )
    shared[SharedKey.ACTIVE_STATS_CONFIG_MODAL] = stats_config_modal
    return stats_config_modal
