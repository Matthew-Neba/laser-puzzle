# Laser Puzzle RL Architecture

```text
+------------------------------------------+
| Your C Environment                       |
| laser_puzzle.h                           |
|                                          |
|  LaserPuzzle struct                      |
|  c_reset(env)                            |
|  c_step(env)                             |
|  c_render(env)                           |
|  c_close(env)                            |
+--------------------+---------------------+
                     |
                     | included by
                     v
+------------------------------------------+
| binding.c                                |
|                                          |
|  #define Env LaserPuzzle                 |
|  #define OBS_SIZE 36                     |
|  #define NUM_ATNS 1                      |
|  #define ACT_SIZES {NUM_ACTIONS}         |
|  #define OBS_TENSOR_T ByteTensor         |
|                                          |
|  my_init(env, kwargs)                    |
|  my_log(log, out)                        |
+--------------------+---------------------+
                     |
                     | specializes
                     v
+------------------------------------------+
| vecenv.h                                 |
|                                          |
| Generates vector-env C code for          |
| LaserPuzzle.                             |
|                                          |
|  create_static_vec                       |
|  static_vec_reset                        |
|  static_vec_step                         |
|  gpu_vec_step / cpu_vec_step             |
|  static_vec_close                        |
|                                          |
| Owns big buffers:                        |
|  observations [envs, obs_size]           |
|  actions      [envs, num_atns]           |
|  rewards      [envs]                     |
|  terminals    [envs]                     |
+--------------------+---------------------+
                     |
                     | compiled into
                     v
+------------------------------------------+
| Native Compiled Module                   |
| C / C++ / CUDA shared library            |
|                                          |
|  Runs many CPU C envs                    |
|  Moves tensors/buffers                   |
|  Interfaces with PyTorch/CUDA            |
+--------------------+---------------------+
                     |
                     | called by
                     v
+------------------------------------------+
| Python Trainer                           |
|                                          |
|  Creates vector env                      |
|  Runs policy/model                       |
|  Sends actions                           |
|  Receives observations/rewards/dones     |
|  Computes PPO loss                       |
|  Optimizes neural net                    |
|  Logs/checkpoints                        |
+------------------------------------------+
```

## Runtime Loop

```text
Python policy
    |
    v
CUDA/PyTorch computes actions
    |
    v
actions buffer
    |
    v
vecenv calls c_step(env) for many C envs
    |
    v
obs/reward/terminal buffers updated
    |
    v
Python/PyTorch reads batch and trains
```

## Key Idea

`binding.c` is the contract between the C environment and the compiled Puffer
vector environment. It tells the compiled code the environment type,
observation shape, action shape, observation dtype, initialization callback, and
log export callback.

## What `binding.c` Provides

`binding.c` is not gameplay logic. It is compile-time metadata and two callback
functions for the generic vector environment.

```c
#include "laser_puzzle.h"

#define OBS_SIZE (INIT_ROWS * INIT_COLS)
#define NUM_ATNS 1
#define ACT_SIZES {NUM_ACTIONS}
#define OBS_TENSOR_T ByteTensor

#define Env LaserPuzzle
#include "vecenv.h"
```

These macros must be visible before `vecenv.h` is included because `vecenv.h`
uses them to generate concrete C functions for this specific environment.

- `Env`: the C struct type for one environment instance.
- `OBS_SIZE`: number of observation elements per agent.
- `NUM_ATNS`: number of action values per agent per step.
- `ACT_SIZES`: action-space shape. For this puzzle, `{NUM_ACTIONS}` means one
  discrete action with `NUM_ACTIONS` choices.
- `OBS_TENSOR_T`: observation dtype exposed to the Python/PyTorch side.

The callbacks:

```c
void my_init(Env* env, Dict* kwargs);
void my_log(Log* log, Dict* out);
```

`my_init` initializes fields that are not reset every episode, such as board
memory, dimensions, maximum steps, and `num_agents`.

`my_log` copies averaged C `Log` fields into a dictionary that Python can read.

## What `vecenv.h` Generates

After `binding.c` defines the macros, including `vecenv.h` generates functions
specialized to `LaserPuzzle`:

```c
StaticVec* create_static_vec(...);
void static_vec_reset(StaticVec* vec);
void static_vec_step(StaticVec* vec);
void gpu_vec_step(StaticVec* vec);
void cpu_vec_step(StaticVec* vec);
void static_vec_close(StaticVec* vec);
int get_obs_size(void);
int get_num_atns(void);
int* get_act_sizes(void);
const char* get_obs_dtype(void);
```

Those functions form the compiled vector-env API that the rest of Puffer calls.

## Buffer Ownership

`vecenv.h` allocates large contiguous buffers for all environments:

```text
observations: total_agents * OBS_SIZE
actions:      total_agents * NUM_ATNS
rewards:      total_agents
terminals:    total_agents
```

Then each `LaserPuzzle` gets pointers into its slice:

```c
env->observations = big_observations + offset;
env->actions = big_actions + offset;
env->rewards = big_rewards + offset;
env->terminals = big_terminals + offset;
```

This layout lets the compiled/PyTorch side treat many C environments as one
batch.

In standalone `laser_puzzle.c`, there is no `vecenv.h` wrapper, so the program
must still provide these buffers itself. That is why standalone and vectorized
training need a clear ownership rule.

## Required Env Fields For Default `vecenv.h`

When `binding.c` does not define `MY_VEC_INIT`, `vecenv.h` uses its default
`my_vec_init`. That default path expects the env struct to have:

```c
int num_agents;
unsigned int rng;
```

`num_agents` tells `vecenv.h` how many agents this env contributes to the
batched buffers. Laser Puzzle is single-agent, so it is `1`.

`rng` is seeded by the default vector init. The env can then use it for
per-environment randomness instead of global `rand()`, which is important when
many envs are stepped in parallel.

If a custom `MY_VEC_INIT` is written, these assumptions can be changed, but most
Puffer envs use the default path and include these fields.
