"""
Reinforcement Learning agents for adaptive fire-response dispatch routing.

Agents implemented:
  - DQNAgent  : Deep Q-Network                      (Mnih et al., 2015)
  - PPOAgent  : Proximal Policy Optimisation         (Schulman et al., 2017)
  - DDPGAgent : Deep Deterministic Policy Gradient   (Lillicrap et al., 2016)
  - A3CAgent  : Asynchronous Advantage Actor-Critic  (Mnih et al., 2016)

DQN, PPO, and DDPG use Stable-Baselines3 with Gymnasium environments.
A3C is implemented from scratch with PyTorch multiprocessing since SB3 does
not include an A3C implementation.
"""

from __future__ import annotations

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.multiprocessing as mp
import numpy as np
import gymnasium as gym
from stable_baselines3 import DQN, PPO, DDPG
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise
from typing import Optional


# ── Shared Actor-Critic Network (used by A3C) ─────────────────────────────────

class ActorCritic(nn.Module):
    """Shared backbone with separate policy (actor) and value (critic) heads."""

    def __init__(self, obs_dim: int, action_dim: int, hidden: int = 256):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.actor = nn.Linear(hidden, action_dim)   # logits
        self.critic = nn.Linear(hidden, 1)           # state value V(s)

    def forward(self, x):
        h = self.shared(x)
        return self.actor(h), self.critic(h)

    def get_action(self, obs: np.ndarray):
        obs_t = torch.FloatTensor(obs).unsqueeze(0)
        logits, value = self(obs_t)
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action.item(), log_prob, value.squeeze()


# ── DQN Agent ─────────────────────────────────────────────────────────────────

class DQNAgent:
    """
    Deep Q-Network agent wrapping Stable-Baselines3 DQN.

    Suitable for discrete action spaces, e.g., choosing among candidate
    next waypoints on the road graph.

    Args:
        env_id:          Gymnasium environment ID (or a gym.Env instance).
        model_path:      Path to save/load model checkpoints.
        learning_rate:   Optimizer learning rate.
        buffer_size:     Replay buffer capacity.
        batch_size:      Mini-batch size for gradient updates.
        gamma:           Discount factor.
        exploration_fraction: Fraction of training where ε decays.
        target_update_interval: Steps between target network syncs.
        verbose:         SB3 verbosity level (0 = silent, 1 = info).
    """

    def __init__(
        self,
        env_id: str = "DispatchRouting-v0",
        model_path: str = "checkpoints/dqn_dispatch",
        learning_rate: float = 1e-4,
        buffer_size: int = 100_000,
        batch_size: int = 64,
        gamma: float = 0.99,
        exploration_fraction: float = 0.2,
        target_update_interval: int = 1000,
        verbose: int = 1,
    ):
        self.env_id = env_id
        self.model_path = model_path
        self._model: Optional[DQN] = None

        self._kwargs = dict(
            policy="MlpPolicy",
            learning_rate=learning_rate,
            buffer_size=buffer_size,
            batch_size=batch_size,
            gamma=gamma,
            exploration_fraction=exploration_fraction,
            target_update_interval=target_update_interval,
            verbose=verbose,
        )

    def build(self, env: Optional[gym.Env] = None):
        env = env or gym.make(self.env_id)
        self._model = DQN(env=env, **self._kwargs)
        return self

    def train(self, total_timesteps: int = 500_000):
        callbacks = [
            CheckpointCallback(save_freq=10_000, save_path=os.path.dirname(self.model_path)),
            EvalCallback(self._model.get_env(), best_model_save_path=self.model_path, eval_freq=5_000),
        ]
        self._model.learn(total_timesteps=total_timesteps, callback=callbacks)

    def predict(self, obs: np.ndarray, deterministic: bool = True):
        return self._model.predict(obs, deterministic=deterministic)

    def save(self):
        self._model.save(self.model_path)

    def load(self, env: Optional[gym.Env] = None):
        env = env or gym.make(self.env_id)
        self._model = DQN.load(self.model_path, env=env)
        return self


# ── PPO Agent ─────────────────────────────────────────────────────────────────

class PPOAgent:
    """
    Proximal Policy Optimisation agent wrapping Stable-Baselines3 PPO.

    PPO is well-suited for the dispatch routing problem: it handles both
    discrete (waypoint selection) and continuous (speed profile) action spaces
    and is stable in on-policy training across vectorised SUMO environments.

    Args:
        env_id:        Gymnasium environment ID.
        model_path:    Path to save/load model checkpoints.
        n_envs:        Number of parallel environments for on-policy rollouts.
        n_steps:       Steps per rollout per environment.
        batch_size:    PPO mini-batch size.
        n_epochs:      Gradient update epochs per rollout.
        learning_rate: Optimizer learning rate.
        clip_range:    PPO clipping parameter ε.
        gamma:         Discount factor.
        gae_lambda:    GAE λ for advantage estimation.
        ent_coef:      Entropy bonus coefficient (encourages exploration).
        verbose:       SB3 verbosity level.
    """

    def __init__(
        self,
        env_id: str = "DispatchRouting-v0",
        model_path: str = "checkpoints/ppo_dispatch",
        n_envs: int = 4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        learning_rate: float = 3e-4,
        clip_range: float = 0.2,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        ent_coef: float = 0.01,
        verbose: int = 1,
    ):
        self.env_id = env_id
        self.model_path = model_path
        self.n_envs = n_envs
        self._model: Optional[PPO] = None

        self._kwargs = dict(
            policy="MlpPolicy",
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            learning_rate=learning_rate,
            clip_range=clip_range,
            gamma=gamma,
            gae_lambda=gae_lambda,
            ent_coef=ent_coef,
            verbose=verbose,
        )

    def build(self, env: Optional[gym.Env] = None):
        vec_env = env or make_vec_env(self.env_id, n_envs=self.n_envs)
        self._model = PPO(env=vec_env, **self._kwargs)
        return self

    def train(self, total_timesteps: int = 1_000_000):
        callbacks = [
            CheckpointCallback(save_freq=20_000, save_path=os.path.dirname(self.model_path)),
            EvalCallback(self._model.get_env(), best_model_save_path=self.model_path, eval_freq=10_000),
        ]
        self._model.learn(total_timesteps=total_timesteps, callback=callbacks)

    def predict(self, obs: np.ndarray, deterministic: bool = True):
        return self._model.predict(obs, deterministic=deterministic)

    def save(self):
        self._model.save(self.model_path)

    def load(self, env: Optional[gym.Env] = None):
        vec_env = env or make_vec_env(self.env_id, n_envs=1)
        self._model = PPO.load(self.model_path, env=vec_env)
        return self


# ── DDPG Agent ────────────────────────────────────────────────────────────────

class DDPGAgent:
    """
    Deep Deterministic Policy Gradient agent wrapping Stable-Baselines3 DDPG.

    Best suited for continuous action spaces, e.g., continuous speed/priority
    scoring over candidate route segments.

    Args:
        env_id:            Gymnasium environment ID.
        model_path:        Path to save/load model checkpoints.
        action_noise_sigma: Standard deviation for Ornstein-Uhlenbeck / Normal
                            action exploration noise.
        learning_rate:     Optimizer learning rate (actor and critic share it).
        buffer_size:       Replay buffer size.
        batch_size:        Mini-batch size.
        gamma:             Discount factor.
        tau:               Soft target network update rate.
        verbose:           SB3 verbosity level.
    """

    def __init__(
        self,
        env_id: str = "DispatchRoutingContinuous-v0",
        model_path: str = "checkpoints/ddpg_dispatch",
        action_noise_sigma: float = 0.1,
        learning_rate: float = 1e-4,
        buffer_size: int = 200_000,
        batch_size: int = 256,
        gamma: float = 0.99,
        tau: float = 0.005,
        verbose: int = 1,
    ):
        self.env_id = env_id
        self.model_path = model_path
        self.action_noise_sigma = action_noise_sigma
        self._model: Optional[DDPG] = None

        self._kwargs = dict(
            policy="MlpPolicy",
            learning_rate=learning_rate,
            buffer_size=buffer_size,
            batch_size=batch_size,
            gamma=gamma,
            tau=tau,
            verbose=verbose,
        )

    def build(self, env: Optional[gym.Env] = None):
        env = env or gym.make(self.env_id)
        n_actions = env.action_space.shape[0]
        noise = NormalActionNoise(
            mean=np.zeros(n_actions),
            sigma=self.action_noise_sigma * np.ones(n_actions),
        )
        self._model = DDPG(env=env, action_noise=noise, **self._kwargs)
        return self

    def train(self, total_timesteps: int = 500_000):
        callbacks = [
            CheckpointCallback(save_freq=10_000, save_path=os.path.dirname(self.model_path)),
            EvalCallback(self._model.get_env(), best_model_save_path=self.model_path, eval_freq=5_000),
        ]
        self._model.learn(total_timesteps=total_timesteps, callback=callbacks)

    def predict(self, obs: np.ndarray, deterministic: bool = True):
        return self._model.predict(obs, deterministic=deterministic)

    def save(self):
        self._model.save(self.model_path)

    def load(self, env: Optional[gym.Env] = None):
        env = env or gym.make(self.env_id)
        self._model = DDPG.load(self.model_path, env=env)
        return self


# ── A3C Agent ─────────────────────────────────────────────────────────────────

def _a3c_worker(
    rank: int,
    global_model: ActorCritic,
    optimizer,
    env_id: str,
    max_episodes: int,
    gamma: float,
    results_queue: mp.Queue,
):
    """Worker process: collects trajectories and updates the shared global model."""
    torch.manual_seed(rank)
    env = gym.make(env_id)
    local_model = ActorCritic(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.n,
    )

    for episode in range(max_episodes):
        local_model.load_state_dict(global_model.state_dict())

        obs, _ = env.reset()
        done = False
        log_probs, values, rewards = [], [], []

        while not done:
            action, log_prob, value = local_model.get_action(obs)
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            log_probs.append(log_prob)
            values.append(value)
            rewards.append(reward)

        # Compute returns and advantages
        returns = []
        R = 0.0
        for r in reversed(rewards):
            R = r + gamma * R
            returns.insert(0, R)
        returns_t = torch.FloatTensor(returns)
        values_t = torch.stack(values).squeeze()
        log_probs_t = torch.stack(log_probs)

        advantages = returns_t - values_t.detach()
        actor_loss = -(log_probs_t * advantages).mean()
        critic_loss = F.mse_loss(values_t, returns_t)
        entropy = -(torch.exp(log_probs_t) * log_probs_t).mean()
        loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy

        optimizer.zero_grad()
        loss.backward()
        # Copy gradients to global model
        for local_p, global_p in zip(local_model.parameters(), global_model.parameters()):
            if local_p.grad is not None:
                global_p._grad = local_p.grad
        optimizer.step()

        total_reward = sum(rewards)
        results_queue.put((rank, episode, total_reward))

    env.close()


class A3CAgent:
    """
    Asynchronous Advantage Actor-Critic (A3C) with shared global model.

    Multiple worker processes each run their own environment instance and
    asynchronously push gradient updates to the shared global network.
    This improves sample diversity and training stability without a replay buffer.

    Args:
        env_id:       Gymnasium environment ID (must be discrete action space).
        model_path:   Path to save/load the global model.
        obs_dim:      Observation space dimensionality.
        action_dim:   Number of discrete actions.
        hidden:       Hidden layer size for the shared ActorCritic.
        num_workers:  Number of parallel worker processes.
        max_episodes: Episodes per worker.
        gamma:        Discount factor.
        learning_rate: Global optimizer learning rate.
    """

    def __init__(
        self,
        env_id: str = "DispatchRouting-v0",
        model_path: str = "checkpoints/a3c_dispatch.pt",
        obs_dim: int = 64,
        action_dim: int = 8,
        hidden: int = 256,
        num_workers: int = 4,
        max_episodes: int = 1000,
        gamma: float = 0.99,
        learning_rate: float = 1e-4,
    ):
        self.env_id = env_id
        self.model_path = model_path
        self.num_workers = num_workers
        self.max_episodes = max_episodes
        self.gamma = gamma

        self.global_model = ActorCritic(obs_dim, action_dim, hidden)
        self.global_model.share_memory()
        self.optimizer = torch.optim.Adam(self.global_model.parameters(), lr=learning_rate)

    def train(self):
        results_queue: mp.Queue = mp.Queue()
        workers = [
            mp.Process(
                target=_a3c_worker,
                args=(
                    rank,
                    self.global_model,
                    self.optimizer,
                    self.env_id,
                    self.max_episodes,
                    self.gamma,
                    results_queue,
                ),
            )
            for rank in range(self.num_workers)
        ]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        return results_queue

    def predict(self, obs: np.ndarray):
        action, _, _ = self.global_model.get_action(obs)
        return action

    def save(self):
        torch.save(self.global_model.state_dict(), self.model_path)

    def load(self):
        state = torch.load(self.model_path, map_location="cpu")
        self.global_model.load_state_dict(state)
        return self
