# deephonor_gym Package

This package is part of the RL (Reinforcement Learning) project.  
You can call this tool DHGym.

这个库取名 DHGym，因为我很喜爱这个库。

## Overview

The development purpose of deephonor-gym is to significantly lower the barriers to reinforcement learning and physical simulation.   
Based on this library, users can very quickly view and train robots.  
While this simulation platform has limited performance, it offers high accuracy, making it well-suited for algorithm validation by students, companies, and individual enthusiasts.

翻译：易用，好用，免费

## Installation

The recommended way to install this package is via PyPI:

`pip install deephonor-gym --no-cache-dir`

or

`pip install deephonor-gym`

## License

This project is licensed under the **GNU Affero General Public License v3.0**.  
See [LICENSE](LICENSE) for the full text.

## Detail
- explain_action
    - 'ball' is link name. -> 'Impulse.ball' = direction array
    - 'KP1' is joint name. -> 'joint.ball' = angle

- explain_reset
    - 'ball' is link name.
    - 'KP1' is joint name.

```bash
   Y 
   |     Z screen 
   |  ／
   .—— —— X
``` 

## Usage

Once installed, the package can be imported via `from deephonor_gym import DHgym, DHgym_VecEnv, open_browser, Upload`
Or, you can read the source code to access additional details.

## Example

具体见 example 目录下的 train.ipynb ，哪里有详细的解释

```python
from deephonor_gym import DHgym, DHgym_VecEnv, open_browser, Upload

conn = DHgym.connect() # 与网页连接，仅运行一次

class myEnv(DHgym) :
    """用户自己写的代码"""
    def init(self):
        ...

    def explain_obs(self,obs):
        ...

    def explain_action(self,action):
        ...

    def explain_reset(self,reset_array):
        ...

    def reward(self,state):
        ...
env_Engine = DHgym_VecEnv( [lambda : myEnv(conn)]) # 查看 env

```

