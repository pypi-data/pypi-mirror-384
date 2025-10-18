This Python client makes it easy to work with Decision Optimization Experiments.

The available functionality of the client includes, for example, the ability to access an experiment, and, starting from an existing scenario, create one or several copies where some of the input data or model formulation can be modified, and then solved. Several scenarios can be created and run synchronously or asynchronously. Results are automatically saved and made available in the experiment. They can hence be used in visualizations, for example to compare scenarios.

Use cases include:

- automated testing: programmatically run multiple scenarios of a model with different data to ensure the correctness of the model and its scalability,
- what-if analysis: create different scenarios for different situations and see the impact on their optimal solutions
- multi-objective trade-off analysis: create different scenarios with different combinations of weights of different objectives and see the impact on the solutions,
- Monte Carlo simulations
- Pareto frontier approximations
- etc.

All this is done within the model development environment, allowing you to identify and validate what the best model to deploy is.

First, create a ``decision_optimization_client.Client`` class, from which you'll be able to retrieve an ``decision_optimization_client.Experiment``.
