import gym
import numpy as np
from tools.get_task import get_task_eval, get_task_tr, get_task_eval_fail, get_task_tr_fail, get_task_eval_FDD


def d2r(num):
    return num * np.pi / 180.0


def r2d(num):
    return num * 180 / np.pi


def map_to(num: np.ndarray, a, b):
    """ Map linearly num on the [-1, 1] range to the [a, b] range"""
    return ((num + 1.0) / 2.0) * (b - a) + a


class Citation(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['graph']}

    def __init__(self, evaluation=False, failure=None, FDD=False):

        super(Citation, self).__init__()

        self.evaluation = evaluation
        if failure is not None:

            self.failure_input = failure
            if self.failure_input[0] == 'de':
                import envs.elevatorrange._citation as C_MODEL
            elif self.failure_input[0] == 'da':
                import envs.aileroneff._citation as C_MODEL
            elif self.failure_input[0] == 'dr':
                import envs.rudderstuck._citation as C_MODEL
            elif self.failure_input[0] == 'cg':
                import envs.cgshift._citation as C_MODEL
            elif self.failure_input[0] == 'ice':
                import envs.icing._citation as C_MODEL
            elif self.failure_input[0] == 'ht':
                import envs.horztailbreaks._citation as C_MODEL
            elif self.failure_input[0] == 'vt':
                import envs.verttailbreaks._citation as C_MODEL
            else:
                raise ValueError(f"Failure type not recognized.")

            if self.evaluation:
                if FDD: self.task_fun = get_task_eval_FDD
                else: self.task_fun = get_task_eval_fail
            else:
                self.task_fun = get_task_tr_fail

        else:
            import envs.normal._citation as C_MODEL
            self.failure_input = ['', 0.0, 0.0]
            if self.evaluation: self.task_fun = get_task_eval
            else: self.task_fun = get_task_tr

        self.C_MODEL = C_MODEL
        self.time = self.task_fun()[3]
        self.dt = self.time[1] - self.time[0]
        self.ref_signal = self.task_fun()[0]
        self.track_indices = self.task_fun()[1]
        self.obs_indices = self.task_fun()[2]

        if self.evaluation:
            self.sideslip_factor = 4.0 * np.ones(self.time.shape[0])
        else:
            self.sideslip_factor = 10.0 * np.ones(self.time.shape[0])

        self.pitch_factor = np.ones(self.time.shape[0])
        if self.failure_input[0] == 'dr':
            self.sideslip_factor = np.zeros(self.time.shape[0])
            if FDD:
                self.sideslip_factor[:int(self.time.shape[0]/2)] = 4.0 * np.ones(int(self.time.shape[0]/2))
        # elif self.failure_input[0] == 'ht':
        #     self.pitch_factor = np.zeros(self.time.shape[0])
        #     if FDD:
        #         self.pitch_factor[:int(self.time.shape[0]/2)] = np.ones(int(self.time.shape[0]/2))
        elif self.failure_input[0] == 'da' and self.evaluation:
            self.pitch_factor = 1.5*np.ones(self.time.shape[0])
            if FDD:
                self.pitch_factor[:int(self.time.shape[0]/2)] = np.ones(int(self.time.shape[0]/2))

        elif self.failure_input[0] == 'ice':
            self.ref_signal = self.task_fun(theta_angle=-25)[0]

        # self.observation_space = gym.spaces.Box(-100, 100, shape=(len(self.obs_indices) + 3 + 2,), dtype=np.float64)
        self.observation_space = gym.spaces.Box(-100, 100, shape=(len(self.obs_indices) + 3 ,), dtype=np.float64)
        self.action_space = gym.spaces.Box(-1., 1., shape=(3,), dtype=np.float64)
        self.current_deflection = np.zeros(3)

        self.state = None
        self.scale_s = None
        self.state_history = None
        self.action_history = None
        self.error = None
        self.step_count = None

    def step(self, action_rates: np.ndarray):

        self.current_deflection = self.bound_a(self.current_deflection + self.scale_a(action_rates)*self.dt)
        if self.sideslip_factor[self.step_count - 1] == 0.0: self.current_deflection[2]= 0.0

        if self.time[self.step_count] < 5.0 and self.evaluation:
            self.state = self.C_MODEL.step(
                np.hstack([d2r(self.current_deflection), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, self.failure_input[1]]))
        else:
            self.state = self.C_MODEL.step(
                np.hstack([d2r(self.current_deflection), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, self.failure_input[2]]))

        self.error = d2r(self.ref_signal[:, self.step_count]) - self.state[self.track_indices]
        self.error[self.track_indices.index(5)] *= self.sideslip_factor[self.step_count]
        self.error[self.track_indices.index(7)] *= self.pitch_factor[self.step_count]

        self.state_history[:, self.step_count] = self.state*self.scale_s
        self.action_history[:, self.step_count] = self.current_deflection

        self.step_count += 1
        done = bool(self.step_count >= self.time.shape[0])
        if np.isnan(self.state).sum() > 0:
            print(self.state_history[:, self.step_count-2])
            # exit()
        if self.state[9] <= 50.0 or self.state[9] >= 1e4 or np.greater(np.abs(r2d(self.state[:3])), 1e4).any():
            return np.zeros(self.observation_space.shape), -1 * self.time.shape[0], True, {'is_success': False}

        return self.get_obs(), self.get_reward(), done, {'is_success': True}

    def reset(self):

        self.reset_soft()
        self.ref_signal = self.task_fun()[0]
        return np.zeros(self.observation_space.shape)

    def reset_soft(self):

        self.C_MODEL.initialize()
        action_trim = np.array(
            [-0.024761262011031245, 1.3745996716698875e-14, -7.371050575286063e-14, 0., 0., 0., 0., 0.,
             0.38576210972746433, 0.38576210972746433, self.failure_input[1]])
        self.state = self.C_MODEL.step(action_trim)
        self.scale_s = np.ones(self.state.shape)
        self.scale_s[[0, 1, 2, 4, 5, 6, 7, 8]] = 180 / np.pi
        self.state_history = np.zeros((self.state.shape[0], self.time.shape[0]))
        self.action_history = np.zeros((self.action_space.shape[0], self.time.shape[0]))
        self.error = np.zeros(len(self.track_indices))
        self.step_count = 0
        self.current_deflection = np.zeros(3)
        return np.zeros(self.observation_space.shape)

    def get_reward(self):

        max_bound = np.ones(self.error.shape)
        reward_vec = np.abs(np.maximum(np.minimum(r2d(self.error / 30), max_bound), -max_bound))
        # reward_vec = 0.5*np.exp(-np.absolute(self.error)*1000)
        reward = -reward_vec.sum() / self.error.shape[0]
        return reward

    def get_obs(self):

        untracked_obs_index = np.setdiff1d(self.obs_indices, self.track_indices)
        # return np.hstack([self.error[:2], 0.0, self.state[untracked_obs_index], self.current_deflection[:2], 0.0])
        return np.hstack([self.error, self.state[untracked_obs_index],  self.current_deflection])

    @staticmethod
    def scale_a(action_unscaled: np.ndarray) -> np.ndarray:
        """Min-max un-normalization from [-1, 1] action space to actuator limits"""

        max_bound = np.array([15, 40, 20])
        action_scaled = map_to(action_unscaled, -max_bound, max_bound)

        return action_scaled

    @staticmethod
    def bound_a(action):

        min_bounds = np.array([-20.05, -37.24, -21.77])
        max_bounds = np.array([14.9, 37.24, 21.77])
        return np.minimum(np.maximum(action, min_bounds), max_bounds)

    def render(self, mode='any'):
        raise NotImplementedError()

    def close(self):
        self.C_MODEL.terminate()
        return

# from stable_baselines.common.env_checker import check_env
#
# envs = Citation()
#
# # Box(4,) means that it is a Vector with 4 components
# print("Observation space:", envs.observation_space.shape)
# print("Action space:", envs.action_space)
#
# check_env(envs, warn=True)
