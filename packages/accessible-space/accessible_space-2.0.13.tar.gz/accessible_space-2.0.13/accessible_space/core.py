import collections
import gc
import warnings

import numpy as np
import scipy.integrate

from .motion_models import constant_velocity_time_to_arrive_1d, approx_two_point_time_to_arrive, constant_velocity_time_to_arrive
from .utility import progress_bar


# SimulationResult object to hold simulation results
_result_fields = [
    "attack_cum_prob",  # F x PHI x T
    "attack_cum_poss",  # F x PHI x T
    "attack_prob_density",  # F x PHI x T
    "attack_poss_density",  # F x PHI x T
    "defense_cum_prob",  # F x PHI x T
    "defense_cum_poss",  # F x PHI x T
    "defense_prob_density",  # F x PHI x T
    "defense_poss_density",  # F x PHI x T

    "cum_p0",  # F x PHI x T
    "p0_density",  # F x PHI x T

    "player_cum_prob",  # F x P x PHI x T
    "player_cum_poss",  # F x P x PHI x T
    "player_prob_density",  # F x P x PHI x T
    "player_poss_density",  # F x P x PHI x T

    "phi_grid",  # PHI
    "r_grid",  # T
    "x_grid",  # F x PHI x T
    "y_grid",  # F x PHI x T
]
ALL_OPTIONAL_FIELDS_TO_RETURN = tuple([field for field in _result_fields if field not in ["phi_grid", "r_grid", "x_grid", "y_grid"]])
SimulationResult = collections.namedtuple("SimulationResult", _result_fields, defaults=[None] * len(_result_fields))

# Default model parameters
_DEFAULT_A_MAX = 10.659091365334193
_DEFAULT_B0 = -4.565680899844368
_DEFAULT_B1 = -188.74468208593532
_DEFAULT_EXCLUDE_PASSER = True
_DEFAULT_FACTOR = 5.077423030272923
_DEFAULT_FACTOR2 = 1.0063028450754512
_DEFAULT_INERTIAL_SECONDS = 1.1043767821571149
_DEFAULT_KEEP_INERTIAL_VELOCITY = True
_DEFAULT_N_V0 = 13.751097117532021
_DEFAULT_NORMALIZE = False
_DEFAULT_PASS_START_LOCATION_OFFSET = -1.5245340256423476
_DEFAULT_PLAYER_VELOCITY = 34.6836072667285
_DEFAULT_RADIAL_GRIDSIZE = 5.034759576558597
_DEFAULT_RESPECT_OFFSIDE = False
_DEFAULT_TIME_OFFSET_BALL = -0.4384754490159207
_DEFAULT_TOL_DISTANCE = 9.986761680941445
_DEFAULT_USE_APPROX_TWO_POINT = True
_DEFAULT_USE_EFFICIENT_SIGMOID = True
_DEFAULT_USE_FIXED_V0 = True
_DEFAULT_USE_MAX = True
_DEFAULT_USE_POSS = True
_DEFAULT_V0_MAX = 42.18118275402132
_DEFAULT_V0_MIN = 8.886015553615485
_DEFAULT_V0_PROB_AGGREGATION_MODE = "mean"
_DEFAULT_V_MAX = 19.85563874348074


def _approximate_sigmoid(x):
    """
    Computational efficient sigmoid approximation.

    >>> _approximate_sigmoid(np.array([-1, 0, 1])), 1 / (1 + np.exp(-np.array([-1, 0, 1])))
    (array([0.25, 0.5 , 0.75]), array([0.26894142, 0.5       , 0.73105858]))
    """
    return 0.5 * (x / (1 + np.abs(x)) + 1)


def _sigmoid(x):
    """
    >>> _sigmoid(np.array([-1, 0, 1]))
    array([0.26894142, 0.5       , 0.73105858])
    """
    return 1 / (1 + np.exp(-x))


def _assert_matrix_consistency(PLAYER_POS, BALL_POS, phi_grid, v0_grid, passer_team, team_list, players=None, passers=None):
    F = PLAYER_POS.shape[0]
    assert F == BALL_POS.shape[0], f"Dimension F is {F} (from PLAYER_POS: {PLAYER_POS.shape}), but BALL_POS shape is {BALL_POS.shape}"
    assert F == phi_grid.shape[0], f"Dimension F is {F} (from PLAYER_POS: {PLAYER_POS.shape}), but phi_grid shape is {phi_grid.shape}"
    assert F == v0_grid.shape[0], f"Dimension F is {F} (from PLAYER_POS: {PLAYER_POS.shape}), but v0_grid shape is {v0_grid.shape}"
    assert F == passer_team.shape[0], f"Dimension F is {F} (from PLAYER_POS: {PLAYER_POS.shape}), but passer_team shape is {passer_team.shape}"
    P = PLAYER_POS.shape[1]
    assert P == team_list.shape[0], f"Dimension P is {P} (from PLAYER_POS: {PLAYER_POS.shape}), but team_list shape is {team_list.shape}"
    assert PLAYER_POS.shape[2] >= 4  # >= or = ?
    assert BALL_POS.shape[1] >= 2  # ...
    if passers is not None:
        assert F == passers.shape[0], f"Dimension F is {F} (from PLAYER_POS: {PLAYER_POS.shape}), but passers shape is {passers.shape}"
        assert P == players.shape[0], f"Dimension P is {P} (from PLAYER_POS: {PLAYER_POS.shape}), but players shape is {players.shape}"


def simulate_passes(
    # Input data
    PLAYER_POS,  # F x P x 4[x, y, vx, vy], player positions
    BALL_POS,  # F x 2[x, y], ball positions
    phi_grid,  # F x PHI, pass angles
    v0_grid,  # F x V0, pass speeds
    passer_teams,  # F, frame-wise team of passers
    player_teams,  # P, player teams
    players=None,  # P, players
    passers=None,  # F, frame-wise passer
    exclude_passer=False,
    playing_direction=None,
    respect_offside=False,
    fields_to_return=ALL_OPTIONAL_FIELDS_TO_RETURN,
    x_pitch_min=-52.5, x_pitch_max=52.5, y_pitch_min=-34, y_pitch_max=34,

    # Model parameters
    pass_start_location_offset=_DEFAULT_PASS_START_LOCATION_OFFSET,
    time_offset_ball=_DEFAULT_TIME_OFFSET_BALL,
    radial_gridsize=_DEFAULT_RADIAL_GRIDSIZE,
    b0=_DEFAULT_B0,
    b1=_DEFAULT_B1,
    player_velocity=_DEFAULT_PLAYER_VELOCITY,
    keep_inertial_velocity=_DEFAULT_KEEP_INERTIAL_VELOCITY,
    use_max=_DEFAULT_USE_MAX,
    v_max=_DEFAULT_V_MAX,
    a_max=_DEFAULT_A_MAX,
    inertial_seconds=_DEFAULT_INERTIAL_SECONDS,
    tol_distance=_DEFAULT_TOL_DISTANCE,
    use_approx_two_point=_DEFAULT_USE_APPROX_TWO_POINT,
    v0_prob_aggregation_mode=_DEFAULT_V0_PROB_AGGREGATION_MODE,
    normalize=_DEFAULT_NORMALIZE,
    use_efficient_sigmoid=_DEFAULT_USE_EFFICIENT_SIGMOID,

    factor=_DEFAULT_FACTOR,
    factor2=_DEFAULT_FACTOR2,
) -> SimulationResult:
    """ Calculate the pass simulation model using numpy matrices - Core functionality of this package

    # Simulate a pass from player A straight to the right towards a defender B who is 50m away.
    >>> res = simulate_passes(np.array([[[0, 0, 0, 0], [50, 0, 0, 0]]]), np.array([[0, 0]]), np.array([[0]]), np.array([[10]]), np.array([0]), np.array([0, 1]), players=np.array(["A", "B"]), passers=np.array(["A"]), radial_gridsize=15)
    >>> res.defense_poss_density.shape, res.defense_poss_density
    ((1, 1, 13), array([[[8.89786731e-05, 1.64897230e-04, 1.29669104e-03, 1.94280126e-01,
             1.91894891e-01, 1.88063562e-01, 1.77544360e-01, 3.89546322e-02,
             2.01864630e-03, 1.02515215e-04, 5.17596953e-06, 2.60590596e-07,
             1.30974323e-08]]]))
    >>> res.attack_cum_prob.shape, res.attack_cum_prob  # F x PHI x T
    ((1, 1, 13), array([[[0.        , 0.01097577, 0.01807728, 0.02306136, 0.02424135,
             0.02432508, 0.02433268, 0.02433416, 0.02433455, 0.02433456,
             0.02433456, 0.02433456, 0.02433456]]]))
    >>> res.phi_grid.shape, res.phi_grid
    ((1, 1), array([[0]]))
    >>> res.r_grid.shape, res.r_grid
    ((13,), array([ -1.52453403,  13.47546597,  28.47546597,  43.47546597,
            58.47546597,  73.47546597,  88.47546597, 103.47546597,
           118.47546597, 133.47546597, 148.47546597, 163.47546597,
           178.47546597]))
    >>> res.x_grid.shape, res.x_grid
    ((1, 1, 13), array([[[ -1.52453403,  13.47546597,  28.47546597,  43.47546597,
              58.47546597,  73.47546597,  88.47546597, 103.47546597,
             118.47546597, 133.47546597, 148.47546597, 163.47546597,
             178.47546597]]]))
    >>> res.y_grid.shape, res.y_grid
    ((1, 1, 13), array([[[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]]]))
    """
    if not set(fields_to_return) <= set(ALL_OPTIONAL_FIELDS_TO_RETURN):
        invalid_fields = set(fields_to_return) - set(ALL_OPTIONAL_FIELDS_TO_RETURN)
        raise ValueError(f"fields_to_return contains unknown fields: {invalid_fields}. Available: {ALL_OPTIONAL_FIELDS_TO_RETURN}")

    _assert_matrix_consistency(PLAYER_POS, BALL_POS, phi_grid, v0_grid, passer_teams, player_teams, players, passers)

    def _should_return_any_of(fields):
        return any([field in fields for field in fields_to_return])

    # Pre-processing: Treat offside players like air
    if respect_offside:
        if playing_direction is None:
            raise ValueError("'playing_direction' must be provided if 'respect_offside' is True")

        PLAYERS_NORM_X = PLAYER_POS[:, :, 0] * playing_direction[:, np.newaxis]  # F x P
        BALL_NORM_X = BALL_POS[:, 0] * playing_direction

        is_attacking_team = (passer_teams[:, np.newaxis] == player_teams[np.newaxis, :]) | ~np.isfinite(PLAYERS_NORM_X)  # F x P
        SECOND_LAST_DEFENDER_NORM_X = np.ma.sort(np.ma.array(PLAYERS_NORM_X, mask=is_attacking_team), axis=1, endwith=False)[:, -2]
        X_OFFSIDE_LINE = np.maximum(SECOND_LAST_DEFENDER_NORM_X, BALL_NORM_X)  # F

        PLAYER_IS_OFFSIDE = is_attacking_team & (PLAYERS_NORM_X > X_OFFSIDE_LINE[:, np.newaxis]) & (PLAYERS_NORM_X > 0)

        if passers is not None:
            player_is_passer = passers[:, np.newaxis] == players[np.newaxis, :]  # F x P
            PLAYER_IS_OFFSIDE = PLAYER_IS_OFFSIDE & (~player_is_passer)  # F x P

        try:
            PLAYER_POS[PLAYER_IS_OFFSIDE, :] = np.nan
        except ValueError:
            warnings.warn("Offside not properly detectable, maybe too few defenders. Ignoring offside.")

    ### 1. Calculate ball trajectory
    # 1.1 Calculate spatial grid
    max_pass_length = np.sqrt((x_pitch_max - x_pitch_min) ** 2 + (y_pitch_max - y_pitch_min) ** 2) + radial_gridsize * 3  # T
    D_BALL_SIM = np.arange(pass_start_location_offset, max_pass_length + pass_start_location_offset + radial_gridsize, radial_gridsize)  # T

    # 1.2 Calculate temporal grid
    T_BALL_SIM = constant_velocity_time_to_arrive_1d(
        x=D_BALL_SIM[0], v=v0_grid[:, :, np.newaxis], x_target=D_BALL_SIM[np.newaxis, np.newaxis, :],
    )  # F x V0 x T
    T_BALL_SIM += time_offset_ball

    # 1.3 Calculate 2D points along ball trajectory
    cos_phi, sin_phi = np.cos(phi_grid), np.sin(phi_grid)  # F x PHI
    X_BALL_SIM = BALL_POS[:, 0][:, np.newaxis, np.newaxis] + cos_phi[:, :, np.newaxis] * D_BALL_SIM[np.newaxis, np.newaxis, :]  # F x PHI x T
    Y_BALL_SIM = BALL_POS[:, 1][:, np.newaxis, np.newaxis] + sin_phi[:, :, np.newaxis] * D_BALL_SIM[np.newaxis, np.newaxis, :]  # F x PHI x T

    ### 2 Calculate player interception rates
    # 2.1 Calculate time to arrive for each player along ball trajectory
    if use_approx_two_point:
        TTA_PLAYERS = approx_two_point_time_to_arrive(  # F x P x PHI x T
            x=PLAYER_POS[:, :, 0][:, :, np.newaxis, np.newaxis], y=PLAYER_POS[:, :, 1][:, :, np.newaxis, np.newaxis],
            vx=PLAYER_POS[:, :, 2][:, :, np.newaxis, np.newaxis], vy=PLAYER_POS[:, :, 3][:, :, np.newaxis, np.newaxis],
            x_target=X_BALL_SIM[:, np.newaxis, :, :], y_target=Y_BALL_SIM[:, np.newaxis, :, :],

            # Parameters
            use_max=use_max, velocity=player_velocity, keep_inertial_velocity=keep_inertial_velocity, v_max=v_max,
            a_max=a_max, inertial_seconds=inertial_seconds, tol_distance=tol_distance,
        )
    else:
        TTA_PLAYERS = constant_velocity_time_to_arrive(  # F x P x PHI x T
            x=PLAYER_POS[:, :, 0][:, :, np.newaxis, np.newaxis], y=PLAYER_POS[:, :, 1][:, :, np.newaxis, np.newaxis],
            x_target=X_BALL_SIM[:, np.newaxis, :, :], y_target=Y_BALL_SIM[:, np.newaxis, :, :],

            # Parameter
            player_velocity=player_velocity,
        )

    if exclude_passer:
        if passers is None:
            raise ValueError("'passers' must be provided if 'exclude_passer' is True")
        i_passers_to_exclude = np.array([list(players).index(passer) for passer in passers])
        i_frames = np.arange(TTA_PLAYERS.shape[0])
        TTA_PLAYERS[i_frames, i_passers_to_exclude, :, :] = np.inf  # F x P x PHI x T

    TTA_PLAYERS = np.nan_to_num(TTA_PLAYERS, nan=np.inf)  # Handle players not participating in the game by setting their TTA to infinity
    gc.collect()

    # 2.2 Transform time to arrive into interception rates
    TMP = TTA_PLAYERS[:, :, np.newaxis, :, :] - T_BALL_SIM[:, np.newaxis, :, np.newaxis, :]  # F x P x PHI x T - F x PHI x T = F x P x V0 x PHI x T
    with np.errstate(over='ignore'):  # overflow leads to inf which will be handled gracefully later
        TMP[:] = b0 + b1 * TMP  # 1 + 1 * F x P x V0 x PHI x T = F x P x V0 x PHI x T
    with np.errstate(invalid='ignore'):  # inf -> nan
        TMP[:] = _approximate_sigmoid(TMP) if use_efficient_sigmoid else _sigmoid(TMP)
    TMP = np.nan_to_num(TMP, nan=0)  # F x P x V0 x PHI x T, gracefully handle overflow
    DT = T_BALL_SIM[:, :, 1] - T_BALL_SIM[:, :, 0]  # F x V0
    ar_time = TMP / (factor * (v0_grid ** (-factor2))[:, np.newaxis, :, np.newaxis, np.newaxis])  # F x P x V0 x PHI x T
    del TMP
    gc.collect()

    ## 3. Use interception rates to calculate probabilities
    # 3.1 Sums of interception rates over players
    sum_ar = np.nansum(ar_time, axis=1) if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density", "attack_cum_prob", "defense_cum_prob", "player_cum_prob", "p0_density", "cum_p0"]) else None  # F x V0 x PHI x T
    player_is_attacking = (player_teams[np.newaxis, :] == passer_teams[:, np.newaxis]) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density", "attack_cum_prob", "defense_cum_prob", "attack_prob_density", "defense_prob_density"]) else None  # F x P
    sum_ar_att = np.nansum(np.where(player_is_attacking[:, :, np.newaxis, np.newaxis, np.newaxis], ar_time, 0), axis=1) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T
    sum_ar_def = np.nansum(np.where(~player_is_attacking[:, :, np.newaxis, np.newaxis, np.newaxis], ar_time, 0), axis=1) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T

    # 3.2 Integral of sum of interception rates
    int_sum_ar = scipy.integrate.cumulative_trapezoid(y=sum_ar, x=T_BALL_SIM[:, :, np.newaxis, :], initial=0, axis=-1) if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density", "attack_cum_prob", "defense_cum_prob", "player_cum_prob", "p0_density", "cum_p0"]) else None  # F x V0 x PHI x T
    int_sum_ar_att = scipy.integrate.cumulative_trapezoid(y=sum_ar_att, x=T_BALL_SIM[:, :, np.newaxis, :], initial=0, axis=-1) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T
    int_sum_ar_def = scipy.integrate.cumulative_trapezoid(y=sum_ar_def, x=T_BALL_SIM[:, :, np.newaxis, :], initial=0, axis=-1) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T

    # 3.3 Cumulative probability P0 from integrals
    cum_p0 = np.exp(-int_sum_ar) if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density", "attack_cum_prob", "defense_cum_prob", "player_cum_prob", "p0_density", "cum_p0"]) else None  # F x V0 x PHI x T, cumulative probability that no one intercepted
    cum_p0_only_att = np.exp(-int_sum_ar_att) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T
    cum_p0_only_def = np.exp(-int_sum_ar_def) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x V0 x PHI x T
    cum_p0_only_opp = np.where(
        player_is_attacking[:, :, np.newaxis, np.newaxis, np.newaxis],
        cum_p0_only_def[:, np.newaxis, :, :, :], cum_p0_only_att[:, np.newaxis, :, :, :]
    ) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x P x V0 x PHI x T

    # 3.4 Probability density from P0
    dpr_over_dt = cum_p0[:, np.newaxis, :, :, :] * ar_time if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density", "attack_cum_prob", "defense_cum_prob", "player_cum_prob", "cum_p0"]) else None  # if "prob" in ptypes else None  # F x P x V0 x PHI x T
    dp0_over_dt = -cum_p0 * sum_ar if _should_return_any_of(["p0_density"]) else None  # F x V0 x PHI x T
    dpr_poss_over_dt = cum_p0_only_opp * ar_time if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # if "poss" in ptypes else None  # F x P x V0 x PHI x T

    # 3.5 Cumulative probability
    pr_cum_prob = scipy.integrate.cumulative_trapezoid(  # F x P x V0 x PHI x T, cumulative probability that player P intercepted
        y=dpr_over_dt,  # F x P x V0 x PHI x T
        x=T_BALL_SIM[:, np.newaxis, :, np.newaxis, :],  # F x V0 x T
        initial=0, axis=-1,
    ) if _should_return_any_of(["attack_cum_prob", "defense_cum_prob", "player_cum_prob", "cum_p0"]) else None

    # 3.6. Go from dt -> dx
    DX = radial_gridsize  # ok because we use an equally spaced grid
    dpr_over_dx = dpr_over_dt * DT[:, np.newaxis, :, np.newaxis, np.newaxis] / DX if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density"]) else None  # F x P x V0 x PHI x T
    del dpr_over_dt
    gc.collect()
    dp0_over_dx = dp0_over_dt * DT[:, :, np.newaxis, np.newaxis] / DX if _should_return_any_of(["p0_density"]) else None  # F x V0 x PHI x T
    del dp0_over_dt
    gc.collect()
    dpr_poss_over_dx = dpr_poss_over_dt * DT[:, np.newaxis, :, np.newaxis, np.newaxis] / DX if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x P x V0 x PHI x T
    del dpr_poss_over_dt
    gc.collect()

    # 3.7 Aggregate over v0
    player_prob_density = (np.mean(dpr_over_dx, axis=2) if v0_prob_aggregation_mode == "mean" else np.max(dpr_over_dx, axis=2)) if _should_return_any_of(["attack_prob_density", "defense_prob_density", "player_prob_density"]) else None  # F x P x PHI x T, Take the average over all V0 in v0_grid
    p0_density = (np.mean(dp0_over_dx, axis=1) if v0_prob_aggregation_mode == "mean" else np.min(dp0_over_dx, axis=1)) if _should_return_any_of(["p0_density"]) else None  # F x PHI x T
    player_poss_density = np.max(dpr_poss_over_dx, axis=2) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x P x PHI x T, np.max not supported yet with numba using axis https://github.com/numba/numba/issues/1269

    cum_p0_vagg = (np.mean(cum_p0, axis=1) if v0_prob_aggregation_mode == "mean" else np.min(cum_p0, axis=1)) if _should_return_any_of(["cum_p0"]) or normalize and _should_return_any_of(["attack_cum_prob", "defense_cum_prob", "player_cum_prob"]) else None  # F x PHI x T
    pr_cum_prob_vagg = (np.mean(pr_cum_prob, axis=2) if v0_prob_aggregation_mode == "mean" else np.max(pr_cum_prob, axis=2)) if _should_return_any_of(["attack_cum_prob", "defense_cum_prob", "player_cum_prob", "cum_p0"]) else None  # F x P x PHI x T

    # 3.8 Normalize
    if normalize:
        # Normalize cumulative probability
        p_cum_sum = cum_p0_vagg + pr_cum_prob_vagg.sum(axis=1) if _should_return_any_of(["attack_cum_prob", "defense_cum_prob", "player_cum_prob", "cum_p0"]) else None  # F x PHI x T
        cum_p0_vagg = cum_p0_vagg / p_cum_sum if _should_return_any_of(["cum_p0"]) else None
        pr_cum_prob_vagg = pr_cum_prob_vagg / p_cum_sum[:, np.newaxis, :, :] if _should_return_any_of(["attack_cum_prob", "defense_cum_prob", "player_cum_prob"]) else None  # F x P x PHI x T

        # Normalize possibility density
        dpr_over_dx_vagg_poss_times_dx = player_poss_density * DX if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x P x PHI x T
        num_max = np.max(dpr_over_dx_vagg_poss_times_dx, axis=(1, 3)) if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x PHI
        with np.errstate(invalid='ignore'):
            player_poss_density = player_poss_density / num_max[:, np.newaxis, :, np.newaxis] if _should_return_any_of(["attack_cum_poss", "attack_poss_density", "defense_cum_poss", "defense_poss_density", "player_cum_poss", "player_poss_density"]) else None  # F x P x PHI x T

        # TODO: Normalization is hard because the prob-/possibilities are time-dependent AND need to be normalized w.r.t both the player- and the time-axis.

    # 3.9 Aggregate over players (Individual level -> Team level)
    attack_prob_density = np.nansum(np.where(player_is_attacking[:, :, np.newaxis, np.newaxis], player_prob_density, 0), axis=1) if _should_return_any_of(["attack_prob_density"]) else None  # F x PHI x T
    defense_prob_density = np.nansum(np.where(~player_is_attacking[:, :, np.newaxis, np.newaxis], player_prob_density, 0), axis=1) if _should_return_any_of(["defense_prob_density"]) else None  # F x PHI x T
    attack_poss_density = np.nanmax(np.where(player_is_attacking[:, :, np.newaxis, np.newaxis], player_poss_density, 0), axis=1) if _should_return_any_of(["attack_cum_poss", "attack_poss_density"]) else None  # F x PHI x T
    defense_poss_density = np.nanmax(np.where(~player_is_attacking[:, :, np.newaxis, np.newaxis], player_poss_density, 0), axis=1) if _should_return_any_of(["defense_cum_poss", "defense_poss_density"]) else None  # F x PHI x T
    attack_cum_prob = np.nansum(np.where(player_is_attacking[:, :, np.newaxis, np.newaxis], pr_cum_prob_vagg, 0), axis=1) if _should_return_any_of(["attack_cum_prob"]) else None  # F x PHI x T
    defense_cum_prob = np.nansum(np.where(~player_is_attacking[:, :, np.newaxis, np.newaxis], pr_cum_prob_vagg, 0), axis=1) if _should_return_any_of(["defense_cum_prob"]) else None  # F x PHI x T

    player_cum_poss = np.maximum.accumulate(player_poss_density, axis=-1) * radial_gridsize if _should_return_any_of(["player_cum_poss"]) else None  # TODO cleaner would be to move this earlier?
    attack_cum_poss = np.maximum.accumulate(attack_poss_density, axis=-1) * radial_gridsize if _should_return_any_of(["attack_cum_poss"]) else None  # possibility CDF uses cummax instead of cumsum to emerge from PDF
    defense_cum_poss = np.maximum.accumulate(defense_poss_density, axis=-1) * radial_gridsize if _should_return_any_of(["defense_cum_poss"]) else None

    result = SimulationResult(
        # Team-level prob-/possibilities (cumulative and densities) along simulated ball trajectories
        attack_cum_prob=attack_cum_prob,  # F x PHI x T
        attack_cum_poss=attack_cum_poss,  # F x PHI x T
        attack_prob_density=attack_prob_density,  # F x PHI x T
        attack_poss_density=attack_poss_density,  # F x PHI x T
        defense_cum_prob=defense_cum_prob,  # F x PHI x T
        defense_cum_poss=defense_cum_poss,  # F x PHI x T
        defense_prob_density=defense_prob_density,  # F x PHI x T
        defense_poss_density=defense_poss_density,  # F x PHI x T

        # Player-specific prob-/possibilities
        player_cum_prob=pr_cum_prob_vagg,  # F x P x PHI x T
        player_cum_poss=player_cum_poss,  # F x P x PHI x T
        player_prob_density=player_prob_density,  # F x P x PHI x T
        player_poss_density=player_poss_density,  # F x P x PHI x T

        # Complementary proability
        cum_p0=cum_p0_vagg,  # F x PHI x T
        p0_density=p0_density,  # F x PHI x T

        # Trajectory grids
        phi_grid=phi_grid,  # F x PHI
        r_grid=D_BALL_SIM,  # T
        x_grid=X_BALL_SIM,  # F x PHI x T
        y_grid=Y_BALL_SIM,  # F x PHI x T
    )

    # Set fields not to return to zero
    for field in _result_fields:
        if field in ["phi_grid", "r_grid", "x_grid", "y_grid"]:
            continue
        if field not in fields_to_return:
            result = result._replace(**{field: None})

    return result


def simulate_passes_chunked(
    # Input data
    PLAYER_POS,
    BALL_POS,
    phi_grid,
    v0_grid,
    passer_teams,
    player_teams,
    players=None,
    passers=None,  # F, frame-wise passer
    exclude_passer=False,
    playing_direction=None,
    respect_offside=False,
    x_pitch_min=-52.5, x_pitch_max=52.5, y_pitch_min=-34, y_pitch_max=34,

    # Options
    use_progress_bar=True,
    chunk_size=150,
    fields_to_return=ALL_OPTIONAL_FIELDS_TO_RETURN,

    # Model parameters
    pass_start_location_offset=_DEFAULT_PASS_START_LOCATION_OFFSET,
    time_offset_ball=_DEFAULT_TIME_OFFSET_BALL,
    radial_gridsize=_DEFAULT_RADIAL_GRIDSIZE,
    b0=_DEFAULT_B0,
    b1=_DEFAULT_B1,
    player_velocity=_DEFAULT_PLAYER_VELOCITY,
    keep_inertial_velocity=_DEFAULT_KEEP_INERTIAL_VELOCITY,
    use_max=_DEFAULT_USE_MAX,
    v_max=_DEFAULT_V_MAX,
    a_max=_DEFAULT_A_MAX,
    inertial_seconds=_DEFAULT_INERTIAL_SECONDS,
    tol_distance=_DEFAULT_TOL_DISTANCE,
    use_approx_two_point=_DEFAULT_USE_APPROX_TWO_POINT,
    v0_prob_aggregation_mode=_DEFAULT_V0_PROB_AGGREGATION_MODE,
    normalize=_DEFAULT_NORMALIZE,
    use_efficient_sigmoid=_DEFAULT_USE_EFFICIENT_SIGMOID,

    factor=_DEFAULT_FACTOR,
    factor2=_DEFAULT_FACTOR2,
) -> SimulationResult:
    """
    Execute pass simulation in chunks to avoid OOM.

    >>> res = simulate_passes_chunked(np.array([[[0, 0, 0, 0], [50, 0, 0, 0]]]), np.array([[0, 0]]), np.array([[0]]), np.array([[10]]), np.array([0]), np.array([0, 1]), players=np.array(["A", "B"]), passers=np.array(["A"]), radial_gridsize=15)
    >>> res.defense_poss_density.shape, res.defense_poss_density
    ((1, 1, 13), array([[[8.89786731e-05, 1.64897230e-04, 1.29669104e-03, 1.94280126e-01,
             1.91894891e-01, 1.88063562e-01, 1.77544360e-01, 3.89546322e-02,
             2.01864630e-03, 1.02515215e-04, 5.17596953e-06, 2.60590596e-07,
             1.30974323e-08]]]))
    """
    if chunk_size is None or chunk_size <= 0:
        chunk_size = PLAYER_POS.shape[0]
    _assert_matrix_consistency(PLAYER_POS, BALL_POS, phi_grid, v0_grid, passer_teams, player_teams, players, passers)

    F = PLAYER_POS.shape[0]

    i_chunks = list(range(0, F, chunk_size))

    full_result = None

    if use_progress_bar:
        i_chunks = progress_bar(i_chunks, desc="Simulating passes", total=len(i_chunks), unit="chunk")

    for chunk_nr, i in enumerate(i_chunks):
        i_chunk_end = min(i + chunk_size, F)

        PLAYER_POS_chunk = PLAYER_POS[i:i_chunk_end, ...]
        BALL_POS_chunk = BALL_POS[i:i_chunk_end, ...]
        phi_grid_chunk = phi_grid[i:i_chunk_end, ...]
        v0_grid_chunk = v0_grid[i:i_chunk_end, ...]
        passer_team_chunk = passer_teams[i:i_chunk_end, ...]
        if passers is not None:
            passers_chunk = passers[i:i_chunk_end, ...]
        else:
            passers_chunk = None
        if playing_direction is not None:
            playing_direction_chunk = playing_direction[i:i_chunk_end, ...]
        else:
            playing_direction_chunk = None

        result = simulate_passes(
            PLAYER_POS_chunk, BALL_POS_chunk, phi_grid_chunk, v0_grid_chunk, passer_team_chunk, player_teams, players,
            passers_chunk,
            exclude_passer,
            playing_direction_chunk,
            respect_offside,
            fields_to_return,
            x_pitch_min, x_pitch_max, y_pitch_min, y_pitch_max,
            pass_start_location_offset,
            time_offset_ball,
            radial_gridsize,
            b0,
            b1,
            player_velocity,
            keep_inertial_velocity,
            use_max,
            v_max,
            a_max,
            inertial_seconds,
            tol_distance,
            use_approx_two_point,
            v0_prob_aggregation_mode,
            normalize,
            use_efficient_sigmoid,
            factor,
            factor2,
        )

        if full_result is None:
            full_result = result
        else:
            full_p_cum = np.concatenate([full_result.attack_cum_prob, result.attack_cum_prob], axis=0) if full_result.attack_cum_prob is not None else None
            full_poss_cum = np.concatenate([full_result.attack_cum_poss, result.attack_cum_poss], axis=0) if full_result.attack_cum_poss is not None else None
            full_p_density = np.concatenate([full_result.attack_poss_density, result.attack_poss_density], axis=0) if full_result.attack_poss_density is not None else None
            full_prob_density = np.concatenate([full_result.attack_prob_density, result.attack_prob_density], axis=0) if full_result.attack_prob_density is not None else None
            full_p_cum_def = np.concatenate([full_result.defense_cum_prob, result.defense_cum_prob], axis=0) if full_result.defense_cum_prob is not None else None
            full_defense_cum_poss = np.concatenate([full_result.defense_cum_poss, result.defense_cum_poss], axis=0) if full_result.defense_cum_poss is not None else None
            full_p_density_def = np.concatenate([full_result.defense_poss_density, result.defense_poss_density], axis=0) if full_result.defense_poss_density is not None else None
            full_defense_prob_density = np.concatenate([full_result.defense_prob_density, result.defense_prob_density], axis=0) if full_result.defense_prob_density is not None else None
            full_cum_p0 = np.concatenate([full_result.cum_p0, result.cum_p0], axis=0) if full_result.cum_p0 is not None else None
            full_p0_density = np.concatenate([full_result.p0_density, result.p0_density], axis=0) if full_result.p0_density is not None else None
            full_phi = np.concatenate([full_result.phi_grid, result.phi_grid], axis=0) if full_result.phi_grid is not None else None
            full_x0 = np.concatenate([full_result.x_grid, result.x_grid], axis=0) if full_result.x_grid is not None else None
            full_y0 = np.concatenate([full_result.y_grid, result.y_grid], axis=0) if full_result.y_grid is not None else None
            full_player_prob_density = np.concatenate([full_result.player_prob_density, result.player_prob_density], axis=0) if full_result.player_prob_density is not None else None
            full_player_poss_density = np.concatenate([full_result.player_poss_density, result.player_poss_density], axis=0) if full_result.player_poss_density is not None else None
            full_player_cum_prob = np.concatenate([full_result.player_cum_prob, result.player_cum_prob], axis=0) if full_result.player_cum_prob is not None else None
            full_player_cum_poss = np.concatenate([full_result.player_cum_poss, result.player_cum_poss], axis=0) if full_result.player_cum_poss is not None else None
            full_result = SimulationResult(
                attack_cum_poss=full_poss_cum,
                attack_cum_prob=full_p_cum,
                attack_poss_density=full_p_density,
                attack_prob_density=full_prob_density,
                defense_cum_poss=full_defense_cum_poss,
                defense_cum_prob=full_p_cum_def,
                defense_poss_density=full_p_density_def,
                defense_prob_density=full_defense_prob_density,
                cum_p0=full_cum_p0,
                p0_density=full_p0_density,
                player_prob_density=full_player_prob_density,
                player_poss_density=full_player_poss_density,
                player_cum_prob=full_player_cum_prob,
                player_cum_poss=full_player_cum_poss,
                phi_grid=full_phi,
                r_grid=full_result.r_grid,
                x_grid=full_x0,
                y_grid=full_y0,
            )

    return full_result


def clip_simulation_result_to_pitch(
    simulation_result: SimulationResult, x_pitch_min=-52.5, x_pitch_max=52.5, y_pitch_min=-34, y_pitch_max=34,
) -> SimulationResult:
    """
    Set all data points that are outside the pitch to zero (e.g. for DAS computation)

    >>> res = simulate_passes(np.array([[[0, 0, 0, 0], [50, 0, 0, 0]]]), np.array([[0, 0]]), np.array([[0]]), np.array([[10]]), np.array([0]), np.array([0, 1]), players=np.array(["A", "B"]), passers=np.array(["A"]), radial_gridsize=15)
    >>> res.defense_poss_density
    array([[[8.89786731e-05, 1.64897230e-04, 1.29669104e-03, 1.94280126e-01,
             1.91894891e-01, 1.88063562e-01, 1.77544360e-01, 3.89546322e-02,
             2.01864630e-03, 1.02515215e-04, 5.17596953e-06, 2.60590596e-07,
             1.30974323e-08]]])
    >>> clip_simulation_result_to_pitch(res).defense_poss_density
    array([[[8.89786731e-05, 1.64897230e-04, 1.29669104e-03, 1.94280126e-01,
             0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
             0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
             0.00000000e+00]]])
    """
    x = simulation_result.x_grid
    y = simulation_result.y_grid

    if x_pitch_min > x_pitch_max:
        raise ValueError("x_pitch_min must be smaller than x_pitch_max")
    if y_pitch_min > y_pitch_max:
        raise ValueError("y_pitch_min must be smaller than y_pitch_max")

    on_pitch_mask = ((x >= x_pitch_min) & (x <= x_pitch_max) & (y >= y_pitch_min) & (y <= y_pitch_max))  # F x PHI x T

    for cumulative_field in ["attack_cum_prob", "attack_cum_poss", "defense_cum_prob", "defense_cum_poss", "cum_p0", "player_cum_prob", "player_cum_poss"]:
        cum_field_data = getattr(simulation_result, cumulative_field)
        if cum_field_data is None:
            continue

        on_pitch_mask_field = on_pitch_mask if len(cum_field_data.shape) == 3 else np.repeat(on_pitch_mask[:, np.newaxis, :, :], cum_field_data.shape[1], axis=1)

        start_value = 0 if cumulative_field != "cum_p0" else 1
        updated_cum = cum_field_data.copy()
        for i in range(cum_field_data.shape[-1]):
            updated_cum[..., i] = np.where(on_pitch_mask_field[..., i], cum_field_data[..., i], updated_cum[..., i-1] if i > 0 else start_value)
            if cumulative_field == "attack_cum_prob":
                if i > 0:
                    assert np.all(on_pitch_mask_field[..., i] | (updated_cum[..., i] == updated_cum[..., i-1]))

        simulation_result = simulation_result._replace(**{cumulative_field: updated_cum})

    density_replacement_value = 0
    simulation_result = simulation_result._replace(
        attack_prob_density=np.where(on_pitch_mask, simulation_result.attack_prob_density, density_replacement_value) if simulation_result.attack_prob_density is not None else None,
        attack_poss_density=np.where(on_pitch_mask, simulation_result.attack_poss_density, density_replacement_value) if simulation_result.attack_poss_density is not None else None,
        defense_prob_density=np.where(on_pitch_mask, simulation_result.defense_prob_density, density_replacement_value) if simulation_result.defense_prob_density is not None else None,
        defense_poss_density=np.where(on_pitch_mask, simulation_result.defense_poss_density, density_replacement_value) if simulation_result.defense_poss_density is not None else None,
        p0_density=np.where(on_pitch_mask, simulation_result.p0_density, density_replacement_value) if simulation_result.p0_density is not None else None,
        player_prob_density=np.where(on_pitch_mask[:, np.newaxis, :, :], simulation_result.player_prob_density, density_replacement_value) if simulation_result.player_prob_density is not None else None,
        player_poss_density=np.where(on_pitch_mask[:, np.newaxis, :, :], simulation_result.player_poss_density, density_replacement_value) if simulation_result.player_poss_density is not None else None,
    )
    return simulation_result


def integrate_surfaces(result: SimulationResult, x_pitch_min=-52.5, x_pitch_max=52.5, y_pitch_min=-34, y_pitch_max=34):
    """
    Integrate attacking possibility density in result to obtain surface area (AS/DAS)

    >>> res = simulate_passes(np.array([[[0, 0, 0, 0], [50, 0, 0, 0]]]), np.array([[0, 0]]), np.array([[0, 1*np.pi/3, 2*np.pi/3]]), np.array([[10, 10, 10]]), np.array([0]), np.array([0, 1]), radial_gridsize=15)
    >>> res.attack_poss_density
    array([[[1.03407896e-03, 4.34113430e-04, 5.27060765e-04, 1.51129699e-04,
             1.07173438e-05, 9.21090837e-07, 1.63818876e-07, 2.68226445e-07,
             1.35596313e-08, 6.79782508e-10, 3.40267229e-11, 1.70221067e-12,
             8.51279969e-14],
            [1.03407896e-03, 4.34208810e-04, 5.31611162e-04, 6.84624667e-04,
             9.50183615e-04, 3.61836440e-04, 6.51260823e-05, 1.07221499e-04,
             5.43985030e-06, 2.73437156e-07, 1.37154339e-08, 6.87289329e-10,
             3.44205118e-11],
            [1.03407896e-03, 4.34301416e-04, 5.32301463e-04, 6.87956371e-04,
             9.73593533e-04, 1.66948127e-03, 5.92149182e-03, 1.93318292e-01,
             1.94810292e-01, 1.94616189e-01, 1.94033526e-01, 1.93218568e-01,
             1.92180048e-01]]])
    >>> integrate_surfaces(res)
    Areas(attack_prob=array([10.74287034]), attack_poss=array([10.92307646]), defense_prob=array([224.5886554]), defense_poss=array([1002.23676372]), player_prob=array([[ 10.74287034, 224.5886554 ]]), player_poss=array([[  10.92307646, 1002.23676372]]))
    """
    result = clip_simulation_result_to_pitch(result, x_pitch_min, x_pitch_max, y_pitch_min, y_pitch_max)

    # 1. Get r-part of area elements
    r_grid = result.r_grid  # T

    r_lower_bounds = np.zeros_like(r_grid)  # Initialize with zeros
    r_lower_bounds[1:] = (r_grid[:-1] + r_grid[1:]) / 2  # Midpoint between current and previous element
    r_lower_bounds[0] = r_grid[0]  # Set lower bound for the first element

    r_upper_bounds = np.zeros_like(r_grid)  # Initialize with zeros
    r_upper_bounds[:-1] = (r_grid[:-1] + r_grid[1:]) / 2  # Midpoint between current and next element
    r_upper_bounds[-1] = r_grid[-1]  # Arbitrarily high upper bound for the last element

    dr = r_upper_bounds - r_lower_bounds  # T

    # 2. Get phi-part of area elements
    phi_grid = result.phi_grid  # F x PHI

    phi_lower_bounds = np.zeros_like(phi_grid)  # F x PHI
    phi_lower_bounds[:, 1:] = (phi_grid[:, :-1] + phi_grid[:, 1:]) / 2  # Midpoint between current and previous element
    phi_lower_bounds[:, 0] = phi_grid[:, 0]

    phi_upper_bounds = np.zeros_like(phi_grid)  # Initialize with zeros
    phi_upper_bounds[:, :-1] = (phi_grid[:, :-1] + phi_grid[:, 1:]) / 2  # Midpoint between current and next element
    phi_upper_bounds[:, -1] = phi_grid[:, -1]  # Arbitrarily high upper bound for the last element

    dphi = phi_upper_bounds - phi_lower_bounds  # F x PHI

    # 3. Calculate area elements
    outer_bound_circle_slice_area = dphi[:, :, np.newaxis]/(2*np.pi) * (np.pi * r_upper_bounds[np.newaxis, np.newaxis, :]**2)  # T
    inner_bound_circle_slice_area = dphi[:, :, np.newaxis]/(2*np.pi) * (np.pi * r_lower_bounds[np.newaxis, np.newaxis, :]**2)  # T
    dA = outer_bound_circle_slice_area - inner_bound_circle_slice_area  # F x PHI x T

    # 4. Calculate surface area
    Areas = collections.namedtuple("Areas", ["attack_prob", "attack_poss", "defense_prob", "defense_poss", "player_prob", "player_poss"])

    area_data = {}
    for attribute, team_field in [
        ("attack_prob", result.attack_prob_density),
        ("attack_poss", result.attack_poss_density),
        ("defense_prob", result.defense_prob_density),
        ("defense_poss", result.defense_poss_density),
    ]:
        if team_field is None:
            area_data[attribute] = None
        else:
            area_data[attribute] = np.sum(team_field * dr[np.newaxis, np.newaxis, :] * dA, axis=(1, 2))  # F x PHI x T

    for attribute, player_field in [
        ("player_prob", result.player_prob_density),
        ("player_poss", result.player_poss_density),
    ]:
        if player_field is None:
            area_data[attribute] = None
        else:
            probability_field = player_field * dr[np.newaxis, np.newaxis, np.newaxis, :] * dA[:, np.newaxis, :, :]
            area_data[attribute] = np.sum(probability_field, axis=(2, 3))  # F x P x PHI x T

    return Areas(**area_data)


def as_dangerous_result(result, danger, danger_weight):
    """
    Convert a simulation result to a dangerous simulation result by multiplying density with danger.

    >>> res = simulate_passes_chunked(np.array([[[0, 0, 0, 0], [50, 0, 0, 0]]]), np.array([[0, 0]]), np.array([[0]]), np.array([[10]]), np.array([0]), np.array([0, 1]), players=np.array(["A", "B"]), passers=np.array(["A"]), radial_gridsize=15)
    >>> res.defense_poss_density
    array([[[8.89786731e-05, 1.64897230e-04, 1.29669104e-03, 1.94280126e-01,
             1.91894891e-01, 1.88063562e-01, 1.77544360e-01, 3.89546322e-02,
             2.01864630e-03, 1.02515215e-04, 5.17596953e-06, 2.60590596e-07,
             1.30974323e-08]]])
    >>> danger = np.array([[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.0]]])
    >>> dangerous_res = as_dangerous_result(res, danger, danger_weight=1)
    >>> dangerous_res.defense_poss_density
    array([[[0.00000000e+00, 1.64897230e-05, 2.59338208e-04, 5.82840377e-02,
             7.67579563e-02, 9.40317808e-02, 1.06526616e-01, 2.72682426e-02,
             1.61491704e-03, 9.22636939e-05, 5.17596953e-06, 2.60590596e-07,
             1.30974323e-08]]])
    """
    def weighted_multiplication(_danger, _space, weight=danger_weight):
        return (_danger ** (1 / weight)) * _space if weight is not None else _danger * _space

    return result._replace(
        attack_cum_poss=None,
        attack_cum_prob=None,
        attack_poss_density=weighted_multiplication(danger, result.attack_poss_density) if result.attack_poss_density is not None else None,
        attack_prob_density=weighted_multiplication(danger, result.attack_prob_density) if result.attack_prob_density is not None else None,
        defense_cum_poss=None,
        defense_cum_prob=None,
        defense_poss_density=weighted_multiplication(danger, result.defense_poss_density) if result.defense_poss_density is not None else None,
        defense_prob_density=weighted_multiplication(danger, result.defense_prob_density) if result.defense_prob_density is not None else None,
        player_cum_prob=None,
        player_cum_poss=None,
        player_poss_density=weighted_multiplication(danger[:, np.newaxis, :, :], result.player_poss_density) if result.player_poss_density is not None else None,
        player_prob_density=weighted_multiplication(danger[:, np.newaxis, :, :], result.player_prob_density) if result.player_prob_density is not None else None,
    )
