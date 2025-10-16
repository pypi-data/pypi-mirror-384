import numpy as np
import gymnasium as gym
from gymnasium import spaces
from itertools import accumulate
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from typing import Any, Dict, List, Optional, Tuple
from prt_sim.gymnasium.toolbox import Toolbox
from prt_datasets.detection import BDD100KDataset
from prt_nn.detection import YoloDetector, DetectorInterface

class ImagePipeline(gym.Env):
    """
    A template Gymnasium environment that simulates an image-processing pipeline.

    This environment uses a single fixed task algorithm (Yolo object detector) and the actions produce a dynamic preprocessing pipeline.

    Observation:
        A grayscale (H, W, 1) or RGB (H, W, 3) uint8 image
    Action:
        Discrete(K) - select which processing operation to apply (placeholder)
    Termination:
        Fixed horizon or an internal condition (customize in step)
    Truncation:
        Ends when a max step count is reached
    Render modes:
        - 'rgb_array' returns the current image as an np.ndarray
        - 'human' (optional): implement if you want a GUI viewer
    """

    metadata = {"render_modes": ["rgb_array"], "render_fps": 30}

    def __init__(
        self,
        dataset_root: Path | None = None,
        num_image_samples: int = 1,
        max_steps: int = 20,
        device: torch.device = torch.device("cpu"),
    ) -> None:
        super().__init__()
        self.dataset_root = dataset_root
        self.num_image_samples = num_image_samples
        self.max_steps = max_steps
        self.device = device
        self.current_image = None
        self.steps = 0
        self.current_target = None

        # Get the Algorithm Toolbox information
        self.toolbox = Toolbox()

        # Define action space as a discrete choice among algorithms and a maximum number of parameters scaled between 0 and 1
        self.action_space = spaces.Dict({
            "algorithm": spaces.Discrete(self.toolbox.get_num_algorithms()),
            "parameters": spaces.Box(low=0.0, high=1.0, shape=(self.toolbox.get_num_parameters(),))  
        })  

        self._configure_task()

        # Define Observation space: Pixel space 
        self._configure_dataset()
        image_shape = self.train_dataset[0][0].shape
        self.observation_space = spaces.Box(
            low=0,
            high=1,
            shape=image_shape,  # CxHxW
            dtype=np.float32,
        )


    def _configure_dataset(self) -> None:
        """
        Configure the dataset and dataloaders
        """
        # Make sure the dataset is downloaded
        BDD100KDataset.download(self.dataset_root)

        # Load the dataset and create dataloader
        self.train_dataset = BDD100KDataset(root=self.dataset_root, split="train")
        self.eval_dataset = BDD100KDataset(root=self.dataset_root, split="val")

        # Use generator to ensure reproducibility when a seed is provided
        self.generator = torch.Generator()

        self.train_data_loader = DataLoader(
            self.train_dataset,
            batch_size=self.num_image_samples,
            shuffle=True,
            generator=self.generator,
        )
        self.eval_data_loader = DataLoader(
            self.eval_dataset,
            batch_size=1,
            shuffle=False,
        )

    def _configure_task(self) -> None:
        """
        Configure the task algorithm and interface
        """
        # Configure the object detector
        self.detector = YoloDetector(device=self.device)
        self.task_interface = DetectorInterface(self.detector)

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
              ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to an initial state and returns an initial observation.
        
        Args:
            seed (Optional[int]): The seed that is used to initialize the environment's random number generator
            options (Optional[Dict[str, Any]]): Additional information to specify how the environment is reset. This is not used in this environment.
        Returns:
            observation (np.ndarray): The initial observation of the space.
            info (dict): A dictionary containing auxiliary information about the reset.
        """
        super().reset(seed=seed)
        # Reset the generator if a seed is provided. This will result in the same starting image each time
        if seed is not None:
            self.generator.manual_seed(seed)

        self.steps = 0

        # Load the next batch of images and targets
        # Image has shape BCHW in [0,1] and target is dictionary with 'boxes', 'labels', 'image_id'
        image, target = next(iter(self.train_data_loader))
        self.current_image = image.squeeze(0).to(self.device)  # Use only the first image in the batch
        self.current_target = {k: v.squeeze(0).to(self.device) for k, v in target.items()}

        # Convert from Tensor with shape CHW -> Numpy with shape CHW
        state = self.current_image.cpu().numpy()

        return state, {}


    def step(self, action: Dict[str, Any]) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Run one timestep of the environment's dynamics. When end of episode is reached, you are responsible for calling `reset()` to reset this environment's state.
        
        Args:
            action (dict): An action provided by the agent. This is a dictionary with keys 
                "algorithm": int - the index of the algorithm to apply
                "parameters": np.ndarray - the parameters for the algorithm scaled between 0 and 1
        Returns:
            observation (np.ndarray): Agent's observation of the current environment
            reward (float): Amount of reward returned after previous action
            terminated (bool): Whether the episode has ended. Further step() calls will return undefined results
            truncated (bool): Whether the episode was truncated (max steps reached). Further step() calls will return undefined results
            info (dict): Contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        """
        
        terminated = False
        truncated = False
        info = {}

        # Extract the algorithm and parameters from the action dictionary
        algorithm, all_params = action["algorithm"], action["parameters"]

        # If the done action is chosen, evaluate the terminal reward on the current image
        if algorithm == 0:
            next_state = self.current_image
            reward = self._final_reward_function()
            terminated = True
        else:
            next_state = self.toolbox.apply_algorithm(choice=torch.tensor(algorithm), params=all_params, image=self.current_image.unsqueeze(0)).squeeze(0)
            reward = self._reward_function(next_state)

            # Image produced by the algorithm becomes the next state
            self.current_image = next_state

        # The episode ends if the policy chooses to run the task algorithm or max steps reached
        self.steps += 1

        # If the maximum number of steps is reached, truncate the episode and give a large negative reward
        if self.steps >= self.max_steps and not terminated:
            truncated = True
            reward = -100

        return next_state.cpu().numpy(), reward, terminated, truncated, info

    def render(self) -> Optional[np.ndarray]:
        """
        Rendering is not supported in this environment
        """
        pass

    def close(self) -> None:
        """
        There is nothing to close in this environment
        """
        pass

    def _reward_function(self, next_state: torch.Tensor) -> float:
        """
        The intermediate reward computes the F1 score for the current image after applying the processing algorithm
        
        Args:
            next_state (torch.Tensor): The current image after applying the processing algorithm [C,H,W] in [0,1]
        Returns:
            float: The F1 score for the current image
        """
        prediction = self.task_interface.detect(next_state.unsqueeze(0))
        metric = self.task_interface.evaluate_image(prediction[0], self.current_target)
        return metric.f1

    def _final_reward_function(self) -> float:
        """
        The final terminal reward computes the Mean Average Precision over the entire evaluation dataset

        Returns:
            float: The Mean Average Precision over the entire evaluation dataset
        """
        predictions = []
        targets = []
        i = 0
        for img, target in self.eval_data_loader:
            if i > 100:
                break
            else:
                i += 1

            # Move image and labels to the device
            img = img.to(self.device)
            target = {k: v.squeeze(0).to(self.device) for k, v in target.items()}

            prediction = self.task_interface.detect(img)
            predictions.append(prediction[0])
            targets.append(target)

        metrics = self.task_interface.evaluate(predictions, targets)
        return metrics.map_50_95
    
if __name__ == "__main__":
    from gymnasium.utils.env_checker import check_env
    env = ImagePipeline(device='cuda')
    state, info = env.reset()
    # state, reward, terminated, truncated, info = env.step(env.action_space.sample())
    check_env(env)