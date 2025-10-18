import numpy as np
from prt_sim.gymnasium.image_pipeline import ImagePipeline

def test_image_pipeline_reset():
    env = ImagePipeline()
    obs, info = env.reset()
    assert isinstance(obs, np.ndarray)
    assert info == {}
    assert obs.shape == env.observation_space.shape
    assert obs.dtype == np.float32

def test_image_pipeline_final_reward():
    env = ImagePipeline(device='cuda')
    env.reset()
    reward = env._final_reward_function()
    assert isinstance(reward, float)
    assert 0.0 <= reward <= 1.0

def test_image_pipeline_reward():
    env = ImagePipeline(device='cuda')
    env.reset()

    reward = env._reward_function(env.current_image)
    assert isinstance(reward, float)
    assert 0.0 <= reward <= 1.0

def test_image_pipeline_step():
    env = ImagePipeline(device='cuda')
    env.reset()
    action = {"algorithm": 1, "parameters": np.array([0.0, 0.0, 0.0, 0.0, 0.0])}
    obs, reward, terminated, truncated, info = env.step(action)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == env.observation_space.shape
    assert obs.dtype == np.float32
    assert isinstance(reward, float)
    assert 0.0 <= reward <= 1.0
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert info == {}

def test_image_pipeline_truncated():
    env = ImagePipeline(device='cuda', max_steps=2)
    env.reset()
    action = env.action_space.sample()

    # Artificially set step count to max_steps
    env.steps = 20
    obs, reward, terminated, truncated, info = env.step(action)
    assert truncated == True
    assert reward == -100

def test_image_pipeline_terminated():
    env = ImagePipeline(device='cuda')
    env.reset()
    action = {"algorithm": 0, "parameters": np.array([0.0, 0.0, 0.0, 0.0, 0.0])}
    obs, reward, terminated, truncated, info = env.step(action)
    assert terminated == True
    assert truncated == False
    assert 0.0 <= reward <= 1.0