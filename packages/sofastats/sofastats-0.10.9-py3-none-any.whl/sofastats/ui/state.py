import panel as pn
import param

from sofastats.ui.conf import Alternative, DiffVsRel, IndepVsPaired, Normal, NumGroups, OrdinalVsCategorical, SharedKey

shared = {
    SharedKey.SERVABLES: pn.Column()
}  ## common state for app that is not param

class Bool(param.Parameterized):
    value = param.Boolean(default=False)

class Choice(param.Parameterized):
    value = param.String(default=Alternative.NONE)

class Dict(param.Parameterized):
    value = param.Dict(default=None)

class Text(param.Parameterized):
    value = param.String(default=None)

## PARAMS
## data
got_data_param = Bool(value=False)
data_labels_param = Dict(value={})

## stats helper
difference_not_relationship_param = Choice(value=DiffVsRel.UNKNOWN)

two_not_three_plus_groups_for_diff_param = Choice(value=NumGroups.UNKNOWN)
normal_not_abnormal_for_diff_param = Choice(value=Normal.UNKNOWN)
independent_not_paired_for_diff_param = Choice(value=IndepVsPaired.UNKNOWN)

ordinal_at_least_for_rel_param = Choice(value=OrdinalVsCategorical.UNKNOWN)
normal_not_abnormal_for_rel_param = Choice(value=Normal.UNKNOWN)

## output / results
give_output_tab_focus_param = Bool(value=False)
html_param = Text(value='')
show_output_tab_param = Bool(value=False)
show_output_saved_msg_param = Bool(value=False)

class SidebarToggle(pn.custom.JSComponent):
    value = param.Boolean(doc="If True the sidebar is visible, if False it is hidden")

    _esm = """
export function render({ model }) {
    model.on('value', () => {
        if (model.value) {
            document.getElementById('sidebar-button').style.display = 'none';
            document.getElementById('sidebar').style.display = 'block';
        } else {
            document.getElementById('sidebar-button').style.display = 'none';
            document.getElementById('sidebar').style.display = 'none';
        }
    });
}
"""

data_toggle = SidebarToggle(value=True)
