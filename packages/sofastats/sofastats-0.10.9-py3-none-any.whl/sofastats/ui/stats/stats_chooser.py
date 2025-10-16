from _collections_abc import Collection

import panel as pn

from sofastats.ui.conf import DiffVsRel, IndepVsPaired, Normal, NumGroups, OrdinalVsCategorical, SharedKey, StatsOption
from sofastats.ui.state import (
    difference_not_relationship_param, independent_not_paired_for_diff_param,
    normal_not_abnormal_for_diff_param, normal_not_abnormal_for_rel_param,
    ordinal_at_least_for_rel_param, shared,
    two_not_three_plus_groups_for_diff_param,
)
from sofastats.ui.stats.stats_config import get_stats_config_modal

pn.extension('modal')

## https://panel.holoviz.org/how_to/styling/apply_css.html
progress_stylesheet = """
progress {
  height: 5px;
}
"""
chooser_progress = pn.indicators.Progress(name='Progress', value=0, width=400, height=5, height_policy='fixed',
    stylesheets=[progress_stylesheet])

def set_chooser_progress(items: Collection[StatsOption]):
    """
    We start with all items being in contention and end up with 1 and only 1.
    So we go from 9 to 1 which is 8 steps.
    In contention  9   8   7   6   5   4   3   2   1
    Progress       0   1   2   3   4   5   6   7   8
    So 9-9, 9-8, ... 9-1
    So len(all options) - len(in contention)
    """
    n_all_options = len(StatsOption)
    n_in_contention = len(items)
    score = n_all_options - n_in_contention
    total = n_all_options - 1
    progress_fraction = score / total
    progress_value = round(progress_fraction * 100)
    chooser_progress.value = progress_value


class SubChooser:

    ## https://panel.holoviz.org/how_to/styling/apply_css.html
    btn_stats_config_stylesheet = """
    :host(.solid) .bk-btn.bk-btn-primary {
      font-size: 14px;
    }
    """
    btn_open_stats_config = pn.widgets.Button(
        name="Configure Test", button_type='primary', stylesheets=[btn_stats_config_stylesheet])

    @staticmethod
    def respond_to_choices(difference_not_relationship_value, two_not_three_plus_groups_for_diff_value,
            normal_not_abnormal_for_diff_value, independent_not_paired_for_diff_value,
            ordinal_at_least_for_rel_value,
            normal_not_abnormal_for_rel_value):
        if difference_not_relationship_value == DiffVsRel.UNKNOWN:
            items = sorted(StatsOption)
        elif difference_not_relationship_value == DiffVsRel.DIFFERENCE:
            if two_not_three_plus_groups_for_diff_value == NumGroups.UNKNOWN:
                if normal_not_abnormal_for_diff_value == Normal.UNKNOWN:
                    items = [StatsOption.ANOVA, StatsOption.TTEST_INDEP, StatsOption.TTEST_PAIRED,
                             StatsOption.KRUSKAL_WALLIS, StatsOption.MANN_WHITNEY, StatsOption.WILCOXON]
                elif normal_not_abnormal_for_diff_value == Normal.NORMAL:
                    items = [StatsOption.ANOVA, StatsOption.TTEST_INDEP, StatsOption.TTEST_PAIRED]
                elif normal_not_abnormal_for_diff_value == Normal.NOT_NORMAL:
                    items = [StatsOption.KRUSKAL_WALLIS, StatsOption.MANN_WHITNEY, StatsOption.WILCOXON]
                else:
                    raise Exception(F"Unexpected {normal_not_abnormal_for_diff_value=}")
            elif two_not_three_plus_groups_for_diff_value == NumGroups.TWO:
                if normal_not_abnormal_for_diff_value == Normal.UNKNOWN:
                    if independent_not_paired_for_diff_value == IndepVsPaired.UNKNOWN:
                        items = [StatsOption.TTEST_INDEP, StatsOption.MANN_WHITNEY,
                                 StatsOption.TTEST_PAIRED, StatsOption.WILCOXON]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.INDEPENDENT:
                        items = [StatsOption.TTEST_INDEP, StatsOption.MANN_WHITNEY]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.PAIRED:
                        items = [StatsOption.TTEST_PAIRED, StatsOption.WILCOXON]
                    else:
                        raise Exception(F"Unexpected {independent_not_paired_for_diff_value=}")
                elif normal_not_abnormal_for_diff_value == Normal.NORMAL:
                    if independent_not_paired_for_diff_value == IndepVsPaired.UNKNOWN:
                        items = [StatsOption.TTEST_INDEP, StatsOption.TTEST_PAIRED]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.INDEPENDENT:
                        items = [StatsOption.TTEST_INDEP, ]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.PAIRED:
                        items = [StatsOption.TTEST_PAIRED, ]
                    else:
                        raise Exception(F"Unexpected {independent_not_paired_for_diff_value=}")
                elif normal_not_abnormal_for_diff_value == Normal.NOT_NORMAL:
                    if independent_not_paired_for_diff_value == IndepVsPaired.UNKNOWN:
                        items = [StatsOption.MANN_WHITNEY, StatsOption.WILCOXON]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.INDEPENDENT:
                        items = [StatsOption.MANN_WHITNEY]
                    elif independent_not_paired_for_diff_value == IndepVsPaired.PAIRED:
                        items = [StatsOption.WILCOXON, ]
                    else:
                        raise Exception(F"Unexpected {independent_not_paired_for_diff_value=}")
                else:
                    raise Exception(F"Unexpected {normal_not_abnormal_for_diff_value=}")
            elif two_not_three_plus_groups_for_diff_value == NumGroups.THREE_PLUS:
                if normal_not_abnormal_for_diff_value == Normal.UNKNOWN:
                    items = [StatsOption.ANOVA, StatsOption.KRUSKAL_WALLIS]
                elif normal_not_abnormal_for_diff_value == Normal.NORMAL:
                    items = [StatsOption.ANOVA, ]
                elif normal_not_abnormal_for_diff_value == Normal.NOT_NORMAL:
                    items = [StatsOption.KRUSKAL_WALLIS, ]
                else:
                    raise Exception(F"Unexpected {normal_not_abnormal_for_diff_value=}")
            else:
                raise Exception(F"Unexpected {two_not_three_plus_groups_for_diff_value=}")
        elif difference_not_relationship_value == DiffVsRel.RELATIONSHIP:
            if ordinal_at_least_for_rel_value == OrdinalVsCategorical.UNKNOWN:
                items = [StatsOption.CHI_SQUARE, StatsOption.SPEARMANS, StatsOption.PEARSONS]
            elif ordinal_at_least_for_rel_value == OrdinalVsCategorical.ORDINAL:
                if normal_not_abnormal_for_rel_value == Normal.UNKNOWN:
                    items = [StatsOption.SPEARMANS, StatsOption.PEARSONS]
                elif normal_not_abnormal_for_rel_value == Normal.NORMAL:
                    items = [StatsOption.PEARSONS, ]
                elif normal_not_abnormal_for_rel_value == Normal.NOT_NORMAL:
                    items = [StatsOption.SPEARMANS, ]
                else:
                    raise Exception(F"Unexpected {normal_not_abnormal_for_rel_value=}")
            elif ordinal_at_least_for_rel_value == OrdinalVsCategorical.CATEGORICAL:
                items = [StatsOption.CHI_SQUARE, ]
            else:
                raise Exception(F"Unexpected {ordinal_at_least_for_rel_value=}")
        else:
            raise Exception(F"Unexpected {difference_not_relationship_value=}")
        div_styles = {
            'margin-top': '-30px',
            'margin-bottom': '0',
            'padding': '0 5px 5px 5px',
        }
        internal_css = """
        <style>
            h1 {
              color: #0072b5;
              font-size: 14px;
            }
        </style>
        """
        test_has_been_identified = len(items) == 1
        if test_has_been_identified:
            stats_test = items[0]
            recommendation_html = pn.pane.HTML(styles=div_styles, max_width=500)
            if stats_test == StatsOption.ANOVA:
                content = f"""\
                {internal_css}
                <h1>ANOVA (Analysis Of Variance)</h1>
                <p>The ANOVA (Analysis Of Variance) is good for seeing if there is a difference in means between multiple groups
                when the data is numerical and adequately normal. Generally the ANOVA is robust to non-normality.</p>
                <p>You can evaluate normality by clicking on the "Check Normality" button (under construction).</p>
                <p>The Kruskal-Wallis H may be preferable if your data is not adequately normal.</p>
                """
            elif stats_test == StatsOption.CHI_SQUARE:
                content = f"""\
                {internal_css}
                <h1>Chi Square Test</h1>
                <p>The Chi Square test is one of the most widely used tests in social science.
                It is good for seeing if the results for two variables are independent or related.
                Is there a relationship between gender and income group for example?</p>
                """
            elif stats_test == StatsOption.KRUSKAL_WALLIS:
                content = f"""\
                {internal_css}
                <h1>Kruskal-Wallis H Test</h1>
                <p>The Kruskal-Wallis H is good for seeing if there is a difference in values between multiple groups
                when the data is at least ordered (ordinal).</p>
                <p>You can evaluate normality by clicking on the "Check Normality" button (under construction).</p>
                <p>The ANOVA (Analysis Of Variance) may still be preferable if your data is numerical and adequately normal.</p>
                """
            else:
                content = f"""\
                {internal_css}
                <p>Under Construction</p>
                """
            recommendation_html.object = content
            SubChooser.btn_open_stats_config.name = f"Configure {stats_test} ⮕"
            btn_close = pn.widgets.Button(name="Close")
            stats_config_modal = get_stats_config_modal(stats_test, btn_close)
            def open_stats_config_modal(_event):
                stats_config_modal.show()
            def close_stats_config_modal(_event):
                stats_config_modal.hide()
            btn_close.on_click(close_stats_config_modal)

            SubChooser.btn_open_stats_config.on_click(open_stats_config_modal)

            col_recommendation_styles = {
                'background-color': '#F6F6F6',
                'border': '2px solid black',
                'border-radius': '5px',
                'padding': '0 5px 5px 5px',
            }
            col_recommendation = pn.Column(
                recommendation_html, SubChooser.btn_open_stats_config,
                stats_config_modal,
                styles=col_recommendation_styles)
        else:
            col_recommendation = None
        set_chooser_progress(items)
        return col_recommendation

    ## DIFFERENCE ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    @staticmethod
    def _set_indep_vs_paired_param(indep_vs_paired_value):
        independent_not_paired_for_diff_param.value = indep_vs_paired_value

    @staticmethod
    def get_indep_vs_paired_chooser(two_not_three_plus_groups_for_diff_param_val):
        indep_vs_paired_chooser_or_none = None
        if two_not_three_plus_groups_for_diff_param_val == NumGroups.TWO:
            independent_groups_radio = pn.widgets.RadioButtonGroup(
                name='Independent Groups',
                options=[
                    IndepVsPaired.INDEPENDENT,
                    IndepVsPaired.PAIRED,
                    IndepVsPaired.UNKNOWN,
                ],
                button_type='success', button_style='outline',
                description=("Are the groups independent e.g. 'NZ' and 'USA', or paired "
                    "(e.g. 'Student score before tutoring' and 'Student score after tutoring')?"),
                value=IndepVsPaired.UNKNOWN,
            )
            indep_vs_paired_param_setter = pn.bind(SubChooser._set_indep_vs_paired_param, independent_groups_radio)
            indep_vs_paired_chooser_or_none = pn.Column(
                pn.pane.Markdown("Are the Groups Independent or Paired?"), independent_groups_radio,
                indep_vs_paired_param_setter,
            )
        return indep_vs_paired_chooser_or_none

    @staticmethod
    def _set_norm_for_diff_param(norm_vs_abnormal_value):
        normal_not_abnormal_for_diff_param.value = norm_vs_abnormal_value

    @staticmethod
    def _set_num_of_groups_param(num_of_groups_value):
        two_not_three_plus_groups_for_diff_param.value = num_of_groups_value

    @staticmethod
    def difference_sub_chooser():  ## <====================== DIFFERENCE Main Act!
        normal_for_diff_radio = pn.widgets.RadioButtonGroup(
            name='Normality',
            options=[
                Normal.NORMAL,
                Normal.NOT_NORMAL,
                Normal.UNKNOWN,
            ],
            button_type='success', button_style='outline',
            description=("Is your data normal "
                "i.e. are the values numbers that at least roughly follow a normal distribution curve (bell curve)?"),
            value=Normal.UNKNOWN,
        )
        norm_for_diff_param_setter = pn.bind(SubChooser._set_norm_for_diff_param, normal_for_diff_radio)
        number_of_groups_radio = pn.widgets.RadioButtonGroup(
            name='Number of Groups',
            options=[
                NumGroups.TWO,
                NumGroups.THREE_PLUS,
                NumGroups.UNKNOWN,
            ],
            button_type='success', button_style='outline',
            description=("Are you looking at the difference between two groups "
                "e.g. 'Male' vs 'Female' or between three or more groups e.g. 'Archery' vs 'Badminton' vs 'Basketball'?"),
            value=NumGroups.UNKNOWN,
        )
        indep_vs_paired_chooser = pn.bind(SubChooser.get_indep_vs_paired_chooser, number_of_groups_radio)
        num_of_groups_param_setter = pn.bind(SubChooser._set_num_of_groups_param, number_of_groups_radio)
        col_items = [
            pn.pane.Markdown("Data Values are Normal?"), normal_for_diff_radio,
            pn.pane.Markdown("How Many Groups?"), number_of_groups_radio,
            indep_vs_paired_chooser,
            norm_for_diff_param_setter, num_of_groups_param_setter,
        ]
        sub_chooser = pn.Column(*col_items)
        return sub_chooser

    ## RELATIONSHIP ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @staticmethod
    def _set_norm_for_rel(normal_not_abnormal_for_rel_value):
        normal_not_abnormal_for_rel_param.value = normal_not_abnormal_for_rel_value

    @staticmethod
    def get_normal_chooser_or_none(ordinal_vs_categorical_val):
        normal_chooser_or_none = None
        if ordinal_vs_categorical_val == OrdinalVsCategorical.ORDINAL:
            normal_for_rel_radio = pn.widgets.RadioButtonGroup(
                name='Normality',
                options=[
                    Normal.NORMAL,
                    Normal.NOT_NORMAL,
                    Normal.UNKNOWN,
                ],
                button_type='success', button_style='outline',
                description=("Is your data normal "
                    "i.e. are the values numbers that at least roughly follow a normal distribution curve (bell curve)?"),
                value=Normal.UNKNOWN,
            )
            norm_for_rel_param_setter = pn.bind(SubChooser._set_norm_for_rel, normal_for_rel_radio)
            normal_chooser_or_none = pn.Column(pn.pane.Markdown("Data Values are Normal?"), normal_for_rel_radio,
                norm_for_rel_param_setter)
        return normal_chooser_or_none

    @staticmethod
    def _set_ordinal_vs_categorical(ordinal_vs_categorical_value):
        # print(f"ordinal_at_least_for_rel_param is now '{ordinal_vs_categorical_value}'")
        ordinal_at_least_for_rel_param.value = ordinal_vs_categorical_value

    @staticmethod
    def relationship_sub_chooser():  ## <====================== RELATIONSHIP Main Act!
        ordinal_vs_categorical_radio = pn.widgets.RadioButtonGroup(
            name='Ordinal vs Categorical',
            options=[
                OrdinalVsCategorical.ORDINAL,
                OrdinalVsCategorical.CATEGORICAL,
                OrdinalVsCategorical.UNKNOWN,
            ],
            button_type='success', button_style='outline',
            description=("Do the values have a true sort order (ordinal data) e.g. 1, 2, 3? "
                "Or are they just names e.g. 'NZ', 'Denmark', 'Sri Lanka' (categorical data)?"),
            value=Normal.UNKNOWN,
        )
        normal_chooser_or_none = pn.bind(SubChooser.get_normal_chooser_or_none, ordinal_vs_categorical_radio)
        ordinal_vs_categorical_param_setter = pn.bind(SubChooser._set_ordinal_vs_categorical, ordinal_vs_categorical_radio)
        sub_chooser = pn.Column(
            pn.pane.Markdown("Ordinal or Categorical?"), ordinal_vs_categorical_radio,
            normal_chooser_or_none, ordinal_vs_categorical_param_setter,
        )
        return sub_chooser

    @staticmethod
    def get_ui(diff_not_rel: DiffVsRel) -> pn.Column | None:
        recommendation = pn.bind(SubChooser.respond_to_choices,
            difference_not_relationship_param.param.value,
            two_not_three_plus_groups_for_diff_param.param.value,
            normal_not_abnormal_for_diff_param.param.value,
            independent_not_paired_for_diff_param.param.value,
            ordinal_at_least_for_rel_param.param.value,
            normal_not_abnormal_for_rel_param.param.value)
        if diff_not_rel == DiffVsRel.UNKNOWN:
            sub_chooser = None
        elif diff_not_rel == DiffVsRel.DIFFERENCE:
            sub_chooser = SubChooser.difference_sub_chooser()
        elif diff_not_rel == DiffVsRel.RELATIONSHIP:
            sub_chooser = SubChooser.relationship_sub_chooser()
        else:
            raise ValueError(f"Unexpected {diff_not_rel=}")
        col_chooser = pn.Column(sub_chooser, recommendation,)
        return col_chooser


def get_stats_chooser_modal():
    difference_vs_relationship_radio = pn.widgets.RadioButtonGroup(
        name='Difference vs Relationship',
        options=[
            DiffVsRel.DIFFERENCE,
            DiffVsRel.RELATIONSHIP,
            DiffVsRel.UNKNOWN,
        ],
        button_type='primary', button_style='outline',
        description=("Are you trying to see if there are differences between groups "
            "(e.g. different mean height between players of different sports) "
            "or relationships (e.g. between education level and income)?"),
        value=DiffVsRel.UNKNOWN,
    )

    def set_diff_vs_rel_param(difference_vs_relationship_value):
        difference_not_relationship_param.value = difference_vs_relationship_value

    sub_chooser_or_none = pn.bind(SubChooser.get_ui, difference_vs_relationship_radio)
    diff_vs_rel_param_setter = pn.bind(set_diff_vs_rel_param, difference_vs_relationship_radio)

    chooser_col = pn.Column(
        pn.pane.Markdown("# Test Selection"),
        chooser_progress,
        pn.pane.Markdown("### Answer the questions below to find the best statistical test to use"),
        pn.pane.Markdown("Finding differences or relationships?"),
        difference_vs_relationship_radio,
        sub_chooser_or_none,
        diff_vs_rel_param_setter,
    )

    stats_chooser_modal = pn.layout.Modal(
        chooser_col,
        sizing_mode='stretch_width',
        background_close=True)
    shared[SharedKey.ACTIVE_STATS_CHOOSER_MODAL] = stats_chooser_modal
    return stats_chooser_modal
