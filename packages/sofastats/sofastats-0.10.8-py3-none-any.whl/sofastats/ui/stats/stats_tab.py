"""
Stats form, stats chooser, and stats config

Using nested modals.
Upper modals and buttons opening and closing them must be defined inside lower modals.
"""
import panel as pn

from sofastats.ui.conf import StatsOption
from sofastats.ui.stats.stats_chooser import get_stats_chooser_modal
from sofastats.ui.stats.stats_config import get_stats_config_modal

pn.extension('modal')

def get_stats_main():
    servables = pn.Column()
    stats_need_help_style = {
        'margin-top': '20px',
        'background-color': '#F6F6F6',
        'border': '2px solid black',
        'border-radius': '5px',
        'padding': '0 5px 5px 5px',
    }
    stats_text = pn.pane.Markdown("### Need help choosing a test?", width_policy='max')
    stats_chooser_modal = get_stats_chooser_modal()
    btn_open_stats_chooser_styles = {
        'margin-top': '10px',
    }
    btn_open_stats_chooser = pn.widgets.Button(name="Test Selector", button_type='primary', styles=btn_open_stats_chooser_styles)
    def open_stats_chooser(_event):
        stats_chooser_modal.show()
    btn_open_stats_chooser.on_click(open_stats_chooser)
    get_help_row = pn.Row(stats_text, btn_open_stats_chooser, styles=stats_need_help_style, width=800)

    stats_btn_kwargs = {
        'button_type': 'primary',
        'width': 350,
    }
    btn_anova = pn.widgets.Button(name='ANOVA', description="ANOVA", **stats_btn_kwargs)
    btn_chi_square = pn.widgets.Button(name='Chi Square', description='Chi Square', **stats_btn_kwargs)
    btn_indep_ttest = pn.widgets.Button(name='Independent Samples T-Test', description='Independent Samples T-Test', **stats_btn_kwargs)
    btn_kruskal_wallis = pn.widgets.Button(name='Kruskal-Wallis H', description='Kruskal-Wallis H', **stats_btn_kwargs)
    btn_mann_whitney = pn.widgets.Button(name='Mann-Whitney U', description='Mann-Whitney U', **stats_btn_kwargs)
    btn_normality = pn.widgets.Button(name='Normality', description='Normality', **stats_btn_kwargs)
    btn_paired_ttest = pn.widgets.Button(name='Paired Samples T-Test', description='Paired Samples T-Test', **stats_btn_kwargs)
    btn_pearsons = pn.widgets.Button(name="Pearson's R Correlation", description="Pearson's R Correlation", **stats_btn_kwargs)
    btn_spearmans = pn.widgets.Button(name="Spearman's R Correlation", description="Spearman's R Correlation", **stats_btn_kwargs)
    btn_wilcoxon = pn.widgets.Button(name='Wilcoxon Signed Ranks', description='Wilcoxon Signed Ranks', **stats_btn_kwargs)
    btn_close = pn.widgets.Button(name="Close")
    def open_anova_config(_event):
        stats_config_modal = get_stats_config_modal(StatsOption.ANOVA, btn_close)
        servables.append(stats_config_modal)
        stats_config_modal.show()
        def close_config_modal(_event):
            stats_config_modal.hide()
        btn_close.on_click(close_config_modal)
    btn_anova.on_click(open_anova_config)
    def test_under_construction(event):
        stats_config_modal = pn.layout.Modal(pn.pane.Markdown(f"{event.obj.name} under construction"))
        servables.append(stats_config_modal)
        stats_config_modal.show()
    btn_chi_square.on_click(test_under_construction)
    btn_indep_ttest.on_click(test_under_construction)
    btn_kruskal_wallis.on_click(test_under_construction)
    btn_mann_whitney.on_click(test_under_construction)
    btn_normality.on_click(test_under_construction)
    btn_paired_ttest.on_click(test_under_construction)
    btn_pearsons.on_click(test_under_construction)
    btn_spearmans.on_click(test_under_construction)
    btn_wilcoxon.on_click(test_under_construction)

    stats_col = pn.Column(
        get_help_row,
        pn.pane.Markdown("Select the type of test you want to run"),
        pn.Row(
            pn.Column(btn_anova, btn_chi_square, btn_indep_ttest, btn_kruskal_wallis, btn_mann_whitney),
            pn.Column(btn_normality, btn_paired_ttest, btn_pearsons, btn_spearmans, btn_wilcoxon),
        ),
        servables,
    )
    return pn.Column(stats_col, stats_chooser_modal, )
