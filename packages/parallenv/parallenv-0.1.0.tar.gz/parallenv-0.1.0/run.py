import gymnasium as gym
from  gymnasium.vector import AsyncVectorEnv


import time

if __name__ == "__main__":
    num_envs = 64
    env_fns = [lambda: gym.make("CartPole-v1") for _ in range(num_envs)]
    envs = AsyncVectorEnv(env_fns)
    def policy():
        time.sleep(0.03)
        return envs.action_space.sample()
    observation, info = envs.reset()

    for i in range(100):
        actions = policy()
        observation, reward, terminated, truncated, info = envs.step(actions)
        # No more resets are required since `next_step` autoreset is set by default.
    envs.close()
