from enum import StrEnum

class Alternative(StrEnum):
    NONE = 'None'
    TRUE = 'True'
    FALSE = 'False'

class DiffVsRel(StrEnum):
    DIFFERENCE = 'Difference'
    RELATIONSHIP = 'Relationship'
    UNKNOWN = 'Not Sure'

class IndepVsPaired(StrEnum):
    INDEPENDENT = 'Independent'
    PAIRED = 'Paired'
    UNKNOWN = 'Not Sure'

class Normal(StrEnum):
    NORMAL = 'Normal'
    NOT_NORMAL = 'Not Normal'
    UNKNOWN = 'Not Sure'

class NumGroups(StrEnum):
    TWO = '2 Groups'
    THREE_PLUS = '3+ Groups'
    UNKNOWN = 'Not Sure'

class OrdinalVsCategorical(StrEnum):
    ORDINAL = 'Ordinal'
    CATEGORICAL = 'Categorical'
    UNKNOWN = 'Not Sure'

class SharedKey(StrEnum):
    ACTIVE_STATS_CHOOSER_MODAL = 'active_stats_chooser_modal'  ## so I can hide it from anywhere
    ACTIVE_STATS_CONFIG_MODAL = 'active_stats_config_modal'
    CSV_FPATH = 'csv_fpath'
    CURRENT_OUTPUT_FPATH = 'current_output_fpath'
    DF_CSV = 'df_csv'
    SERVABLES = 'servables'

class StatsOption(StrEnum):
    ANOVA = 'ANOVA'
    CHI_SQUARE = 'Chi Square'
    KRUSKAL_WALLIS = 'Kruskal-Wallis H'
    MANN_WHITNEY = 'Mann-Whitney U'
    PEARSONS = "Pearson's R Correlation"
    SPEARMANS = "Spearman's R Correlation"
    TTEST_INDEP = 'Independent Samples T-Test'
    TTEST_PAIRED = 'Paired Samples T-Test'
    WILCOXON = 'Wilcoxon Signed Ranks'
