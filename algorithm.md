# Training Algorithm

Laser Puzzle uses PufferLib's PPO-style actor-critic trainer.

Each rollout runs many envs in parallel:

```text
samples_per_rollout = total_agents * horizon
```

With the starter config:

```text
1024 envs * 48 steps = 49152 samples
```

Here, a sample means one action step:

```text
observation -> action -> reward/terminal/new observation
```

## Actor-Critic Network

The policy network, or actor, takes the board state and outputs a distribution
over the 48 actions.

The critic takes the board state and outputs a value estimate: how much future
reward this state is expected to lead to.

Puffer learns both with one shared network body:

```text
state -> encoder / MinGRU -> policy head -> action probabilities
                       |
                       -> value head  -> state value
```

The shared encoder/core learns useful board features once, then the two heads
reuse those features for different predictions. This makes learning more
efficient than training two fully separate networks.

So the model predicts both:

- a policy: probabilities over the 48 actions
- a value: expected future reward from the board

Training minimizes:

```text
loss = policy_loss + vf_coef * value_loss - ent_coef * entropy
```

Main knobs:

- `horizon`: steps collected per env before training. `48` matches one full Laser Puzzle episode.
- `total_agents`: parallel env count. More agents collect more data per rollout.
- `minibatch_size`: number of stored step samples per optimizer update.
- `gamma`: future reward discount. Higher means longer-term credit assignment.
- `gae_lambda`: advantage smoothing. Higher uses more long-range reward info.
- `learning_rate`: optimizer step size.
- `vf_coef`: how much the value function loss matters.
- `ent_coef`: exploration bonus. Higher keeps the policy more random early.
- `hidden_size`: neural net width.
- `num_layers`: neural net depth/recurrent layers.

Good first smoke test:

```bash
puffer train laser_puzzle --slowly --train.total-timesteps 100000
```
