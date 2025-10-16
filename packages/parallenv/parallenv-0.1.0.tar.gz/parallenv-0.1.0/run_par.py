# import gymnasium as gym
# from parallenv import ParallEnv

# import time

# if __name__ == "__main__":
#     batch_size = 16
#     num_envs = 64
#     env_fns = [lambda: gym.make("CartPole-v1") for _ in range(num_envs)]    
#     envs = ParallEnv(
#         env_fns,
#         batch_size=batch_size,
#         num_workers=4,
#     )
#     def policy():
#         time.sleep(0.01)
#         return envs.action_space.sample()

#     envs.reset()
#     for i in range(100):
#         ids, observation, reward, terminated, truncated, info = envs.gather()
#         # No more resets are required since `next_step` autoreset is set by default.
#         actions = policy()

#         envs.step(ids, actions)
#     envs.close()
import functools

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from parallenv import ParallEnv

class IdEnv(gym.Env):
    def __init__(self, id: int):
        self.id = id
        self.observation_space = spaces.Box(1, 1)
        self.action_space = spaces.Box(1, 1)

    def step(self, action):
        return np.array((0,)), 0, False, False, {"env_id": self.id}

    def reset(
        self,
        *,
        seed = None,
        options = None,
    ):
        """Resets the environment."""
        super().reset(seed=seed, options=options)
        return  np.array((0,)), {"env_id": self.id}


env_fns = [functools.partial(IdEnv, i) for i in range(4)]

observations = create_empty_array(
    self.single_observation_space, n=len(id_buffer), fn=np.zeros
)


separate_envs 
envs = ParallEnv(
    env_fns=env_fns,
    batch_size=4,
    num_workers=4,
)
envs.reset()
print("reseted")
ids, observation, reward, terminated, truncated, info = envs.gather()
envs.close()
print(info["env_id"])
