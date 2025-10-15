from typing import Optional, List
from prt_rl.env.interface import EnvironmentInterface
from prt_rl.common.recorders import Recorder
from prt_rl.common.visualizers import Visualizer
from prt_rl.agent import BaseAgent


class Runner:
    """
    A runner executes an agent in an environment. It simplifies the process of evaluating agents that have been trained.

    The runner assumes the rgb_array is in the info dictioanary and has shape (num_envs, channel, height, width).

    .. note::
        To use the visualizer, the environment wrapper render mode must be set to 'rgb_array'.
    
    Args:
        env (EnvironmentInterface): the environment to run the agent in
        agent (BaseAgent): Agent to be executed in the environment
        recorders (Optional[List[Recorder]]): List of recorders to record the experience and info during the run
        visualizer (Optional[Visualizer]): Visualizer to show the environment frames during the run
    """
    def __init__(self,
                 env: EnvironmentInterface,
                 agent: BaseAgent,
                 recorders: Optional[List[Recorder]] = None,
                 visualizer: Optional[Visualizer] = None,
                 ) -> None:
        self.env = env
        self.agent = agent
        self.recorders = recorders or []
        self.visualizer = visualizer

    def run(self):
        # Reset the environment and recorder
        for r in self.recorders:
            r.reset()

        state, info = self.env.reset()
        done = False

        # Start visualizer and show initial frame
        if self.visualizer is not None:
            self.visualizer.start()
            self.visualizer.show(info['rgb_array'][0])

        for r in self.recorders:
            r.record_info(info)

        # Loop until the episode is done
        while not done:
            action = self.agent(state)
            next_state, reward, done, info = self.env.step(action)

            # Record the environment frame
            if self.visualizer is not None:
                self.visualizer.show(info['rgb_array'][0])

            for r in self.recorders:
                r.record_info(info)
                r.record_experience({
                    'state': state,
                    'action': action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done
                })

            state = next_state

        if self.visualizer is not None:
            self.visualizer.stop()

        # Save the recording
        for r in self.recorders:
            r.close()

        self.env.close()
