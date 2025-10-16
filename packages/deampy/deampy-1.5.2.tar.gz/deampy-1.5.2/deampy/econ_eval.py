import stat
import string
import warnings

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import scipy.stats as stat
# from scipy.stats import pearsonr
from numpy import corrcoef
from numpy import exp, power, average
from numpy.random import RandomState

import deampy.format_functions as F
from deampy.in_out_functions import write_csv
from deampy.plots.econ_eval_plots import add_curves_to_ax, add_min_monte_carlo_samples_to_ax, add_grids
from deampy.plots.plot_support import output_figure, add_labels_to_panels
from deampy.statistics import SummaryStat, RatioOfMeansStatPaired
from deampy.support.econ_eval_support import *
from deampy.support.misc_classes import *
from deampy.support.misc_functions import convert_lnl_to_prob, get_prob_x_greater_than_ys

Params = {
    'plot.legend.fontsize': 7,
    'plot.legend.loc': 'upper left',

    'ce.cloud.edgecolors': 'w',
    'ce.frontier.color': 'k',
    'ce.frontier.transparency': 0.6,
    'ce.frontier.line_width': 2,
    'ce.frontier.label.shift_x': -0.01, # shift labels to right or left (proportional to the length of the x_axis)
    'ce.frontier.label.shift_y': 0.01, # shift labels to right or left (proportional to the length of the x_axis)

    'ceac.transparency': 0.75,
    'ceac.line_width': 0.75,
    'ceaf.line_width': 2.5,

    'nmb.transparency': 0.75,
    'nmb.line_width': 0.75,
    'nmb.interval.transparency': 0.25,
    'nmb.frontier.line_width': 2.5,
    'nmb.frontier.label.shift_x': -0.01, # shift labels to right or left (proportional to the length of the x_axis)
    'nmb.frontier.label.shift_y': 0.03, # shift labels to right or left (proportional to the length of the x_axis)
    'evpi.plot.label': 'Perfect Information',

    'elc.transparency': 0.75,
    'elc.line_width': 0.75,
    'elc.frontier.line_width': 2.5
}

# warnings.filterwarnings("always")
NUM_OF_BOOTSTRAPS = 1000  # number of bootstrap samples to calculate confidence intervals for ICER


def pv_single_payment(payment, discount_rate, discount_period, discount_continuously=False):
    """ calculates the present value of a single future payment
    :param payment:  to calculate the present value for
    :param discount_rate: discount rate
    :param discount_period: number of periods to discount the payment
    :param discount_continuously: set to True to discount continuously
    :return: payment/(1+discount_rate)^discount_period for discrete discounting
             payment * exp(-discounted_rate*discount_period) for continuous discounting """

    # error checking
    if discount_continuously:
        pass
    else:
        assert type(discount_period) is int, "discount_period should be an integer number."
    if discount_rate < 0 or discount_rate > 1:
        raise ValueError("discount_rate should be a number between 0 and 1.")
    if discount_period <= 0:
        raise ValueError("discount_period should be greater than 0.")

    # calculate the present value
    if discount_continuously:
        return payment * exp(-discount_rate * discount_period)
    else:
        return payment * power(1 + discount_rate, -discount_period)


def pv_continuous_payment(payment, discount_rate, discount_period):
    """ calculates the present value of a future continuous payment (discounted continuously)
    :param payment: payment to calculate the present value for
    :param discount_rate: discount rate
    :param discount_period: (tuple) in the form of (l, u) specifying the period where
                             the continuous payment is received
    :return: payment * (exp(-discount_rate*l - exp(-discount_rate*u))/discount_rate
    """
    assert type(discount_period) is tuple, "discount_period should be a tuple (l, u)."
    if discount_rate < 0 or discount_rate > 1:
        raise ValueError("discount_rate should be a number between 0 and 1.")

    if discount_rate == 0:
        return payment * (discount_period[1] - discount_period[0])
    else:
        return payment/discount_rate * \
               (exp(-discount_rate*discount_period[0])
                - exp(-discount_rate*discount_period[1]))


def equivalent_annual_value(present_value, discount_rate, discount_period):
    """  calculates the equivalent annual value of a present value
    :param present_value:
    :param discount_rate: discount rate (per period)
    :param discount_period: number of periods to discount the payment
    :return: discount_rate*present_value/(1-pow(1+discount_rate, -discount_period))
    """

    # error checking
    assert type(discount_period) is int, "discount_period should be an integer number."
    if discount_rate < 0 or discount_rate > 1:
        raise ValueError("discount_rate should be a number between 0 and 1.")
    if discount_period < 0:
        raise ValueError("discount_period cannot be less than 0.")

    # calculate the equivalent annual value
    return discount_rate*present_value/(1-power(1+discount_rate, -discount_period))


def get_var_of_inmb(wtp, st_d_cost, st_d_effect, corr):
    """
    :param wtp: (double) willingness-to-pay threshold
    :param st_d_cost: (double) st dev of incremental cost observations
    :param st_d_effect: (double) st dev of incremental effect observations
    :param corr (double) correlation between incremental cost and effect
    :return: the variance of incremental NMB
    """

    variance = wtp ** 2 * st_d_effect ** 2 + st_d_cost ** 2 - 2 * wtp * corr * st_d_effect * st_d_cost

    # if np.isnan(variance) or variance < 0:
    #     raise ValueError(st_d_effect, st_d_cost, corr)

    return variance


def get_variance_of_incremental_nmb(wtp, delta_costs, delta_effects):
    """
    :param wtp: (double) willingness-to-pay threshold
    :param delta_costs: (list) of incremental cost observations
    :param delta_effects: (list) of incremental effect observations
    :return: the variance of incremental NMB
    """

    st_d_cost = np.std(delta_costs, ddof=1)
    st_d_effect = np.std(delta_effects, ddof=1)
    # rho = pearsonr(delta_costs, delta_effects)
    rho = corrcoef(delta_costs, delta_effects)[0, 1]

    variance = wtp ** 2 * st_d_effect ** 2 + st_d_cost ** 2 - 2 * wtp * rho * st_d_effect * st_d_cost

    if np.isnan(variance) or variance < 0:
        raise ValueError(st_d_effect, st_d_cost, rho[0])

    return variance


def get_variance_of_icer(delta_costs, delta_effects, num_bootstrap_samples=1000, rng=None, method='taylor'):
    """
    :param delta_costs: (list) of incremental cost observations
    :param delta_effects: (list) of incremental effect observations
    :param num_bootstrap_samples: (int) number of bootstrap samples
    :param rng: (RandomState) random number generator
    :param method: (str) method to calculate the variance of ICER ('taylor' or 'bootstrap')
    :return: the variance of ICER
    """

    if method == 'taylor':

        mean_d_cost = np.mean(delta_costs)
        mean_d_effect = np.mean(delta_effects)
        var_d_cost = np.var(delta_costs, ddof=1)
        var_d_effect = np.var(delta_effects, ddof=1)
        cov_d_cost_d_effect = np.cov(delta_costs, delta_effects)[0, 1]

        variance = (var_d_cost / mean_d_cost ** 2
                    - 2 * cov_d_cost_d_effect / (mean_d_cost * mean_d_effect)
                    + var_d_effect / mean_d_effect ** 2)

        variance *= (mean_d_cost / mean_d_effect) ** 2

    elif method == 'bootstrap':
        n_obs = len(delta_costs)
        if rng is None:
            rng = np.random.RandomState(1)

        # create bootstrap samples for ICERs
        icer_bootstrap_means = np.zeros(num_bootstrap_samples)
        for i in range(num_bootstrap_samples):
            # because cost and health observations are paired,
            # we sample delta cost and delta health together
            indices = rng.choice(a=range(n_obs),
                                 size=n_obs,
                                 replace=True)
            sampled_delta_costs = delta_costs[indices]
            sampled_delta_effects = delta_effects[indices]

            ave_delta_cost = np.average(sampled_delta_costs)
            ave_delta_effect = np.average(sampled_delta_effects)

            # assert all the means should not be 0
            if ave_delta_effect <= 0:
                warnings.warn(': Mean incremental health is 0 or less for one bootstrap sample, '
                                'ICER is not computable')
                # return np.nan
            else:
                icer_bootstrap_means[i] = ave_delta_cost/ave_delta_effect

        variance = np.var(icer_bootstrap_means, ddof=1) * n_obs

        if np.isnan(variance) or variance < 0:
            raise ValueError('Variance of ICER could not be calculated. Increase the number of Monte Carlo samples.')

    else:
        raise ValueError('Method should be either "taylor" or "bootstrap"')

    return variance


def get_bayesian_ci_for_switch_wtp(
        delta_costs, delta_effects, alpha=0.05,
        num_wtp_thresholds=1000, prior_range=None, rng=None):
    """
    assumes that cost and effect observations are paired
    :param delta_costs: (list) of incremental cost observations
    :param delta_effects: (list) of incremental effect observations
    :param alpha: (double) significance level, a value from [0, 1]
    :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
    :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used.
    :param rng: random number generator to generate empirical bootstrap samples
    :return: bayesian confidence interval in the format of list [l, u] for the estimated WTP where
        the NMB lines of two strategies intersect.
    """

    # mean incremental cost, mean incremental effect, and the estimated switch threshold
    mean_d_cost = np.average(delta_costs)
    mean_d_effect = np.average(delta_effects)
    estimated_switch_wtp = mean_d_cost/mean_d_effect
    n_obs = len(delta_costs)

    # create a new random number generator if one is not provided.
    if rng is None:
        rng = RandomState(seed=1)

    # set the prior range of switch wtp threshold if not provided
    if prior_range is None:
        prior_range = [0, 4 * estimated_switch_wtp]

    # lambda0's at which likelihood should be evaluated
    lambda_0s = np.linspace(start=prior_range[0],
                            stop=prior_range[1],
                            num=num_wtp_thresholds)
    lnl_weights = []
    # lnl of observing NMB = 0 given the sampled lambda_0s
    for lambda_0 in lambda_0s:
        variance = get_variance_of_incremental_nmb(
            wtp=lambda_0,
            delta_costs=delta_costs,
            delta_effects=delta_effects)

        lnl_weight = stat.norm.logpdf(
            x=0,
            loc=lambda_0 * mean_d_effect - mean_d_cost,
            scale=np.sqrt(variance / n_obs))

        if np.isnan(lnl_weight):
            raise ValueError(mean_d_effect, mean_d_cost, variance)

        lnl_weights.append(lnl_weight)

    # convert likelihoods to probabilities
    probs = convert_lnl_to_prob(lnl_weights)

    # resamples lambda_0s based on the probabilities
    sampled_lambda_0s = rng.choice(
        a=lambda_0s,
        size=num_wtp_thresholds,
        replace=True,
        p=probs)

    # report CI
    sum_stat = SummaryStat(data=sampled_lambda_0s)
    interval = sum_stat.get_interval(interval_type='p', alpha=alpha)

    return interval


def get_min_monte_carlo_param_samples(delta_costs, delta_effects, max_wtp, epsilon, alpha=0.05,
                                      num_bootstrap_samples=None, rng=None):
    """
    calculates the number of parameter samples such that the probability that
    the estimated ICER is outside a specified range from the true ICER
    is at most alpha:
        that is: Pr{|estimated ICER - true ICER| >  epsilon} < alpha

    :param delta_costs: (list) of incremental cost observations
    :param delta_effects: (list) of incremental effect observations
    :param max_wtp: (double) the maximum WTP threshold to be considered
    :param epsilon: (double) the acceptable error in estimating ICER
    :param alpha: (double) the acceptable probability that the estimated ICER is
        outside the specified range from the true ICER
    :param num_bootstrap_samples: (int) number of bootstrap samples to characterize the distribution of
        the minimum required  number of parameter samples
    :param rng: (RandomState) random number generator used for bootstrapping
    :return: (int or tuple) minimum required number of parameter samples (N) or
        a tuple of (N, interval) if num_bootstrap_samples is not None, where the interval
        shows the distribution of N from bootstrapping.
    """

    mean_delta_cost = np.average(delta_costs)
    mean_delta_effect = np.average(delta_effects)
    r = mean_delta_cost / mean_delta_effect

    # make sure that ICER is well-defined
    # if mean incremental effect <=0 then ICER is not defined and we return nan
    # if mean incremental effect > 0 and mean incremetal cost <= 0 then
    # ICER will be negative and will be handled by the code
    # to calculate the variance of icer below.
    if mean_delta_effect <= 0:
        if num_bootstrap_samples in (None, 0):
            return math.nan
        else:
            return math.nan, [math.nan, math.nan]

    # if one estimate for min N is needed
    if num_bootstrap_samples in (0, None):

        method = 'icer' # 'nmb'

        if method == 'icer':

            # adjust epsilon
            if r > max_wtp:
                epsilon = max(epsilon, r - max_wtp)
            if r < 0:
                epsilon = -r

            var = get_variance_of_icer(
                delta_costs=delta_costs,
                delta_effects=delta_effects)
            sample_size = var / pow(epsilon, 2) / alpha

        elif method == 'nmb':
            var = get_variance_of_incremental_nmb(
                wtp=min(r, max_wtp),
                delta_costs=delta_costs,
                delta_effects=delta_effects)
            sample_size = var / pow(epsilon * mean_delta_effect, 2) / alpha
        else:
            raise ValueError('method must be either "icer" or "nmb"')

        return round(sample_size) + 1

    else: # if bootstrapping needs to be done

        # set random number generator seed
        if rng is None:
            rng = np.random.RandomState(1)

        bootstrap_ns = np.zeros(num_bootstrap_samples)
        n_obs = len(delta_costs)

        for i in range(num_bootstrap_samples):
            # because cost and health observations are paired,
            # we sample delta cost and delta health together
            indices = rng.choice(a=range(n_obs),
                                 size=n_obs,
                                 replace=True)
            sampled_delta_costs = delta_costs[indices]
            sampled_delta_effects = delta_effects[indices]

            bootstrap_ns[i] = get_min_monte_carlo_param_samples(
                delta_costs=sampled_delta_costs,
                delta_effects=sampled_delta_effects,
                max_wtp=max_wtp,
                epsilon=epsilon,
                alpha=alpha,
                num_bootstrap_samples=None,
                rng=None)

        sum_stat = SummaryStat(data=bootstrap_ns)

        n_full = get_min_monte_carlo_param_samples(
            delta_costs=delta_costs,
            delta_effects=delta_effects,
            max_wtp=max_wtp,
            epsilon=epsilon,
            alpha=alpha)

        interval = sum_stat.get_interval(interval_type='p', alpha=alpha)

        # round up interval values
        new_interval = []
        for a in interval:
            if np.isnan(a):
                new_interval.append(math.nan)
            else:
                new_interval.append(int(a)+1)

        # return the bootstrap interval
        return n_full, new_interval


class Strategy:
    def __init__(self, name, cost_obs, effect_obs, color=None, marker='o', label=None, short_label=None):
        """
        :param name: name of the strategy
        :param cost_obs: list or numpy.array of cost observations
        :param effect_obs: list or numpy.array of effect observations
        :param color: (string) color code
                (https://www.webucator.com/blog/2015/03/python-color-constants-module/)
        :param marker: (string) marker code
                (https://matplotlib.org/3.1.1/api/markers_api.html)
        :param label: (string) label to show on the legend (if None, name is used)
        :param short_label: (string) label to show in the center of the probability clouds
            or on the curves of NMBs (if None, label is used)
        """

        assert color is None or type(color) is str, "color argument should be a string."

        self.idx = 0        # index of the strategy
        self.name = name
        self.color = color
        self.marker = marker

        self.label = name if label is None else label
        self.shortLabel = self.label if short_label is None else short_label

        self.ifDominated = False
        self.switchingWTP = 0
        self.switchingWTPInterval = []

        self.costObs = assert_np_list(cost_obs,
                                      error_message='cost_obs should be a list or a np.array')
        self.dCostObs = None    # (list) cost observations with respect to base
        self.incCostObs = None  # (list) incremental cost observations
        self.cost = None        # summary statistics for cost
        self.dCost = None       # summary statistics for cost with respect to base
        self.incCost = None     # summary statistics for incremental cost

        self.effectObs = assert_np_list(effect_obs,
                                        error_message='effect_obs should be a list or a np.array')
        self.dEffectObs = None      # (list) effect observations with respect to base
        self.incEffectObs = None    # (list) incremental effect observations
        self.effect = None          # summary statistics for effect
        self.dEffect = None         # summary statistics for effect with respect to base
        self.incEffect = None       # summary statistics for incremental effect

        self.cer = None         # cost-effectiveness ratio with respect to base
        self.icer = None        # icer summary statistics
        self.eIncNMB = None     # summary statistics for expected incremental net health benefit
                                # integrated over a wtp distribution

        self.cost = Stat.SummaryStat(name='Cost of '+name, data=self.costObs)
        self.effect = Stat.SummaryStat(name='Effect of '+name, data=self.effectObs)

    def reset(self):
        """ set class attributes that will be calculated later to None """

        self.ifDominated = False
        self.dCostObs = None
        self.incCostObs = None
        self.dCost = None
        self.incCost = None

        self.dEffectObs = None
        self.incEffectObs = None
        self.dEffect = None
        self.incEffect = None

        self.cer = None
        self.icer = None

    def get_cost_err_interval(self, interval_type, alpha=0.05, multiplier=1):
        """
        :param interval_type: (string) 'c' for t-based confidence interval,
                                       'cb' for bootstrap confidence interval, and
                                       'p' for percentile interval
        :param alpha: significance level
        :param multiplier: to multiply the estimate and the interval by the provided value
        :return: list [err_l, err_u] for the lower and upper error length
                of confidence or prediction intervals of cost observations.
                NOTE: [err_l, err_u] = [mean - L, mean + U], where [L, U] is the confidence or prediction interval

        """
        interval = self.cost.get_interval(interval_type, alpha, multiplier)
        return [self.cost.get_mean()*multiplier - interval[0],
                interval[1] - self.cost.get_mean()*multiplier]

    def get_effect_err_interval(self, interval_type, alpha, multiplier=1):
        """
        :param interval_type: (string) 'c' for t-based confidence interval,
                                       'cb' for bootstrap confidence interval, and
                                       'p' for percentile interval
        :param alpha: significance level
        :param multiplier: to multiply the estimate and the interval by the provided value
        :return: list [err_l, err_u] for the lower and upper error length
                of confidence or prediction intervals of effect observations.
                NOTE: [err_l, err_u] = [mean - L, mean + U], where [L, U] is the confidence or prediction interval

        """
        interval = self.effect.get_interval(interval_type, alpha, multiplier)
        return [self.effect.get_mean()*multiplier - interval[0],
                interval[1] - self.effect.get_mean()*multiplier]


class _EconEval:
    """ super class for cost-effective analysis (CEA),  cost-benefit analysis (CBA),
        and budget-constrain health optimization (BCHO)"""

    def __init__(self, strategies, if_paired, health_measure='u',
                 if_reset_strategies=False, wtp_range=None, n_of_wtp_values=200):
        """
        :param strategies: the list of strategies (assumes that the first strategy represents the "base" strategy)
        :param if_paired: set to true to indicate that the strategies are paired
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        :param if_reset_strategies: set to True if the cost and effect with respect to
            base, incremental cost and effect, ICER, and CER of strategies should be recalculated.
        :param wtp_range: ([l, u]) range of willingness-to-pay values over which the NMB analysis should be done
        :param n_of_wtp_values: (int) number of wtp values over which the NMB analysis should be done
        """

        if health_measure not in ['u', 'd']:
            raise ValueError("health_measure can be either 'u' (for utility) or 'd' (for disutility).")

        if strategies is None:
            raise ValueError('A list of strategies must be provided)')
        elif isinstance(strategies, list) is False:
            raise ValueError('strategies should be a list of Strategy objects.')
        elif len(strategies) < 2:
            raise ValueError('strategies should include at least two Strategies.')

        self.strategies = strategies  # list of strategies
        # assign the index of each strategy
        for i, s in enumerate(strategies):
            s.idx = i
            if if_reset_strategies:
                s.reset()

        self._n = len(strategies)  # number of strategies
        self._ifPaired = if_paired  # if cost and effect outcomes are paired across strategies
        self._healthMeasure = health_measure  # utility of disutility
        self._u_or_d = 1 if health_measure == 'u' else -1

        # assign colors to strategies
        self._assign_colors()

        self._strategies_on_frontier = []  # list of strategies on the frontier
        self._ifFrontierIsCalculated = False  # CE frontier is not calculated yet
        self._ifPairwiseCEAsAreCalculated = False
        self._pairwise_ceas = []  # list of list to cea's

        self._incrementalNMBLines = []  # list of incremental NMB curves with respect to the base
        self._acceptabilityCurves = []  # the list of acceptability curves
        self._expectedLossCurves = []  # the list of expected loss curves
        self._evpi = None  # expected value of perfect information

        # wtp values (includes the specified minimum and maximum wtp value)
        self.wtpValues = None
        if wtp_range is not None:
            self.wtpValues = np.linspace(wtp_range[0], wtp_range[1], num=n_of_wtp_values, endpoint=True)

        # index of strategy with the highest expected net-monetary benefit over the wtp range
        self.idxHighestExpNMB = []
        # index of strategy with the lowest expected loss over the wtp range
        self.idxLowestExpLoss = []

        # shift the strategies
        self._find_shifted_strategies()

        # find the cost-effectiveness frontier
        self._find_frontier()

    def _check_if_wtp_range_provided(self):

        if self.wtpValues is None:
            raise ValueError('Willingness-to-pay range is not provided. '
                             'It could be provided when the CEA class is instantiated using '
                             'argument wtp_range=(l, u).')

    def _assign_colors(self):
        """ assigns color to each strategy if colors are not provided """

        # decide about the color of each curve
        rainbow_colors = cm.rainbow(np.linspace(0, 1, self._n))
        for i, s in enumerate(self.strategies):
            if s.color is None:
                s.color = rainbow_colors[i]

    def _find_shifted_strategies(self):
        """ find shifted strategies.
        In calculating the change in effect, it accounts for whether QALY or DALY is used.
        """

        # shift all strategies such that the base strategy (first in the list) lies on the origin
        # if observations are paired across strategies
        if self._ifPaired:

            for i, s in enumerate(self.strategies):

                s.dCostObs = s.costObs - self.strategies[0].costObs
                s.dCost = Stat.DifferenceStatPaired(name='Cost with respect to base',
                                                    x=s.costObs,
                                                    y_ref=self.strategies[0].costObs)
                # if health measure is utility
                if self._healthMeasure == 'u':
                    s.dEffectObs = s.effectObs - self.strategies[0].effectObs
                    s.dEffect = Stat.DifferenceStatPaired(name='Effect with respect to base',
                                                          x=s.effectObs,
                                                          y_ref=self.strategies[0].effectObs)

                else:  # if health measure is disutility
                    s.dEffectObs = self.strategies[0].effectObs - s.effectObs
                    s.dEffect = Stat.DifferenceStatPaired(name='Effect with respect to base',
                                                          x=self.strategies[0].effectObs,
                                                          y_ref=s.effectObs)

                # cost-effectiveness ratio of non-base strategies
                if i > 0:
                    s.cer = ICERPaired(name='Cost-effectiveness ratio of ' + s.name,
                                       costs_new=s.costObs,
                                       effects_new=s.effectObs,
                                       costs_base=self.strategies[0].costObs,
                                       effects_base=self.strategies[0].effectObs,
                                       health_measure=self._healthMeasure)

        else:  # if not paired
            # get average cost and effect of the base strategy
            base_ave_cost = self.strategies[0].cost.get_mean()
            base_ave_effect = self.strategies[0].effect.get_mean()

            for i, s in enumerate(self.strategies):
                s.dCostObs = s.costObs - base_ave_cost
                s.dCost = Stat.DifferenceStatIndp(name='Cost with respect to base',
                                                  x=s.costObs,
                                                  y_ref=self.strategies[0].costObs)
                if self._healthMeasure == 'u':
                    s.dEffectObs = s.effectObs - base_ave_effect
                    s.dEffect = Stat.DifferenceStatIndp(name='Effect with respect to base',
                                                        x=s.effectObs,
                                                        y_ref=self.strategies[0].effectObs)

                else:  # if health measure is disutility
                    s.dEffectObs = base_ave_effect - s.effectObs
                    s.dEffect = Stat.DifferenceStatIndp(name='Effect with respect to base',
                                                        x=self.strategies[0].effectObs,
                                                        y_ref=s.effectObs)

                # cost-effectiveness ratio of non-base strategies
                if i > 0:
                    s.cer = ICERIndp(name='Cost-effectiveness ratio of ' + s.name,
                                     costs_new=s.costObs,
                                     effects_new=s.effectObs,
                                     costs_base=self.strategies[0].costObs,
                                     effects_base=self.strategies[0].effectObs,
                                     health_measure=self._healthMeasure)

    def _find_frontier(self):

        # apply criteria 1 (strict dominance)
        # if a strategy i yields less health than strategy j but costs more, it is dominated
        # sort by effect with respect to base
        self.strategies.sort(key=get_d_effect)
        for i in range(self._n):
            for j in range(i+1, self._n):
                if self.strategies[i].dCost.get_mean() >= self.strategies[j].dCost.get_mean():
                    self.strategies[i].ifDominated = True
                    break

        # select all non-dominated strategies
        select_strategies = [s for s in self.strategies if not s.ifDominated]

        # apply criteria 1 (strict dominance)
        # if a strategy i costs more than strategy j but yields less health, it is dominated
        # sort strategies by cost with respect to the base
        select_strategies.sort(key=get_d_cost, reverse=True)
        for i in range(len(select_strategies)):
            for j in range(i + 1, len(select_strategies)):
                if select_strategies[i].dEffect.get_mean() <= select_strategies[j].dEffect.get_mean():
                    select_strategies[i].ifDominated = True
                    break

        # apply criteria 2 (weak dominance)
        # select all non-dominated strategies
        select_strategies = [s for s in self.strategies if not s.ifDominated]

        for i in range(len(select_strategies)):
            for j in range(i+1, len(select_strategies)):
                # cost and effect of strategy i
                d_cost_i = select_strategies[i].dCost.get_mean()
                d_effect_i = select_strategies[i].dEffect.get_mean()
                # cost and effect of strategy j
                d_cost_j = select_strategies[j].dCost.get_mean()
                d_effect_j = select_strategies[j].dEffect.get_mean()
                # vector connecting strategy i to j
                v_i_to_j = np.array([d_effect_j - d_effect_i, d_cost_j - d_cost_i])

                # find strategies with dEffect between i and j
                s_between_i_and_j = []
                for s in select_strategies:
                    if d_effect_i < s.dEffect.get_mean() < d_effect_j:
                        s_between_i_and_j.append(s)

                # if the dEffect of no strategy is between the effects of strategies i and j
                if len(s_between_i_and_j) == 0:
                    continue  # to the next j
                else:

                    for inner_s in s_between_i_and_j:
                        # vector from i to inner_s
                        v_i_to_inner = np.array([inner_s.dEffect.get_mean() - d_effect_i,
                                                 inner_s.dCost.get_mean() - d_cost_i])

                        # cross products of vector i to j and the vectors i to the inner point
                        cross_product = v_i_to_j[0] * v_i_to_inner[1] - v_i_to_j[1] * v_i_to_inner[0]

                        # if cross_product > 0 the point is above the line
                        # (because the point are sorted vertically)
                        # ref: How to tell whether a point is to the right or left side of a line
                        # https://stackoverflow.com/questions/1560492
                        if cross_product > 0:
                            inner_s.ifDominated = True

        # sort strategies by effect with respect to the base
        self.strategies.sort(key=get_d_effect)

        # find strategies on the frontier
        self._strategies_on_frontier = [s for s in self.strategies if not s.ifDominated]

        # sort back
        self.strategies.sort(key=get_index)

        # frontier is calculated
        self._ifFrontierIsCalculated = True

        # calculate the incremental outcomes
        self._calculate_incremental_outcomes()

    def _calculate_incremental_outcomes(self):

        if self._ifPaired:

            for i, s in enumerate(self._strategies_on_frontier):
                if i > 0:
                    s_before = self._strategies_on_frontier[i-1]

                    s.incCostObs = s.costObs - s_before.costObs
                    s.incCost = Stat.DifferenceStatPaired(name='Incremental cost',
                                                          x=s.costObs,
                                                          y_ref=s_before.costObs)
                    # if health measure is utility
                    if self._healthMeasure == 'u':
                        s.incEffectObs = s.effectObs - self._strategies_on_frontier[i-1].effectObs
                        s.incEffect = Stat.DifferenceStatPaired(name='Effect with respect to base',
                                                                x=s.effectObs,
                                                                y_ref=s_before.effectObs)

                    else:  # if health measure is disutility
                        s.incEffectObs = self._strategies_on_frontier[i-1].effectObs - s.effectObs
                        s.incEffect = Stat.DifferenceStatPaired(name='Effect with respect to base',
                                                                x=s_before.effectObs,
                                                                y_ref=s.effectObs)
                    # ICER
                    s.icer = ICERPaired(name='ICER of {} relative to {}'.format(s.name, s_before.name),
                                        costs_new=s.costObs,
                                        effects_new=s.effectObs,
                                        costs_base=s_before.costObs,
                                        effects_base=s_before.effectObs,
                                        health_measure=self._healthMeasure)

        else:  # if not paired

            for i, s in enumerate(self._strategies_on_frontier):

                if i > 0:
                    s_before = self._strategies_on_frontier[i - 1]

                    # get average cost and effect of the strategy i - 1
                    ave_cost_i_1 =s_before.cost.get_mean()
                    ave_effect_i_1 = s_before.effect.get_mean()

                    s.incCostObs = s.costObs - ave_cost_i_1
                    s.incCost = Stat.DifferenceStatIndp(name='Cost with respect to base',
                                                        x=s.costObs,
                                                        y_ref=s_before.costObs)
                    if self._healthMeasure == 'u':
                        s.incEffectObs = s.effectObs - ave_effect_i_1
                        s.incEffect = Stat.DifferenceStatIndp(name='Effect with respect to base',
                                                              x=s.effectObs,
                                                              y_ref=s_before.effectObs)

                    else:  # if health measure is disutility
                        s.incEffectObs = ave_effect_i_1 - s.effectObs
                        s.incEffect = Stat.DifferenceStatIndp(name='Effect with respect to base',
                                                              x=s_before.effectObs,
                                                              y_ref=s.effectObs)

                    # ICER
                    s.icer = ICERIndp(name='ICER of {} relative to {}'.format(s.name, s_before.name),
                                      costs_new=s.costObs,
                                      effects_new=s.effectObs,
                                      costs_base=s_before.costObs,
                                      effects_base=s_before.effectObs,
                                      health_measure=self._healthMeasure)

    def _create_pairwise_ceas(self):
        """
        creates a list of list for pairwise cost-effectiveness analysis
        For example for strategies ['Base', 'A', 'B']:
        [
            ['Base wr Base',    'A wr Base',    'B wr Base'],
            ['Base wr A',       'A wr A',       'B wr A'],
            ['B wr B',          'A wr B',       'B wr B'],
        ]
        """

        # create CEA's for all pairs
        self._pairwise_ceas = []
        for s_base in self.strategies:
            list_ceas = []
            for s_new in self.strategies:#[1:]:

                # if the base and the new strategies are the same
                if s_base.name == s_new.name:
                    list_ceas.append(None)
                else:
                    list_ceas.append(CEA(strategies=[s_base, s_new],
                                         if_paired=self._ifPaired,
                                         health_measure=self._healthMeasure,
                                         if_reset_strategies=True)
                                     )
            self._pairwise_ceas.append(list_ceas)

        self._ifPairwiseCEAsAreCalculated = True

        # since the relative performance of strategies
        # (relative costs and relative effects) have changed.
        self._ifFrontierIsCalculated = False

    def _build_incremental_nmb_curves(self, interval_type='n'):
        """
        prepares the information needed to plot the incremental net-monetary benefit lines
        with respect to the first strategy (base)
        :param interval_type: (string) 'n' for no interval,
                                       'c' for confidence interval,
                                       'p' for percentile interval):
        """

        self._check_if_wtp_range_provided()

        self._incrementalNMBLines = []  # list of incremental NMB curves

        # create the NMB curves
        for s in self.strategies:

            if self._ifPaired:
                # create a paired NMB object
                incremental_nmb = IncrementalNMBPaired(name=s.name,
                                                       costs_new=s.costObs,
                                                       effects_new=s.effectObs,
                                                       costs_base=self.strategies[0].costObs,
                                                       effects_base=self.strategies[0].effectObs,
                                                       health_measure=self._healthMeasure)

            else:
                # create an independent NMB object
                incremental_nmb = IncrementalNMBIndp(name=s.name,
                                                     costs_new=s.costObs,
                                                     effects_new=s.effectObs,
                                                     costs_base=self.strategies[0].costObs,
                                                     effects_base=self.strategies[0].effectObs,
                                                     health_measure=self._healthMeasure)

            # make a NMB curve
            self._incrementalNMBLines.append(INMBCurve(label=s.label,
                                                       short_label=s.shortLabel,
                                                       color=s.color,
                                                       wtp_values=self.wtpValues,
                                                       inmb_stat=incremental_nmb,
                                                       interval_type=interval_type)
                                             )

        self.idxHighestExpNMB = update_curves_with_highest_values(
            wtp_values=self.wtpValues, curves=self._incrementalNMBLines)

    def _build_acceptability_curves(self, normal_approximation=False):
        """
        prepares the information needed to plot the cost-effectiveness acceptability curves
        :param normal_approximation: (bool) set to True to use normal distributions to approximate the
            acceptability curves (assumes that all cost and effect estimates are independent across strategies)
        """

        self._check_if_wtp_range_provided()

        if not self._ifPaired:
            raise ValueError('Calculating the acceptability curves when outcomes are not paired'
                             'across strategies is not implemented.')

        # initialize acceptability curves
        self._acceptabilityCurves = []
        for s in self.strategies:
            self._acceptabilityCurves.append(
                AcceptabilityCurve(label=s.label,
                                   short_label=s.shortLabel,
                                   color=s.color))

        n_obs = len(self.strategies[0].costObs)

        # if approximation is used
        if normal_approximation:
            # find the mean and standard deviation of all strategies
            # with respect to the base strategy
            d_cost_means = []
            d_cost_st_devs = []
            d_effect_means = []
            d_effect_st_devs = []
            cov_d_effect_and_d_cost = []
            for s in self.strategies:
                d_cost_means.append(s.dCost.get_mean())
                d_cost_st_devs.append(s.dCost.get_stdev())
                d_effect_means.append(s.dEffect.get_mean())
                d_effect_st_devs.append(s.dEffect.get_stdev())
                corr = corrcoef(s.dEffectObs, s.dCostObs)[0, 1]
                if np.isnan(corr):
                    cov_d_effect_and_d_cost.append(0)
                else:
                    cov_d_effect_and_d_cost.append(corr)

        # for each WTP value, calculate the number of times that
        # each strategy has the highest NMB value
        for w in self.wtpValues:

            # if approximation is used
            if normal_approximation:

                for i in range(self._n):
                    # make a list of means and st_devs of strategies other than i
                    nmb_means_others = []
                    nmb_st_devs_others = []
                    for j in range(self._n):
                        if i != j:
                            # mean and variance of NMB of strategy j
                            mean = w * d_effect_means[j] - d_cost_means[j]
                            variance = pow(w * d_effect_st_devs[j], 2) \
                                       + pow(d_effect_st_devs[j], 2) \
                                       - 2 * w * cov_d_effect_and_d_cost[j]
                            nmb_means_others.append(mean)
                            nmb_st_devs_others.append(np.sqrt(variance))

                    # find the distribution of strategy i
                    nmb_mean_i = w * d_effect_means[i] - d_cost_means[i]
                    nmb_st_dev_i = np.sqrt(
                        pow(w * d_effect_st_devs[i], 2) \
                        + pow(d_effect_st_devs[i], 2) \
                        - 2 * w * cov_d_effect_and_d_cost[i]
                    )

                    # calculate the probability that i has the highest NMB
                    prob_i_max = get_prob_x_greater_than_ys(
                        x_mean=nmb_mean_i, x_st_dev=nmb_st_dev_i,
                        y_means=nmb_means_others, y_st_devs=nmb_st_devs_others)

                    self._acceptabilityCurves[i].xs.append(w)
                    self._acceptabilityCurves[i].ys.append(prob_i_max)

            else:

                # number of times that each strategy is optimal
                count_maximum = np.zeros(self._n)

                for obs_idx in range(n_obs):

                    # find which strategy has the maximum:
                    max_nmb = float('-inf')
                    max_s_i = 0  # index of the optimal strategy for this observation
                    for s_i, s in enumerate(self.strategies):
                        nmb = w * s.dEffectObs[obs_idx] - s.dCostObs[obs_idx]
                        if nmb > max_nmb:
                            max_nmb = nmb
                            max_s_i = s_i

                    count_maximum[max_s_i] += 1

                # calculate probabilities that each strategy has been optimal
                prob_maximum = count_maximum / n_obs

                for i in range(self._n):
                    self._acceptabilityCurves[i].xs.append(w)
                    self._acceptabilityCurves[i].ys.append(prob_maximum[i])

        if len(self.idxHighestExpNMB) == 0:
            self.idxHighestExpNMB = update_curves_with_highest_values(
                wtp_values=self.wtpValues, curves=self._incrementalNMBLines)

        # find the optimal strategy for each wtp value
        for wtp_idx, wtp in enumerate(self.wtpValues):
            opt_idx = self.idxHighestExpNMB[wtp_idx]
            self._acceptabilityCurves[opt_idx].frontierXs.append(wtp)
            self._acceptabilityCurves[opt_idx].frontierYs.append(
                self._acceptabilityCurves[opt_idx].ys[wtp_idx])

        for c in self._acceptabilityCurves:
            c.convert_lists_to_arrays()

    def _build_expected_loss_curves(self):
        """
        prepares the information needed to plot the expected loss curves
        """

        self._check_if_wtp_range_provided()

        if not self._ifPaired:
            raise ValueError('Calculating the expected loss curves when outcomes are not paired'
                             'across strategies is not implemented.')

        # initialize expected loss curves
        self._expectedLossCurves = []
        for s in self.strategies:
            self._expectedLossCurves.append(
                ExpectedLossCurve(label=s.label,
                                  short_label=s.shortLabel,
                                  color=s.color))

        n_obs = len(self.strategies[0].costObs)

        # for each WTP value, calculate the expected loss in NMB for each strategy
        for w_idx, w in enumerate(self.wtpValues):

            mean_max_nmb = 0  # mean of the maximum NMB
            for obs_idx in range(n_obs):

                # find which strategy has the maximum nmb for this observation:
                max_nmb = float('-inf')
                for s_i, s in enumerate(self.strategies):
                    d_effect = (s.effectObs[obs_idx] - self.strategies[0].effectObs[obs_idx]) * self._u_or_d
                    d_cost = s.costObs[obs_idx] - self.strategies[0].costObs[obs_idx]
                    nmb = w * d_effect - d_cost
                    if nmb > max_nmb:
                        max_nmb = nmb

                mean_max_nmb += max_nmb

            # estimate the expected maximum NMB
            mean_max_nmb = mean_max_nmb / n_obs

            # store x and y values for this expected loss in NMB curve
            for s_i in range(self._n):
                self._expectedLossCurves[s_i].xs.append(w)
                self._expectedLossCurves[s_i].ys.append(mean_max_nmb - self._incrementalNMBLines[s_i].ys[w_idx])

        if len(self.idxLowestExpLoss) == 0:
            self.idxLowestExpLoss = update_curves_with_lowest_values(
                wtp_values=self.wtpValues, curves=self._expectedLossCurves)

    def _calculate_evpi_curve(self):
        """ calculates the expected value of perfect information (EVPI) curve """

        self._check_if_wtp_range_provided()

        self._evpi = []
        n_of_sims = len(self.strategies[0].dCostObs)

        # for all budget value
        for wtp in self.wtpValues:

            # find the highest achievable NMB under perfect information
            max_nmbs = []
            for i in range(n_of_sims):
                # find costs and effects of strategies for the ith monte carlo simulation run
                costs = [s.dCostObs[i] for s in self.strategies]
                effects = [s.dEffectObs[i] for s in self.strategies]

                # find the maximum effect
                max_nmb = float('-inf')
                for c, e in zip(costs, effects):
                    nmb = wtp * e - c
                    if nmb > max_nmb:
                        max_nmb = nmb
                max_nmbs.append(max_nmb)

            self._evpi.append(average(max_nmbs))

        # curve
        self._incrementalNMBLines.append(
            EVPI(xs=self.wtpValues, ys=self._evpi, label=Params['evpi.plot.label'], color='k'))


class CEA(_EconEval):
    """ class for cost-effective analysis (CEA) and cost-benefit analysis (CBA) """

    def __init__(self, strategies, if_paired, health_measure='u', if_reset_strategies=False,
                 wtp_range=None, n_of_wtp_values=200):
        """
        :param strategies: the list of strategies (assumes that the first strategy represents the "base" strategy)
        :param if_paired: set to true to indicate that the strategies are paired
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        :param if_reset_strategies: set to True if the cost and effect with respect to
            base, incremental cost and effect, ICER, and CER of strategies should be recalculated.
        :param wtp_range: ([l, u]) range of willingness-to-pay values over which the NMB analysis should be done
        :param n_of_wtp_values: (int) number of wtp values over which the NMB analysis should be done
        """

        _EconEval.__init__(self, strategies=strategies,
                           if_paired=if_paired,
                           health_measure=health_measure,
                           if_reset_strategies=if_reset_strategies,
                           wtp_range=wtp_range,
                           n_of_wtp_values=n_of_wtp_values)

    def export_ce_table(
            self, interval_type='c',  alpha=0.05, ci_method='bootstrap', num_bootstrap_samples=1000,
            rng=None, prior_range=None, num_wtp_thresholds=1000,
            cost_digits=0, effect_digits=2, icer_digits=1,
            cost_multiplier=1, effect_multiplier=1,
            file_name='ce_table.csv', directory=''):
        """
        :param interval_type: (string) the interval type for cost and effect estimates
            (for ICER, we always report confidence interval)
            'n' or None for no interval
            'c' or 'cb' for bootstrap confidence interval, and
            'p' for percentile interval
        :param alpha: significance level, a value from [0, 1]
        :param ci_method: (string) method to calculate confidence interval of ICER ('bootstrap' or 'Bayesian')
        :param num_bootstrap_samples: number of bootstrap samples when 'bootstrap' method is selected
        :param rng: random number generator to generate empirical bootstrap samples
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used
        :param cost_digits: digits to round cost estimates to
        :param effect_digits: digits to round effect estimate to
        :param icer_digits: digits to round ICER estimates to
        :param cost_multiplier: set to 1/1000 or 1/100000 to represent cost in terms of
                thousands or hundred thousands unit
        :param effect_multiplier: set to 1/1000 or 1/100000 to represent effect in terms of
                thousands or hundred thousands unit
        :param file_name: address and file name where the CEA results should be saved to
        :param directory: directory (relative to the current root) where the files should be located
            for example use 'Example' to create and save the csv file under the folder Example
        """

        # find the frontier if not calculated already
        if not self._ifFrontierIsCalculated:
            self._find_frontier()

        table = [['Strategy', 'Cost', 'Effect', 'Incremental Cost', 'Incremental Effect',
                  'ICER (with confidence interval)']]
        # sort strategies in increasing order of cost
        self.strategies.sort(key=get_d_cost)

        for i, s in enumerate(self.strategies):
            row=[]
            # strategy name
            row.append(s.name)
            # strategy cost
            row.append(s.cost.get_formatted_mean_and_interval(interval_type=interval_type,
                                                              alpha=alpha,
                                                              deci=cost_digits,
                                                              form=',',
                                                              multiplier=cost_multiplier))
            # strategy effect
            row.append(s.effect.get_formatted_mean_and_interval(interval_type=interval_type,
                                                                alpha=alpha,
                                                                deci=effect_digits,
                                                                form=',',
                                                                multiplier=effect_multiplier))

            # strategy incremental cost
            if s.incCost is None:
                row.append('-')
            else:
                row.append(s.incCost.get_formatted_mean_and_interval(interval_type=interval_type,
                                                                     alpha=alpha,
                                                                     deci=cost_digits,
                                                                     form=',',
                                                                     multiplier=cost_multiplier))
            # strategy incremental effect
            if s.incEffect is None:
                row.append('-')
            else:
                row.append(s.incEffect.get_formatted_mean_and_interval(interval_type=interval_type,
                                                                       alpha=alpha,
                                                                       deci=effect_digits,
                                                                       form=',',
                                                                       multiplier=effect_multiplier))

            # ICER
            if s.ifDominated:
                row.append('Dominated')
            elif s.icer is not None:
                row.append(s.icer.get_formatted_mean_and_interval(interval_type='c',
                                                                  alpha=alpha,
                                                                  method=ci_method,
                                                                  num_bootstrap_samples=num_bootstrap_samples,
                                                                  rng=rng,
                                                                  prior_range=prior_range,
                                                                  num_wtp_thresholds=num_wtp_thresholds,
                                                                  deci=icer_digits,
                                                                  form=',',
                                                                  multiplier=1))
            else:
                row.append('-')

            table.append(row)

        write_csv(file_name=file_name, directory=directory, rows=table, delimiter=',')

        # sort strategies back
        self.strategies.sort(key=get_index)

    def get_strategies_on_frontier(self):
        """
        :return: strategies on the frontier sorted in the increasing order of effect
        """

        if not self._ifFrontierIsCalculated:
            self._find_frontier()

        return self._strategies_on_frontier

    def get_strategies_not_on_frontier(self):
        """
        :return: strategies not on the frontier
        """

        if not self._ifFrontierIsCalculated:
            self._find_frontier()

        return [s for s in self.strategies if s.ifDominated]

    def get_wtp_switch_thresholds_on_frontier(self, with_confidence_intervals=True, alpha=0.05):
        """
        :param with_confidence_intervals (bool) set to False
            if confidence intervals should not be calculated
        :param alpha: (float) significance level
        :return: (dictionary) of strategies on the frontier with the estimate of WTP threshold
            at which the strategy becomes the optimal option.
            key: strategy name and value: [wtp threshold, confidence interval]
                or wtp threshold when confidence interval is not requested.
        """

        dic_of_strategies = {}
        for s in self.get_strategies_on_frontier():
            if s.icer is not None:
                if with_confidence_intervals:
                    dic_of_strategies[s.name] = [
                        s.icer.get_ICER(),
                        s.icer.get_CI(alpha=alpha,
                                      method='bootstrap',
                                      num_bootstrap_samples=1000)]
                else:
                    dic_of_strategies[s.name] = s.icer.get_ICER()

        return dic_of_strategies

    def get_min_monte_carlo_parameter_samples(
            self, max_wtp, epsilon, alpha=0.05, num_bootstrap_samples=1000, rng=None,
            comparison_type='frontier'):
        """
        :param max_wtp: (double) the highest willingness-to-pay (WTP) value that is deemed reasonable to consider
        :param epsilon: (double) the acceptable error in estimating ICER
        :param alpha: (double) the acceptable probability that the estimated ICER is outside the specified range
        :param num_bootstrap_samples: (int) number of bootstrap samples to characterize
            the distribution of estimated Ns. If None, only the estimated N is returned.
        :param rng: (RandomState) random number generator used for bootstrapping
        :param comparison_type: (string) 'frontier' to compare strategies on the frontier or
            'pairwise' to compare all pairwise combinations of strategies
                ('pairwise is more conservative and may require a substantially more samples)
        :return: (int) the minimum Monte Carlo samples from parameter distributions
        """

        # find the minimum required number of Monte Carlo samples from parameter distributions
        max_n = 0
        max_interval = None

        if comparison_type == 'frontier':

            # find strategies on the frontier
            if not self._ifFrontierIsCalculated:
                self._find_frontier()
            strategies_on_frontier = self.get_strategies_on_frontier()

            # go over all strategies on the frontier
            for i in range(len(strategies_on_frontier) - 1):

                results = get_min_monte_carlo_param_samples(
                    delta_costs=strategies_on_frontier[i + 1].costObs - strategies_on_frontier[i].costObs,
                    delta_effects=(strategies_on_frontier[i + 1].effectObs - strategies_on_frontier[
                        i].effectObs) * self._u_or_d,
                    max_wtp=max_wtp,
                    epsilon=epsilon,
                    alpha=alpha,
                    num_bootstrap_samples=num_bootstrap_samples,
                    rng=rng)

                if num_bootstrap_samples is None:
                    n = results
                    interval = None
                else:
                    n, interval = results

                if not np.isnan(n):
                    if n > max_n:
                        max_n = n
                        max_interval = interval

        elif comparison_type == 'pairwise':

            # go over all pairwise comparisons between strategies
            for i in range(self._n):
                for j in range(self._n):
                    if i != j:
                        s_i = self.strategies[i]
                        s_j = self.strategies[j]

                        results = get_min_monte_carlo_param_samples(
                            delta_costs=s_j.costObs - s_i.costObs,
                            delta_effects=(s_j.effectObs - s_i.effectObs) * self._u_or_d,
                            max_wtp=max_wtp,
                            epsilon=epsilon,
                            alpha=alpha,
                            num_bootstrap_samples=num_bootstrap_samples,
                            rng=rng)

                        if num_bootstrap_samples is None:
                            n = results
                            interval = None
                        else:
                            n, interval = results

                        if not np.isnan(n):
                            if n > max_n:
                                max_n = n
                                max_interval = interval

        else:
            raise ValueError('comparison_type should be either "frontier" or "pairwise"')

        if num_bootstrap_samples is None:
            return max_n
        else:
            return max_n, max_interval

    def get_dict_min_monte_carlo_parameter_samples(
            self, max_wtp, epsilons, alphas, num_bootstrap_samples=None, rng=None):
        """
        :param max_wtp: (double) the highest willingness-to-pay (WTP) value that is deemed reasonable to consider
        :param epsilons: (list) the acceptable errors in estimating ICER
        :param alphas: (list) the acceptable probabilities that the estimated ICER is
            outside the specified range from the true ICER
        :param num_bootstrap_samples: (int) number of bootstrap samples to characterize the distribution of
            the minimum required  number of parameter samples
        :param rng: (RandomState) random number generator used for bootstrapping
        :return: (dictionary) of minimum Monte Carlo samples needed to achieve the desired statistical power
            first key is power values and the second key is error tolerance
        """

        if not isinstance(alphas, list):
            alphas = [alphas]
        if not isinstance(epsilons, list):
            epsilons = [epsilons]

        dic_of_ns = {}
        for alpha in alphas:
            dic_of_ns[alpha] = {}
            for epsilon in epsilons:
                dic_of_ns[alpha][epsilon] = self.get_min_monte_carlo_parameter_samples(
                    max_wtp=max_wtp, epsilon=epsilon, alpha=alpha,
                    num_bootstrap_samples=num_bootstrap_samples, rng=rng)

        return dic_of_ns

    def get_dCost_dEffect_cer(self,
                              interval_type='n',
                              alpha=0.05,
                              cost_digits=0, effect_digits=2, icer_digits=1,
                              cost_multiplier=1, effect_multiplier=1):
        """
        :param interval_type: (string) 'n' for no interval,
                                       'c' for confidence interval,
                                       'p' for percentile interval
        :param alpha: significance level
        :param cost_digits: digits to round cost estimates to
        :param effect_digits: digits to round effect estimate to
        :param icer_digits: digits to round ICER estimates to
        :param cost_multiplier: set to 1/1000 or 1/100,000 to represent cost in terms of
                thousands or a hundred thousands unit
        :param effect_multiplier: set to 1/1000 or 1/100,000 to represent effect in terms of
                thousands or a hundred thousands unit
        :return: a dictionary of additional cost, additional effect, and cost-effectiveness ratio for
                all strategies with respect to the Base strategy
        """

        dictionary_results = {}

        for s in [s for s in self.strategies if s.idx > 0]:

            d_cost_text = s.dCost.get_formatted_mean_and_interval(interval_type=interval_type,
                                                                  alpha=alpha,
                                                                  deci=cost_digits,
                                                                  form=',',
                                                                  multiplier=cost_multiplier)
            d_effect_text = s.dEffect.get_formatted_mean_and_interval(interval_type=interval_type,
                                                                      alpha=alpha,
                                                                      deci=effect_digits,
                                                                      form=',',
                                                                      multiplier=effect_multiplier)
            cer_text = s.cer.get_formatted_mean_and_interval(interval_type=interval_type,
                                                             alpha=alpha,
                                                             deci=icer_digits,
                                                             form=',',
                                                             multiplier=1)
            # add to the dictionary
            dictionary_results[s.name] = [d_cost_text, d_effect_text, cer_text]

        return dictionary_results

    def add_ce_plane_to_ax(self, ax,
                           title=None, x_range=None, y_range=None,
                           add_clouds=True, show_legend=True, show_frontier=True,
                           center_s=50, cloud_s=10, transparency=0.1,
                           cost_multiplier=1, effect_multiplier=1,
                           cost_decimals=None, effect_decimals=None,
                           interval_type='c', significance_level=0.05, interval_transparency=0.5,
                           legend_loc_code=2, grid_info=None):
        """
        adds a cost-effectiveness plane to the provided ax
        :param ax: axis
        :param title: (string) title of the panel
        :param x_range: (tuple) range of x-axis
        :param y_range: (tuple) range of y-axis
        :param add_clouds: (bool) if to add the probability clouds
        :param show_legend: (bool) if to show the legend
        :param show_frontier: (bool) if to show the cost-effectiveness frontier
        :param center_s: (float) the size of the dot showing (x,y) of a strategy
        :param cloud_s: (float) the size of dots building the probability clouds
        :param transparency: (float) the transparency of dots building the probability clouds
        :param cost_multiplier: (float) to multiply the cost values
        :param effect_multiplier: (float) to multiply the effect values
        :param cost_decimals: (int) to round the labels of cost axis
        :param effect_decimals: (int) to round the labels of the effect axis
        :param interval_type: (string) None to not display the intervals,
                                       'c' for t-based confidence interval,
                                       'cb' for bootstrap confidence interval, and
                                       'p' for percentile interval
        :param significance_level: (float) significance level for the interval
        :param interval_transparency: (float) the transparency of intervals
        :param legend_loc_code: (int) legend location code
            https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
        :param grid_info: (None or 'default', or tuple of tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        """

        # find the frontier (x, y)'s
        frontier_d_effect = []
        frontier_d_costs = []
        for s in self.get_strategies_on_frontier():
            frontier_d_effect.append(s.dEffect.get_mean()*effect_multiplier)
            frontier_d_costs.append(s.dCost.get_mean()*cost_multiplier)

        # add all strategies
        for s in self.strategies:
            # the mean change in effect and cost
            ax.scatter(s.dEffect.get_mean()*effect_multiplier, s.dCost.get_mean()*cost_multiplier,
                       color=s.color,  # color
                       alpha=1,  # transparency
                       marker=s.marker,  # markers
                       s=center_s,  # marker size
                       label=s.label,  # label to show in the legend
                       zorder=2,
                       edgecolors=Params['ce.cloud.edgecolors']
                       )
            # add error bars
            if interval_type is not None:
                x_mean = s.dEffect.get_mean()*effect_multiplier
                y_mean = s.dCost.get_mean()*cost_multiplier

                x_interval = s.dEffect.get_interval(
                    interval_type=interval_type, alpha=significance_level, multiplier=effect_multiplier)
                y_interval = s.dCost.get_interval(
                    interval_type=interval_type, alpha=significance_level, multiplier=cost_multiplier)

                ax.errorbar(x_mean, y_mean,
                            xerr=[[x_mean-x_interval[0]], [x_interval[1]-x_mean]],
                            yerr=[[y_mean-y_interval[0]], [y_interval[1]-y_mean]],
                            fmt='none', color=s.color, linewidth=1, alpha=interval_transparency)

        # add the frontier line
        if show_frontier and len(self.get_strategies_on_frontier()) > 1:
            ax.plot(frontier_d_effect, frontier_d_costs,
                    color=Params['ce.frontier.color'],  # color
                    alpha=Params['ce.frontier.transparency'],  # transparency
                    linewidth=Params['ceac.line_width'],  # line width
                    zorder=3,
                    label='Frontier',  # label to show in the legend
                    )

        if show_legend:
            ax.legend(fontsize=Params['plot.legend.fontsize'], loc=legend_loc_code)

        # and the clouds
        if add_clouds:
            # add all strategies
            for s in self.strategies:
                ax.scatter(s.dEffectObs * effect_multiplier, s.dCostObs * cost_multiplier,
                           color=s.color,  # color of dots
                           marker=s.marker, # marker
                           alpha=transparency,  # transparency of dots
                           s=cloud_s,  # size of dots
                           zorder=1
                           )

        ax.set_xlim(x_range)  # x-axis range
        ax.set_ylim(y_range)  # y-axis range

        # format x-axis
        if effect_decimals is not None:
            vals_x = ax.get_xticks()
            ax.set_xticks(vals_x)
            ax.set_xticklabels(['{:,.{prec}f}'.format(x, prec=effect_decimals) for x in vals_x])

        # format y-axis
        if cost_decimals is not None:
            vals_y = ax.get_yticks()
            ax.set_yticks(vals_y)
            ax.set_yticklabels(['{:,.{prec}f}'.format(x, prec=cost_decimals) for x in vals_y])

        ax.set_xlim(x_range)  # x-axis range
        ax.set_ylim(y_range)  # y-axis range

        ax.axhline(y=0, c='k', linestyle='--', linewidth=0.5)
        ax.axvline(x=0, c='k', linestyle='--', linewidth=0.5)

        ax.set_title(title)

        # grid
        add_grids(ax=ax, grid_info=grid_info)

    def plot_ce_plane(self,
                      title='Cost-Effectiveness Analysis',
                      x_label='Additional Health',
                      y_label='Additional Cost',
                      x_range=None, y_range=None,
                      add_clouds=False, fig_size=(5, 5),
                      show_legend=True, show_frontier=True,
                      center_s=75, cloud_s=25, transparency=0.1,
                      cost_multiplier=1, effect_multiplier=1,
                      cost_digits=0, effect_digits=1,
                      interval_type='c', significance_level=0.05, interval_transparency=0.5,
                      grid_info=None, file_name=None
                      ):
        ''' plots a cost-effectiveness plane
        :param title: (string) title of the figure
        :param x_label: (string) label of x-axis
        :param y_label: (string) label of y-axis
        :param x_range: (tuple) (minimum value, maximum value) of the y-axis
        :param y_range: (tuple) (minimum value, maximum value) of the y-axis
        :param add_clouds: (boolean) set to True to show the projection clouds
        :param fig_size: (tuple) (width, height) of the figure
        :param show_legend: (boolean) set to True to show the legends
        :param show_frontier: (boolean) set to True to show the frontier
        :param center_s: (float) size of dots that show the mean cost and health of each strategy
        :param cloud_s: (float) size of dots that form the clouds
        :param transparency: (float between 0 and 1) transparency of dots that form the clouds
        :param cost_multiplier: (float) set to 1/1000 or 1/100000 to represent cost in terms of
                thousands or hundred thousands unit
        :param effect_multiplier: (float) set to 1/1000 or 1/100000 to represent effect in terms of
                thousands or hundred thousands unit
        :param cost_digits: (int) number of digits to round cost labels to
        :param effect_digits: (int) number of digits to round effect labels to
        :param interval_type: (string) None to not display the intervals,
                               'c' for t-based confidence interval,
                               'cb' for bootstrap confidence interval, and
                               'p' for percentile interval
        :param significance_level: (float) significance level for the interval
        :param interval_transparency: (float) the transparency of intervals
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        :param file_name: (string) file name to save the figure as
        :return:
        '''

        fig, ax = plt.subplots(figsize=fig_size)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        # add the cost-effectiveness plane
        self.add_ce_plane_to_ax(ax=ax,
                                title=title, x_range=x_range, y_range=y_range,
                                add_clouds=add_clouds,
                                show_legend=show_legend, show_frontier=show_frontier,
                                center_s=center_s, cloud_s=cloud_s, transparency=transparency,
                                cost_multiplier=cost_multiplier, effect_multiplier=effect_multiplier,
                                cost_decimals=cost_digits, effect_decimals=effect_digits,
                                interval_type=interval_type, significance_level=significance_level,
                                interval_transparency=interval_transparency, grid_info=grid_info)

        fig.tight_layout()
        output_figure(plt=fig, file_name=file_name)

    def export_pairwise_cea(self, interval_type='n',
                            alpha=0.05,
                            cost_digits=0, effect_digits=2, icer_digits=1,
                            cost_multiplier=1, effect_multiplier=1,
                            directory='Pairwise_CEA'):
        """
        :param interval_type: (string) 'n' for no interval,
                                       'c' for confidence interval,
                                       'p' for percentile interval
        :param alpha: significance level
        :param cost_digits: digits to round cost estimates to
        :param effect_digits: digits to round effect estimate to
        :param icer_digits: digits to round ICER estimates to
        :param cost_multiplier: set to 1/1000 or 1/100,000 to represent cost in terms of
                thousands or a hundred thousands unit
        :param effect_multiplier: set to 1/1000 or 1/100,000 to represent effect in terms of
                thousands or a hundred thousands unit
        :param directory: directory (relative to the current root) where the files should be located
            for example use 'Example' to create and save the csv file under the folder Example
        """

        # create the pair-wise cost-effectiveness analyses
        if not self._ifPairwiseCEAsAreCalculated:
            self._create_pairwise_ceas()

        # save the CEA tables
        for row_of_ceas in self._pairwise_ceas:
            for cea in row_of_ceas:
                if cea is not None:
                    name = cea.strategies[1].name + ' to ' + cea.strategies[0].name
                    cea.export_ce_table(interval_type=interval_type,
                                        alpha=alpha,
                                        cost_digits=cost_digits,
                                        effect_digits=effect_digits,
                                        icer_digits=icer_digits,
                                        cost_multiplier=cost_multiplier,
                                        effect_multiplier=effect_multiplier,
                                        file_name=name+'.csv',
                                        directory=directory)

    def plot_pairwise_ceas(self,
                           figure_size=None, font_size=6,
                           show_subplot_labels=False,
                           effect_label='', cost_label='',
                           center_s=50, cloud_s=25, transparency=0.2,
                           x_range=None, y_range=None,
                           cost_multiplier=1, effect_multiplier=1,
                           column_titles=None, row_titles=None,
                           file_name='pairwise_CEA.png'):

        # identify which CEA is valid
        # (i.e. comparing strategies that are on the frontier)
        # valid comparisons are marked with '*'
        valid_comparison = []
        for i in range(self._n):
            valid_comparison.append(['']*self._n)
        on_frontier = self.get_strategies_on_frontier()
        for idx in range(len(on_frontier)-1):
            i = on_frontier[idx].idx
            j = on_frontier[idx+1].idx
            valid_comparison[i][j] = '*'

        # set default properties of the figure
        plt.rc('font', size=font_size) # fontsize of texts
        plt.rc('axes', titlesize=font_size)  # fontsize of the figure title
        plt.rc('axes', titleweight='semibold')  # fontweight of the figure title

        # plot each panel
        f, axarr = plt.subplots(nrows=self._n, ncols=self._n,
                                sharex=True, sharey=True, figsize=figure_size)

        Y_LABEL_COORD_X = -0.05     # increase to move the A-B-C labels to right
        abc_idx = 0
        for i in range(self._n):
            for j in range(self._n):
                # get the current axis
                ax = axarr[i, j]

                # add the A-B-C label if needed
                if show_subplot_labels:
                    ax.text(Y_LABEL_COORD_X - 0.05, 1.05,
                            string.ascii_uppercase[abc_idx] + ')',
                            transform=ax.transAxes,
                            size=font_size + 1, weight='bold')

                # add titles for the figures_national in the first row
                if i == 0:
                    if column_titles is None:
                        ax.set_title(self.strategies[j].name)
                    else:
                        ax.set_title(column_titles[j])

                # add y_labels for the figures_national in the first column
                if j == 0:
                    if row_titles is None:
                        ax.set_ylabel(self.strategies[i].name, fontweight='bold')
                    else:
                        ax.set_ylabel(row_titles[i], fontweight='bold')

                # specify ranges of x- and y-axis
                if x_range is not None:
                    ax.set_xlim(x_range)
                if y_range is not None:
                    ax.set_ylim(y_range)

                # CEA of these 2 strategies
                cea = CEA(strategies=[self.strategies[i], self.strategies[j]],
                          if_paired=self._ifPaired,
                          health_measure=self._healthMeasure,
                          if_reset_strategies=True)

                # add the CE figure to this axis
                cea.add_ce_plane_to_ax(ax=ax, show_legend=False,
                                       center_s=center_s,
                                       cloud_s=cloud_s,
                                       transparency=transparency,
                                       cost_multiplier=cost_multiplier,
                                       effect_multiplier=effect_multiplier)

                # add ICER to the figure
                # could be 'Dominated', 'Cost-Saving' or 'estimated ICER'
                text = ''
                if i != j and cea.strategies[1].ifDominated:
                    text = 'Dominated'
                elif cea.strategies[1].dCost.get_mean() < 0 and cea.strategies[1].dEffect.get_mean() > 0:
                    text = 'Cost-Saving' + valid_comparison[i][j]
                elif cea.strategies[1].icer is not None:
                    text = F.format_number(cea.strategies[1].icer.get_ICER(), deci=1, format='$') + valid_comparison[i][j]
                # add the text of the ICER to the figure
                ax.text(0.95, 0.95, text, transform=ax.transAxes, fontsize=6,
                        va='top', ha='right')

                abc_idx += 1

        # add the common effect and cost labels
        f.text(0.55, 0, effect_label, ha='center', va='center', fontweight='bold')
        f.text(0.99, 0.5, cost_label, va='center', rotation=-90, fontweight='bold')

        # f.show()
        f.savefig(file_name, bbox_inches='tight', dpi=300)

        # since the relative performance of strategies 
        # (relative costs and relative effects) have changed.
        self._ifFrontierIsCalculated = False

    def export_minimum_monte_carlo_samples(
            self, max_wtp, epsilons, alphas, file_name):
        """
        :param max_wtp: (double) the highest willingness-to-pay (WTP) value that is deemed reasonable to consider
        :param epsilons: (list) of error tolerances
        :param alphas: (list) of significance levels
        :param file_name: (string) the file name to save the results as
        :return: (dictionary) of minimum Monte Carlo samples needed to achieve the desired statistical power
            first key is power values and the second key is error tolerance
        """

        if not isinstance(alphas, list):
            alphas = [alphas]
        if not isinstance(epsilons, list):
            epsilons = [epsilons]

        dic_of_ns = self.get_dict_min_monte_carlo_parameter_samples(
            max_wtp=max_wtp, epsilons=epsilons, alphas=alphas)

        rows = [['Alpha/Epsilon']]
        for epsilon in epsilons:
            rows[0].append(epsilon)

        for alpha in alphas:
            rows.append([alpha])
            for epsilon in epsilons:
                rows[-1].append(dic_of_ns[alpha][epsilon])

        write_csv(rows=rows, file_name=file_name)

    def plot_min_monte_carlo_parameter_samples(
            self, max_wtp, epsilons, alphas,
            x_range=None, y_range=None, x_multiplier=1, y_multiplier=1,
            x_label=r'Acceptable Error in Estimating ICER ($\epsilon$)',
            y_label='Required Number of Parameter Samples',
            num_bootstrap_samples=None, rng=None,
            fig_size=(4, 4), file_name=None):
        """ plots the minimum number of Monte Carlo parameter samples needed to achieve the desired accuracy
        :param max_wtp: (double) the highest willingness-to-pay (WTP) value that is deemed reasonable to consider
        :param epsilons: (list) of epsilon values (the acceptable error in estimating ICER)
        :param alphas: (list) of significance levels (the acceptable probability that the estimated ICER is
        outside the specified range from the true ICER)
        :param x_range: (list) of x-axis range
        :param y_range: (list) of y-axis range
        :param x_multiplier: (double) multiplier for x-axis values
        :param y_multiplier: (double) multiplier for y-axis values
        :param x_label: (string) x-axis label
        :param y_label: (string) y-axis label
        :param fig_size: (tuple) figure size
        :param file_name: (string) file name to save the figure as
        """

        dict_of_ns = self.get_dict_min_monte_carlo_parameter_samples(
            max_wtp=max_wtp, epsilons=epsilons, alphas=alphas,
            num_bootstrap_samples=num_bootstrap_samples, rng=rng)

        f, ax = plt.subplots(figsize=fig_size)
        add_min_monte_carlo_samples_to_ax(
            ax=ax, dict_of_ns=dict_of_ns, epsilons=epsilons,
            x_range=x_range, y_range=y_range, x_multiplier=x_multiplier)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        f.tight_layout()

        output_figure(plt=f, file_name=file_name)

    def plot_incremental_nmb_lines(self,
                                   title='Incremental Net Monetary Benefit',
                                   x_label='Willingness-To-Pay Threshold',
                                   y_label='Incremental Net Monetary Benefit',
                                   show_evpi=False,
                                   y_range=None,
                                   y_axis_multiplier=1.0,
                                   y_axis_decimal=0,
                                   interval_type='c',
                                   delta_wtp=None,
                                   transparency_lines=0.5,
                                   transparency_intervals=0.2,
                                   show_legend=True,
                                   show_labels_on_frontier=False,
                                   grid_info=None,
                                   figure_size=(5, 5),
                                   file_name=None):
        """
        plots the incremental net-monetary benefit of each strategy
                with respect to the base (the first strategy)
        :param wtp_range: (min, max) of WTP values
        :param title: title
        :param x_label: x-axis label
        :param y_label: y-axis label
        :param show_evpi: (bool) if to show EVPI curve
        :param y_range: (list) range of y-axis
        :param y_axis_multiplier: (float) multiplier to scale the y-axis
            (e.g. 0.001 for thousands)
        :param y_axis_decimal: (float) decimal of y_axis numbers
        :param interval_type: (string) 'n' for no interval,
                                       'c' for confidence interval,
                                       'p' for percentile interval
        :param delta_wtp: distance between the labels of WTP values shown on the x-axis
        :param transparency_lines: transparency of net monetary benefit lines (0.0 transparent through 1.0 opaque)
        :param transparency_intervals: transparency of intervals (0.0 transparent through 1.0 opaque)
        :param show_legend: set true to show legend
        :param show_labels_on_frontier: set true to show strategy labels on frontier
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        :param figure_size: (tuple) size of the figure (e.g. (2, 3)
        :param file_name: (string) file name to save the figure as
        """

        # make incremental NMB curves
        self._build_incremental_nmb_curves(interval_type=interval_type)

        if show_evpi:
            self._calculate_evpi_curve()

        # initialize plot
        fig, ax = plt.subplots(figsize=figure_size)

        # add the incremental NMB curves
        add_curves_to_ax(ax=ax, curves=self._incrementalNMBLines,
                         x_range=[self.wtpValues[0], self.wtpValues[-1]],
                         title=title, x_label=x_label,
                         y_label=y_label, y_range=y_range, x_delta=delta_wtp,
                         y_axis_multiplier=y_axis_multiplier,
                         y_axis_format_decimals=None,
                         transparency_lines=transparency_lines,
                         transparency_intervals=transparency_intervals,
                         show_legend=show_legend,
                         show_labels_on_frontier=show_labels_on_frontier, grid_info=grid_info)

        fig.tight_layout()

        fig.tight_layout()
        output_figure(plt=fig, file_name=file_name)

    def plot_expected_loss_curves(self,
                                  title='Expected Loss Curves',
                                  x_label='Willingness-To-Pay Threshold',
                                  y_label='Expected Loss in Net Monetary Benefit',
                                  delta_wtp=None,
                                  y_range=None,
                                  show_legend=True,
                                  legend_font_size_and_loc=None,
                                  legends=None,
                                  y_axis_multiplier=1.0, y_axis_format_decimals=None,
                                  grid_info=None,
                                  file_name=None, fig_size=(5, 5), ):
        """
        plot expected loss curves
        :param title: title
        :param x_label: x-axis label
        :param y_label: y-axis label
        :param delta_wtp: (float) distance between ticks on x-axis
        :param y_range: (tuple) range of y-axis
        :param show_legend: (bool) if to show the legend
        :param legends: (list of strings) texts for legends
        :param legend_font_size_and_loc: (tuple) (font size, location) for the legend
        :param y_axis_multiplier: (float) multiplier for the y-axis
        :param y_axis_format_decimals: (format, int) format and number of decimal places to show on the y-axis
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
           if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        :param fig_size: (tuple) size of the figure (e.g. (2, 3)
        :param file_name: (string) file name to save the figure as
        """

        # initialize plot
        fig, ax = plt.subplots(figsize=fig_size)

        # add the acceptability curves
        self.add_expected_loss_curves_to_ax(
            ax=ax,
            wtp_delta=delta_wtp,
            y_range=y_range,
            show_legend=show_legend,
            legends=legends,
            legend_font_size_and_loc=legend_font_size_and_loc,
            y_axis_multiplier=y_axis_multiplier,
            y_axis_format_decimals=y_axis_format_decimals,
            grid_info=grid_info)

        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        fig.tight_layout()
        output_figure(plt=fig, file_name=file_name)

    def add_inmb_lines_to_ax(self, ax,
                             title='Incremental Net Monetary Benefit',
                             x_label='Willingness-To-Pay Threshold',
                             y_label='Incremental Net Monetary Benefit',
                             show_evpi=False,
                             y_range=None,
                             y_axis_multiplier=1.0,
                             y_axis_format_decimals=None,
                             delta_wtp=None,
                             interval_type='n',
                             show_legend=True,
                             legend_font_size_and_loc=None,
                             show_labels_on_frontier=False,
                             grid_info=None):

        # make incremental NMB curves
        self._build_incremental_nmb_curves(interval_type=interval_type)

        if show_evpi:
            self._calculate_evpi_curve()

        if legend_font_size_and_loc is None:
            legend_font_size_and_loc = (
                Params['plot.legend.fontsize'],
                Params['plot.legend.loc']
            )

        add_curves_to_ax(ax=ax, curves=self._incrementalNMBLines, x_range=[self.wtpValues[0], self.wtpValues[-1]],
                         title=title, x_label=x_label,
                         y_label=y_label, y_range=y_range, x_delta=delta_wtp,
                         y_axis_format_decimals=y_axis_format_decimals,
                         y_axis_multiplier=y_axis_multiplier,
                         transparency_lines=Params['nmb.transparency'],
                         transparency_intervals=Params['nmb.interval.transparency'],
                         show_legend=show_legend,
                         legend_font_size_and_loc=legend_font_size_and_loc,
                         show_labels_on_frontier=show_labels_on_frontier,
                         show_frontier=True,
                         curve_line_width=Params['nmb.line_width'],
                         frontier_line_width=Params['nmb.frontier.line_width'],
                         frontier_label_shift_x=Params['nmb.frontier.label.shift_x'],
                         frontier_label_shift_y=Params['nmb.frontier.label.shift_y'],
                         grid_info=grid_info)

    def plot_acceptability_curves(self,
                                  title=None,
                                  x_label='Willingness-To-Pay Threshold',
                                  y_label='Probability of Being the Optimal Strategy',
                                  y_range=None,
                                  delta_wtp=None,
                                  show_legend=True, fig_size=(5, 5),
                                  legends=None,
                                  grid_info=None,
                                  file_name=None):
        """
        plots the acceptability curves
        :param title: title
        :param x_label: x-axis label
        :param y_label: y-axis label
        :param y_range: (list) range of y-axis
        :param delta_wtp: distance between the labels of WTP values shown on the x-axis
        :param show_legend: set true to show legend
        :param legends: (list) of legends to display on the figure
        :param fig_size: (tuple) size of the figure (e.g. (2, 3)
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        :param file_name: file name
        """

        # make the NMB curves
        self._build_incremental_nmb_curves(interval_type='n')

        # make the acceptability curves
        self._build_acceptability_curves()

        # initialize plot
        fig, ax = plt.subplots(figsize=fig_size)

        # add the acceptability curves
        self.add_acceptability_curves_to_ax(ax=ax,
                                            wtp_delta=delta_wtp,
                                            y_range=y_range,
                                            show_legend=show_legend,
                                            legends=legends,
                                            grid_info=grid_info)

        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        fig.tight_layout()
        output_figure(plt=fig, file_name=file_name)

    def add_acceptability_curves_to_ax(
            self, ax, wtp_delta=None, y_range=None, show_legend=True, legend_font_size_and_loc=None, legends=None,
            grid_info=None,  normal_approximation=False):
        """
        adds the acceptability curves to the provided ax
        :param ax: axis
        :param wtp_delta: (float) distance between ticks on x-axis
        :param y_range: (tuple) range of y-axis
        :param show_legend: (bool) if to show the legend
        :param legends: (list of strings) texts for legends
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        :param normal_approximation: (bool) set to True to use normal distributions to approximate
            the acceptability curves
        """

        if len(self._incrementalNMBLines) == 0:
            self._build_incremental_nmb_curves(interval_type='n')

        if len(self._acceptabilityCurves) == 0:
            self._build_acceptability_curves(normal_approximation=normal_approximation)

        if legend_font_size_and_loc is None:
            legend_font_size_and_loc = (
                Params['plot.legend.fontsize'],
                Params['plot.legend.loc']
            )

        add_curves_to_ax(ax=ax,
                         curves=self._acceptabilityCurves,
                         legends=legends,
                         x_range=[self.wtpValues[0], self.wtpValues[-1]],
                         x_delta=wtp_delta,
                         y_range=y_range, show_legend=show_legend,
                         transparency_lines=Params['ceac.transparency'],
                         curve_line_width=Params['ceac.line_width'],
                         frontier_line_width=Params['ceaf.line_width'],
                         legend_font_size_and_loc=legend_font_size_and_loc,
                         if_y_axis_prob=True, grid_info=grid_info)

    def add_expected_loss_curves_to_ax(
            self, ax, wtp_delta=None, y_range=None, show_legend=True, legend_font_size_and_loc=None, legends=None,
            y_axis_multiplier=1, y_axis_format_decimals=None, grid_info=None):
        """
        adds the acceptability curves to the provided ax
        :param ax: axis
        :param wtp_delta: (float) distance between ticks on x-axis
        :param y_range: (tuple) range of y-axis
        :param show_legend: (bool) if to show the legend
        :param legends: (list of strings) texts for legends
        :param legend_font_size_and_loc: (tuple) (font size, location) for the legend
        :param y_axis_multiplier: (float) multiplier for the y-axis
        :param y_axis_format_decimals: (format, int) format and number of decimal places to show on the y-axis
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        """

        if len(self._incrementalNMBLines) == 0:
            self._build_incremental_nmb_curves(interval_type='n')

        if len(self._expectedLossCurves) == 0:
            self._build_expected_loss_curves()

        if legend_font_size_and_loc is None:
            legend_font_size_and_loc = (
                Params['plot.legend.fontsize'],
                Params['plot.legend.loc']
            )

        add_curves_to_ax(ax=ax,
                         curves=self._expectedLossCurves,
                         legends=legends,
                         x_range=[self.wtpValues[0], self.wtpValues[-1]],
                         x_delta=wtp_delta,
                         y_range=y_range, show_legend=show_legend,
                         transparency_lines=Params['nmb.transparency'],
                         curve_line_width=Params['nmb.line_width'],
                         frontier_line_width=Params['nmb.frontier.line_width'],
                         legend_font_size_and_loc=legend_font_size_and_loc,
                         y_axis_multiplier=y_axis_multiplier, y_axis_format_decimals=y_axis_format_decimals,
                         if_y_axis_prob=False,
                         grid_info=grid_info)

    def plot_cep_nmb(self,
                     cost_multiplier=1, effect_multiplier=1, nmb_multiplier=0.001,
                     cep_title='', nmb_title='',
                     cost_decimals=0, effect_decimals=0, nmb_decimals=0,
                     cost_range=None, effect_range=None, nmb_range=None,
                     cep_x_label='Additional Effect',  cep_y_label='Additional Cost',
                     nmb_x_label='Willingness-To-Pay Threshold', nmb_y_label='Incremental Net Monetary Benefit',
                     delta_wtp=None, show_strategy_label_on_nmb_frontier=False,
                     file_name='cep-nmb.png', fig_size=(3, 7)):
        """
        produces a figure with 2 panels displaying
            cost-effectiveness plane,
            net-monetary benefit,
        :param cost_multiplier: (float) multiplier for cost values
        :param effect_multiplier: (float) multiplier for effect values
        :param nmb_multiplier: (float) multiplier for NMB values
        :param cep_title: (string) title of the cost-effectiveness plane
        :param nmb_title: (string) title of the net-monetary benefit figure
        :param cost_decimals: (int) number of decimals to show for cost values
        :param effect_decimals: (int) number of decimals to show for effect values
        :param nmb_decimals: (int) number of decimals to show for NMB values
        :param cost_range: (tuple) range of x-axis for the cost-effectiveness plane
        :param effect_range: (tuple) range of y-axis for the cost-effectiveness plane
        :param nmb_range: (tuple) range of y-axis for the NMB figure
        :param cep_x_label: (string) x-axis label for the cost-effectiveness plane
        :param cep_y_label: (string) y-axis label for the cost-effectiveness plane
        :param nmb_x_label: (string) x-axis label for the NMB figure
        :param nmb_y_label: (string) y-axis label for the NMB figure
        :param delta_wtp: (float) distance between the labels of WTP values shown on the x-axis
        :param show_strategy_label_on_nmb_frontier: (bool) set to True to show the strategy labels on the NMB frontier
        :param file_name: (string) the file name to save the figure as
        :param fig_size: (tuple) figure size
        """

        f, axes = plt.subplots(1, 2, figsize=fig_size)

        # add labels
        add_labels_to_panels(axarr=axes,
                             x_coord=-0.0, y_coord=1.05, font_size=10)

        # add cost-effectiveness plane
        self.add_ce_plane_to_ax(
            ax=axes[0], title=cep_title,
            cost_multiplier=cost_multiplier, effect_multiplier=effect_multiplier,
            cost_decimals=cost_decimals,  effect_decimals=effect_decimals,
            center_s=25, cloud_s=5,
            x_range=effect_range, y_range=cost_range,
            grid_info='default')
        axes[0].set_xlabel(cep_x_label)
        axes[0].set_ylabel(cep_y_label)

        # add net monetary benefit curve
        self.add_inmb_lines_to_ax(
            ax=axes[1], y_axis_format_decimals=(',', nmb_decimals),
            title=nmb_title,
            y_range=nmb_range,
            delta_wtp=delta_wtp,
            y_axis_multiplier=nmb_multiplier,
            x_label=nmb_x_label,
            y_label=nmb_y_label,
            interval_type='c',
            grid_info='default',
            show_labels_on_frontier=show_strategy_label_on_nmb_frontier,
            show_evpi=False)

        output_figure(plt=f, file_name=file_name)


class ConstrainedOpt(_EconEval):
    """ budget-constrained health optimization
    a class for selecting the alternative with the highest expected health outcomes
    subject to a budget constraint """

    def __init__(self, strategies, budget_range, if_paired, health_measure='u',
                 n_of_budget_values=200, epsilon=None):
        """
        :param strategies: the list of strategies (assumes that the first strategy represents the "base" strategy)
        :param budget_range: ([l, u]) range of budget values over which the analysis should be done
        :param if_paired: indicate whether the strategies are paired
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        :param n_of_budget_values: number of budget values to construct curves of optimal strategies
        :param epsilon: (float, 0 <= epsilon <= 1)
                        decision maker's tolerance in violating the budget constraint.
                        (i.e. epsilon in Prob{DCost_i > B} <= epsilon)
                        If set to None, this constraint will be considered: E[DCost_i] <= B.
        """
        _EconEval.__init__(self, strategies=strategies,
                           if_paired=if_paired,
                           health_measure=health_measure)

        # shift the strategies
        self._find_shifted_strategies()

        # list of cost values which the budget should be below
        # if epsilon = None, it takes the expected dCost of strategies,
        # otherwise, it takes the upper percentile of dCost of strategies.
        self.dCostUp = []
        # list of expected delta effect
        self.dEffect = []
        # list of expected effect curves (and EVPI if needed)
        self.curves = []
        # expected value of perfect information
        self.evpi = None

        # determine budget values
        self.budget_values = np.linspace(budget_range[0], budget_range[1],
                                         num=n_of_budget_values, endpoint=True)

        # set up curves
        for s in strategies:
            if epsilon is None:
                self.dCostUp.append(s.dCost.get_mean())
            else:
                self.dCostUp.append(s.dCost.get_percentile(q=(1 - epsilon) * 100))
            self.dEffect.append(s.dEffect.get_mean())
            self.curves.append(
                ExpHealthCurve(
                    label=s.name,
                    short_label=s.shortLabel,
                    color=s.color,
                    effect_stat=s.dEffect,
                    interval_type='c')
            )

        for b in self.budget_values:
            max_effect = -float('inf')
            max_s_i = None
            for s_i, s in enumerate(self.strategies):
                # if this strategy is feasible
                if self.dCostUp[s_i] <= b:
                    self.curves[s_i].update_feasibility(b=b)
                    if self.dEffect[s_i] > max_effect:
                        max_effect = self.dEffect[s_i]
                        max_s_i = s_i

            if max_s_i is None:
                self.curves[0].frontierXs.append(b)
                self.curves[0].frontierYs.append(None)
            else:
                self.curves[max_s_i].frontierXs.append(b)
                self.curves[max_s_i].frontierYs.append(max_effect)

        # convert lists to arrays
        for c in self.curves:
            c.convert_lists_to_arrays()

    def _calculate_evpi_curve(self):
        """ calculates the expected value of perfect information (EVPI) curve """

        self.evpi = []
        n_of_sims = len(self.strategies[0].dCostObs)

        extra_budget = []
        for s in self.strategies:
            extra_budget.append(s.cost.get_percentile(97.5) - s.cost.get_mean())

        # for all budget value
        for b in self.budget_values:

            # find the best achievable expected effect under perfect information
            max_effects = []
            for i in range(n_of_sims):
                # find costs and effects of strategies for the ith monte carlo simulation run
                costs = [s.dCostObs[i] for s in self.strategies]
                effects = [s.dEffectObs[i] for s in self.strategies]

                # find the maximum effect
                max_e = float('-inf')
                for c, e, extra in zip(costs, effects, extra_budget):

                    # cost of this strategy doesn't satisfy the budget if
                    if c <= b + extra and e > max_e:
                        max_e = e
                max_effects.append(max_e)

            self.evpi.append(average(max_effects))

        # curve
        self.curves.append(
            EVPI(xs=self.budget_values, ys=self.evpi, label='PI', color='k'))

    def plot(self,
             title='Expected Increase in Effect',
             x_label='Budget',
             y_label='Expected Increase in Effect',
             show_evpi=False,
             y_range=None,
             y_axis_multiplier=1,
             delta_budget=None,
             transparency_lines=0.5,
             transparency_intervals=0.2,
             show_legend=True,
             figure_size=(5, 5),
             file_name='Budget.png'):

        # initialize plot
        fig, ax = plt.subplots(figsize=figure_size)

        if show_evpi:
            self._calculate_evpi_curve()

        # add plot to the ax
        add_curves_to_ax(ax=ax,
                         curves=self.curves,
                         x_range=[self.budget_values[0], self.budget_values[-1]],
                         title=title, x_label=x_label,
                         y_label=y_label, y_range=y_range, x_delta=delta_budget,
                         y_axis_multiplier=y_axis_multiplier,
                         transparency_lines=transparency_lines,
                         transparency_intervals=transparency_intervals,
                         show_legend=show_legend,
                         if_format_y_numbers=False)

        fig.show()
        if file_name is not None:
            fig.savefig(file_name, dpi=300)

    def add_e_by_budget_to_ax(self, ax, title=None,
                              delta_budget=None, x_label=None,
                              y_label=None, y_range=None, y_axis_multiplier=1, effect_decimals=None,
                              show_evpi=False, show_legend=True, legend_font_size_and_loc=None, show_frontier=True, show_labels_on_frontier=False,
                              grid_info='default'):
        """ add the effect by budget to the axis
        :param ax: axis
        :param title: (string) title of the figure
        :param delta_budget: (float) the distance between ticks on the x-axis
        :param x_label: (string) x-axis label
        :param y_label: (string) y-axis label
        :param y_range: (tuple) y-axis range
        :param y_axis_multiplier: (float) to multiply the y-axis values by
        :param effect_decimals: (int) to round the values of y-axis (effect)
        :param show_evpi: (bool) to show the expected value of perfect information (EVPI) curve
        :param show_legend: (bool) to show legends
        :param legend_font_size_and_loc: (tuple) (font size, location) of the legend
        :param show_frontier: (bool) to show the frontier (curves with maximum effect or NMB)
        :param show_labels_on_frontier: (bool) to show labels on the frontier
        :param grid_info: (None or 'default', or tuple of (color, linestyle, linewidth, alpha))
            if 'default is selected the tuple ('k', '--', 0.5, 0.2) is used
        """

        if show_evpi:
            self._calculate_evpi_curve()

        if legend_font_size_and_loc is None:
            legend_font_size_and_loc = (
                Params['plot.legend.fontsize'],
                Params['plot.legend.loc']
            )

        y_axis_format_decimals = [',', effect_decimals] if effect_decimals is not None else None
        add_curves_to_ax(
            ax=ax, curves=self.curves, title=title,
            x_range=[self.budget_values[0], self.budget_values[-1]],
            x_delta=delta_budget, x_label=x_label,
            y_label=y_label, y_range=y_range, y_axis_multiplier=y_axis_multiplier,
            transparency_lines=1,
            transparency_intervals=Params['nmb.interval.transparency'],
            show_legend=show_legend,
            show_frontier=show_frontier,
            show_labels_on_frontier=show_labels_on_frontier,
            curve_line_width=Params['nmb.line_width'],
            frontier_line_width=Params['nmb.frontier.line_width'],
            y_axis_format_decimals=y_axis_format_decimals,
            legend_font_size_and_loc=legend_font_size_and_loc,
            frontier_label_shift_x=Params['ce.frontier.label.shift_x'],
            frontier_label_shift_y=Params['ce.frontier.label.shift_y'],
        )

        add_grids(ax=ax, grid_info=grid_info)


class _ComparativeEconMeasure:
    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) effect data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) effect data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        if health_measure not in ['u', 'd']:
            raise ValueError("health_measure can be either 'u' (for utility) or 'd' (for disutility).")

        self.name = name
        # if QALY or DALY is being used
        self._effectMeasure = health_measure
        self._effectMultiplier = 1 if health_measure == 'u' else -1

        # convert input data to numpy.array if needed
        self._costsNew = assert_np_list(costs_new, "cost_new should be list or np.array.")
        self._effectsNew = assert_np_list(effects_new, "effects_new should be list or np.array.")
        self._costsBase = assert_np_list(costs_base, "costs_base should be list or np.array.")
        self._effectsBase = assert_np_list(effects_base, "effects_base should be list or np.array.")

        # calculate the difference in average cost
        self._deltaAveCost = np.average(self._costsNew) - np.average(self._costsBase)
        # change in effect: DALY averted or QALY gained
        self._deltaAveEffect = (np.average(self._effectsNew) - np.average(self._effectsBase)) \
                               * self._effectMultiplier

    def get_ave_d_cost(self):
        """
        :return: average incremental cost
        """
        return self._deltaAveCost

    def get_ave_d_effect(self):
        """
        :return: average incremental effect
        """
        return self._deltaAveEffect


class _ICER(_ComparativeEconMeasure):
    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) effect data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) effect data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        self._isDefined = True  # if ICER cannot be computed, this will change to False

        # initialize the base class
        _ComparativeEconMeasure.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

        # calculate ICER
        if not (self._deltaAveEffect > 0 and self._deltaAveCost >= 0):
            warnings.warn(self.name + ': Mean incremental effect should be > 0 '
                                      'and mean incremental cost should be >= 0. '
                                      'ICER is not computable.')
            self._isDefined = False
            self._ICER = math.nan
        else:
            # $ per DALY averted or $ per QALY gained
            self._ICER = self._deltaAveCost / self._deltaAveEffect

    def get_ICER(self):
        """ return ICER """
        return self._ICER

    def get_CI(self, alpha=0.05, method='bootstrap', num_bootstrap_samples=1000, rng=None,
               prior_range=None, num_wtp_thresholds=1000):
        """
        :param alpha: significance level, a value from [0, 1]
        :param method: (string) 'bootstrap' or 'Bayesian'
        :param num_bootstrap_samples: number of bootstrap samples when 'bootstrap' method is selected
        :param rng: random number generator to generate empirical bootstrap samples
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used.
        :return: confidence interval in the format of list [l, u]
        """
        # abstract method to be overridden in derived classes to process an event
        raise NotImplementedError("This is an abstract method and needs to be implemented in derived classes.")

    def get_PI(self, alpha=0.05):
        """
        :param alpha: significance level, a value from [0, 1]
        :return: percentile interval in the format of list [l, u]
        """
        # abstract method to be overridden in derived classes to process an event
        raise NotImplementedError("This is an abstract method and needs to be implemented in derived classes.")

    def get_formatted_mean_and_interval(self, interval_type='c',
                                        alpha=0.05, method='bootstrap', num_bootstrap_samples=1000, rng=None,
                                        prior_range=None, num_wtp_thresholds=1000,
                                        deci=0, sig_digits=4, form=None,
                                        multiplier=1):
        """
        :param interval_type: (string) 'n' for no interval
                                       'c' or 'cb' for bootstrap confidence interval, and
                                       'p' for percentile interval
        :param alpha: significance level, a value from [0, 1]
        :param method: (string) method to calculate confidence interval ('bootstrap' or 'Bayesian')
        :param num_bootstrap_samples: number of bootstrap samples when 'bootstrap' method is selected
        :param rng: random number generator to generate empirical bootstrap samples
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used
        :param deci: digits to round the numbers to
        :param sig_digits: number of significant digits
        :param form: ',' to format as number, '%' to format as percentage, and '$' to format as currency
        :param multiplier: to multiply the estimate and the interval by the provided value
        :param num_bootstrap_samples: number of bootstrap samples to calculate confidence interval
        :return: (string) estimate of ICER and interval formatted as specified
        """

        estimate = self.get_ICER() * multiplier

        if interval_type == 'c' or interval_type == 'cb':
            interval = self.get_CI(alpha=alpha, method=method, num_bootstrap_samples=num_bootstrap_samples, rng=rng,
                                   prior_range=prior_range, num_wtp_thresholds=num_wtp_thresholds)
        elif interval_type == 'p':
            interval = self.get_PI(alpha=alpha)
        else:
            interval = None

        adj_interval = [v * multiplier for v in interval] if interval is not None else None

        return F.format_estimate_interval(estimate=estimate,
                                          interval=adj_interval,
                                          deci=deci,
                                          sig_digits=sig_digits,
                                          format=form)


class ICERPaired(_ICER):

    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) health data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the baseline
        :param effects_base: (list or numpy.array) health data for the baseline
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        # all cost and effects should have the same length
        if not (len(costs_new) == len(effects_new) == len(costs_base) == len(effects_base)):
            raise ValueError('Paired ICER assume the same number of observations for all cost and health outcomes.')

        # initialize the base class
        _ICER.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

        # incremental observations
        self._deltaCosts = self._costsNew - self._costsBase
        self._deltaEffects = (self._effectsNew - self._effectsBase) * self._effectMultiplier

    def get_CI(self, alpha=0.05, method='bootstrap', num_bootstrap_samples=1000, rng=None,
               prior_range=None, num_wtp_thresholds=1000):
        """
        :param alpha: (double) significance level, a value from [0, 1]
        :param method: (string) 'bootstrap' or 'bayesian' or 'fieller' or 'taylor'
        :param num_bootstrap_samples: number of bootstrap samples when 'bootstrap' method is selected
        :param rng: random number generator to generate empirical bootstrap samples
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used.
        :return: confidence interval in the format of list [l, u]
        """

        # if ICER is not defined, the confidence interval is not defined either
        if np.isnan(self._ICER):
            return [np.nan, np.nan]

        n_obs = len(self._deltaCosts)

        # create a new random number generator if one is not provided.
        if rng is None:
            rng = RandomState(seed=1)

        # check if the Bayesian approach is selected
        if method == 'bayesian' or method == 'Bayesian':

            return get_bayesian_ci_for_switch_wtp(
                delta_costs=self._deltaCosts,
                delta_effects=self._deltaEffects,
                alpha=alpha,
                num_wtp_thresholds=num_wtp_thresholds,
                prior_range=prior_range,
                rng=rng
            )

        elif method == 'fieller' or method == 'Fieller':

            mean_d_cost = self._deltaAveCost
            mean_d_effect = self._deltaAveEffect
            var_d_cost = np.var(self._deltaCosts, ddof=1)
            var_d_effect = np.var(self._deltaEffects, ddof=1)
            cov = np.cov(self._deltaCosts, self._deltaEffects)[0, 1]
            z = stat.norm.ppf(1-alpha/2)

            # solve aR^2 + bR + c = 0
            a = mean_d_effect ** 2 - z**2 * var_d_effect
            b = - 2 * (mean_d_effect * mean_d_cost - z**2 * cov)
            c = mean_d_cost ** 2 - z**2 * var_d_cost

            # solve a quadratic equation
            delta = b**2 - 4 * a * c
            if delta < 0:
                return [np.nan, np.nan]
            else:
                r1 = (-b - np.sqrt(delta)) / (2 * a)
                r2 = (-b + np.sqrt(delta)) / (2 * a)

            # negative ICER is not defined
            if r1 < 0:
                return [np.nan, np.nan]
            else:
                return [r1, r2]

        elif method == 'taylor' or method == 'Taylor':

            mean_d_cost = self._deltaAveCost
            mean_d_effect = self._deltaAveEffect
            var_d_cost = np.var(self._deltaCosts, ddof=1)
            var_d_effect = np.var(self._deltaEffects, ddof=1)
            cov = np.cov(self._deltaCosts, self._deltaEffects)[0, 1]
            z = stat.norm.ppf(1-alpha/2)

            # st dev of icer
            a = var_d_cost / mean_d_cost ** 2
            b = var_d_effect / mean_d_effect ** 2
            c = - 2 * cov/(mean_d_cost * mean_d_effect)
            st_dev_r = self._ICER * math.sqrt(a + b + c)

            r1 = self._ICER - z * st_dev_r
            r2 = self._ICER + z * st_dev_r

            # negative ICER is not defined
            if r1 < 0:
                return [np.nan, np.nan]
            else:
                return [r1, r2]

        elif method == 'bootstrap' or method == 'Bootstrap':
            # bootstrap algorithm

            ratio_stat = RatioOfMeansStatPaired(
                x=self._deltaCosts,
                y_ref=self._deltaEffects,
                name='ICER'
            )

            return ratio_stat.get_bootstrap_CI(alpha=alpha, num_samples=num_bootstrap_samples)

        else:
            raise ValueError('Invalid method. Method should be either bootstrap or Bayesian.')

    def get_PI(self, alpha=0.05):
        """
        :param alpha: significance level, a value from [0, 1]
        :return: prediction interval in the format of list [l, u]
        """

        # calculate ICERs
        if min(self._deltaEffects) <= 0:
            warnings.warn("\nFor '{0},' the prediction interval of ICERs is not computable because at least one "
                          "incremental effect is negative or zero.".format(self.name))
            return [math.nan, math.nan]
        else:
            icers = np.divide(self._deltaCosts, self._deltaEffects)

        return np.percentile(icers, [100 * alpha / 2.0, 100 * (1 - alpha / 2.0)])

    def get_icer_over_iterations(self):
        """
        :return: ICER over iterations
        """
        mean_delta_cost = Stat.DiscreteTimeStat(name='Mean Delta Cost')
        mean_delta_effect = Stat.DiscreteTimeStat(name='Mean Delta Effect')
        icer_over_iterations = []

        for i in range(len(self._deltaCosts)):
            mean_delta_cost.record(self._deltaCosts[i])
            mean_delta_effect.record(self._deltaEffects[i])

            # if ICER so far is defined
            if mean_delta_effect.get_mean() > 0 and mean_delta_cost.get_mean() >= 0:
                icer_over_iterations.append(mean_delta_cost.get_mean() / mean_delta_effect.get_mean())
            else:
                icer_over_iterations.append(math.nan)

        return icer_over_iterations


class ICERIndp(_ICER):

    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) health data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) health data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        # all cost and effects should have the same length for each alternative
        if not (len(costs_new) == len(effects_new) and len(costs_base) == len(effects_base)):
            raise ValueError(
                'ICER assume the same number of observations for the cost and health outcome of each alternative.')

        # initialize the base class
        _ICER.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

    def get_CI(self, alpha=0.05, method='bootstrap', num_bootstrap_samples=1000, rng=None,
               prior_range=None, num_wtp_thresholds=1000):
        """
        :param alpha: significance level, a value from [0, 1]
        :param method: (string) 'bootstrap' or 'Bayesian'
        :param num_bootstrap_samples: number of bootstrap samples when 'bootstrap' method is selected
        :param rng: random number generator to generate empirical bootstrap samples
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used.
        :return: confidence interval in the format of list [l, u]
        """

        if not self._isDefined:
            return [math.nan, math.nan]

        if method == 'Bayesian':
            raise ValueError('The Bayesian approach is not implemented. Use bootstrap instead.')

        # create a new random number generator if one is not provided.
        if rng is None:
            rng = RandomState(seed=1)

        # vector to store bootstrap ICERs
        icer_bootstrap_means = np.zeros(num_bootstrap_samples)

        n_obs_new = len(self._costsNew)
        n_obs_base = len(self._costsBase)

        # get bootstrap samples
        for i in range(num_bootstrap_samples):
            # for the new alternative
            indices_new = rng.choice(a=range(n_obs_new), size=n_obs_new, replace=True)
            costs_new = self._costsNew[indices_new]
            effects_new = self._effectsNew[indices_new]

            # for the base alternative
            indices_base = rng.choice(a=range(n_obs_base), size=n_obs_base, replace=True)
            costs_base = self._costsBase[indices_base]
            effects_base = self._effectsBase[indices_base]

            # calculate this bootstrap ICER
            mean_costs_new = np.mean(costs_new)
            mean_costs_base = np.mean(costs_base)
            mean_effects_new = np.mean(effects_new)
            mean_effects_base = np.mean(effects_base)

            # calculate this bootstrap ICER
            if (mean_effects_new - mean_effects_base) * self._effectMultiplier <= 0:
                self._isDefined = False
                warnings.warn('\nFor "{}, the confidence interval of ICER is not computable."'
                              '\nThis is because at least one of bootstrap mean incremental effect '
                              'is negative.'
                              '\nIncreasing the number of cost and effect observations '
                              'might resolve the issue.'.format(self.name))
                return [math.nan, math.nan]

            else:
                icer_bootstrap_means[i] = \
                    (mean_costs_new - mean_costs_base) / (mean_effects_new - mean_effects_base) \
                    * self._effectMultiplier

        if self._isDefined:
            return np.percentile(icer_bootstrap_means, [100 * alpha / 2.0, 100 * (1 - alpha / 2.0)])
        else:
            return [math.nan, math.nan]

    def get_PI(self, alpha=0.05, num_bootstrap_samples=1000, rng=None):
        """
        :param alpha: significance level, a value from [0, 1]
        :param num_bootstrap_samples: number of bootstrap samples
        :param rng: random number generator
        :return: prediction interval in the format of list [l, u]
        """

        if self._ICER is math.nan:
            return [math.nan, math.nan]

        # create a new random number generator if one is not provided.
        if rng is None:
            rng = RandomState(seed=1)

        if num_bootstrap_samples == 0:
            num_bootstrap_samples = max(len(self._costsNew), len(self._costsBase))

        # calculate element-wise ratio as sample of ICER
        indices_new = rng.choice(a=range(num_bootstrap_samples), size=num_bootstrap_samples, replace=True)
        costs_new = self._costsNew[indices_new]
        effects_new = self._effectsNew[indices_new]

        indices_base = rng.choice(a=range(num_bootstrap_samples), size=num_bootstrap_samples, replace=True)
        costs_base = self._costsBase[indices_base]
        effects_base = self._effectsBase[indices_base]

        if min((effects_new - effects_base) * self._effectMultiplier) <= 0:
            self._isDefined = False
            warnings.warn('\nFor "{}, the prediction interval of ICER is not computable."'
                          '\nThis is because at least one of bootstrap mean incremental effect '
                          'is negative'.format(self.name))
            return [math.nan, math.nan]
        else:
            sample_icers = np.divide(
                (costs_new - costs_base),
                (effects_new - effects_base) * self._effectMultiplier)

        if self._isDefined:
            return np.percentile(sample_icers, [100 * alpha / 2.0, 100 * (1 - alpha / 2.0)])
        else:
            return [math.nan, math.nan]


class _IncrementalNMB(_ComparativeEconMeasure):
    # incremental net monetary benefit
    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) effect data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) effect data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """
        # initialize the base class
        _ComparativeEconMeasure.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

    def get_incremental_nmb(self, wtp):
        """
        :param wtp: willingness-to-pay ($ for QALY gained or $ for DALY averted)
        :returns: the incremental net monetary benefit at the provided willingness-to-pay value
        """
        return wtp * self._deltaAveEffect - self._deltaAveCost

    def get_CI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: confidence interval in the format of list [l, u]
        """
        # abstract method to be overridden in derived classes
        raise NotImplementedError("This is an abstract method and needs to be implemented in derived classes.")

    def get_PI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: percentile interval in the format of list [l, u]
        """
        # abstract method to be overridden in derived classes
        raise NotImplementedError("This is an abstract method and needs to be implemented in derived classes.")

    def get_switch_wtp(self):

        try:
            wtp = self.get_ave_d_cost() / self.get_ave_d_effect()
        except ValueError:
            wtp = math.nan

        return wtp


class IncrementalNMBPaired(_IncrementalNMB):

    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) health data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) health data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        # all cost and effects should have the same length
        if not (len(costs_new) == len(effects_new) == len(costs_base) == len(effects_base)):
            raise ValueError(
                'Paired incremental NMB assumes the same number of observations for all cost and health outcomes.')

        _IncrementalNMB.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

        # incremental observations
        self._deltaCosts = self._costsNew - self._costsBase
        self._deltaEffects = (self._effectsNew - self._effectsBase) * self._effectMultiplier

        self._n = len(costs_new)
        self._statDeltaCost = Stat.SummaryStat(name=self.name, data=self._deltaCosts)
        self._statDeltaEffect = Stat.SummaryStat(name=self.name, data=self._deltaEffects)
        self._corr = corrcoef(self._deltaCosts, self._deltaEffects)[0, 1]

    def get_CI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: confidence interval in the format of list [l, u]
        """
        mean = self.get_incremental_nmb(wtp=wtp)

        t = math.nan
        if self._n > 1:
            t = stat.t.ppf(1 - alpha / 2, self._n - 1)

        st_dev = math.sqrt(get_var_of_inmb(wtp=wtp,
                                           st_d_cost=self._statDeltaCost.get_stdev(),
                                           st_d_effect=self._statDeltaEffect.get_stdev(),
                                           corr=self._corr))
        st_err = st_dev/math.sqrt(self._n)

        l = mean - t * st_err
        u = mean + t * st_err
        return [l, u]

    def get_PI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: percentile interval in the format of list [l, u]
        """
        return Stat.SummaryStat(name=self.name,
                                data=wtp * self._deltaEffects - self._deltaCosts).get_PI(alpha)

    def get_switch_wtp_and_ci_interval(self, alpha=0.05, interval_type='n',
                                       num_bootstrap_samples=1000,
                                       num_wtp_thresholds=1000, prior_range=None, rng=None):
        """
        :param alpha: (double) significance level, a value from [0, 1]
        :param interval_type: (string) 'n' for none and 'c' for confidence interval
        :param num_wtp_thresholds: (int) number of willingness-to-pay thresholds to evaluate posterior
            when 'Bayesian' approach is selected
        :param prior_range: (tuple) in form of (l, u) for the prior range of willingness-to-pay
            threshold that makes NMB zero (if prior is not provided [0, 4 * ICER] will be used.
        :param rng: random number generator to generate empirical bootstrap samples
        :return: bayesian confidence interval in the format of list [l, u]
        """

        wtp = self.get_switch_wtp()

        if interval_type == 'n' or interval_type is None:
            return wtp, None
        elif interval_type == 'c':

            icer =ICERPaired(costs_new=self._costsNew,
                             effects_new=self._effectsNew,
                             costs_base=self._costsBase,
                             effects_base=self._effectsBase,
                             health_measure=self._effectMeasure)

            return icer.get_CI(alpha, method='bootstrap', num_bootstrap_samples=num_bootstrap_samples, rng=rng)

            # return wtp, get_bayesian_ci_for_switch_wtp(
            #     delta_costs=self._deltaCosts,
            #     delta_effects=self._deltaEffects,
            #     alpha=alpha,
            #     num_wtp_thresholds=num_wtp_thresholds,
            #     prior_range=prior_range, rng=rng
            # )
        elif interval_type == 'p':
            raise ValueError('Not implemented.')
        else:
            raise ValueError('Invalid value for interval_type.')


class IncrementalNMBIndp(_IncrementalNMB):

    def __init__(self, costs_new, effects_new, costs_base, effects_base, health_measure='u', name=''):
        """
        :param costs_new: (list or numpy.array) cost data for the new strategy
        :param effects_new: (list or numpy.array) health data for the new strategy
        :param costs_base: (list or numpy.array) cost data for the base line
        :param effects_base: (list or numpy.array) health data for the base line
        :param health_measure: (string) choose 'u' if higher "effect" implies better health
        (e.g. when QALY is used) and set to 'd' if higher "effect" implies worse health
        (e.g. when DALYS is used)
        """

        # all costs and effects should have the same length for each strategy
        if not (len(costs_new) == len(effects_new) and len(costs_base) == len(effects_base)):
            raise ValueError(
                'Independent incremental NMB assumes that for each strategy there are '
                'the same number of observations for cost and health outcomes.')

        _IncrementalNMB.__init__(self, costs_new, effects_new, costs_base, effects_base, health_measure, name)

    def get_CI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: confidence interval in the format of list [l, u]
        """
        # NMB observations of two alternatives
        stat_new = wtp * self._effectsNew * self._effectMultiplier - self._costsNew
        stat_base = wtp * self._effectsBase * self._effectMultiplier - self._costsBase

        # to get CI for stat_new - stat_base
        diff_stat = Stat.DifferenceStatIndp(name=self.name, x=stat_new, y_ref=stat_base)
        return diff_stat.get_t_CI(alpha)

    def get_PI(self, wtp, alpha=0.05):
        """
        :param wtp: willingness-to-pay value ($ for QALY gained or $ for DALY averted)
        :param alpha: significance level, a value from [0, 1]
        :return: percentile interval in the format of list [l, u]
        """
        # NMB observations of two alternatives
        stat_new = wtp * self._effectsNew * self._effectMultiplier - self._costsNew
        stat_base = wtp * self._effectsBase * self._effectMultiplier - self._costsBase

        # to get PI for stat_new - stat_base
        diff_stat = Stat.DifferenceStatIndp(name=self.name, x=stat_new, y_ref=stat_base)
        return diff_stat.get_PI(alpha)

