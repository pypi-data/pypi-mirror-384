<h1 align="center">QReward</h1>
<p align="center">
   <em>AQ ✖️️ Reward = QReward</em>
</p>

<p align="center">
   <a href="https://github.com/AQ-MedAI/QReward/actions">
      <img src="https://github.com/AQ-MedAI/QReward/actions/workflows/python-app.yml/badge.svg" alt="Github Actions Status">
   </a>
   <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/AQ-MedAI/QReward" target="_blank">
      <img src="https://coverage-badge.samuelcolvin.workers.dev/AQ-MedAI/QReward.svg" alt="Coverage">
   </a>
   <a href="https://badge.fury.io/py/qreward">
      <img src="https://badge.fury.io/py/qreward.svg" alt="PyPI version">
   </a>
   <a href="https://pypi.org/project/qreward/">
      <img src="https://img.shields.io/pypi/pyversions/qreward.svg?colorB=brightgreen" alt="PyPI - Python Version">
   </a>
   <a href="https://img.shields.io/github/repo-size/AQ-MedAI/QReward">
      <img src="https://img.shields.io/github/repo-size/AQ-MedAI/QReward" alt="GitHub repo size">
   </a>
</p>
<p align="center">
   <a href="https://pypi.org/project/qreward">
      <img src="https://img.shields.io/pypi/format/qreward.svg" alt="PyPI - Format">
   </a>
   <a href="https://github.com/AQ-MedAI/QReward/pulls">
      <img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat" alt="Contributions welcome">
   </a>
</p>

[中文版本](README_ZH.md)

## 📣 Introduction & Background

This feature is designed to address the compute capacity shortage and concurrency rate-limiting issues in the current RL reward process.
By integrating multiple cloud compute services and combining intelligent scheduling with request optimization strategies, it maximizes the utilization of computing resources and significantly reduces task execution time.
The system automatically determines the request distribution method based on real-time compute availability, rate-limit thresholds, and task priorities, thereby avoiding unnecessary backoff delays and improving overall throughput.

There are three main causes for the latency issue in the current RL reward process:

1. Python concurrent requests triggering rate-limit failures

   * Excessive concurrency leads to hitting the rate limits of the compute service.
   * Once rate limiting occurs, the client applies a backoff strategy, reducing the number of active requests.
   * As a result, the available compute capacity of the Model Cloud Service is not fully utilized, causing potential resource underuse.

2. Insufficient Model Cloud Service compute capacity

   * The Model Cloud Service alone cannot meet the total compute demand, resulting in increased task queuing and processing delays.
   * The solution involves introducing additional compute services to supplement capacity and designing an appropriate scheduling strategy to dynamically and efficiently distribute tasks among multiple compute resources, thereby alleviating compute bottlenecks.

3. Non-optimal task execution flow with unnecessary serialization

   * Some subtasks within the RL reward process could be executed in parallel, but the current implementation runs them sequentially, causing increased total latency.
   * Lack of asynchronous or pipeline optimization results in inefficient mixing of I/O waits and computation.


## ✨ Features

Beyond supporting Verl and Slime, the solution also provides acceleration capabilities for general-purpose functions.

1. HTTP Call Optimization

   * Connection reuse: Reduce handshake latency and frequent reconnections using HTTP Keep-Alive or connection pooling.
   * Batch requests: Aggregate multiple small requests into batch calls to reduce request frequency and network overhead.
   * Concurrency control: Intelligently adjust the level of concurrency to avoid hitting rate limits of the Model Cloud Service while maintaining high utilization.

2. Intelligent Retry Mechanism

   * Error-type-based retry: Quickly retry recoverable errors (e.g., timeouts, temporary network failures) while avoiding retries for non-recoverable errors to save resources.
   * Optimized exponential backoff: Integrate compute utilization monitoring into backoff intervals, dynamically deciding wait times to prevent prolonged idle resources.
   * Multi-source retry: Redirect retries to other available compute services to avoid single-service bottlenecks.

3. Multi-compute Scheduling（Coming soon👀）

   * Integrate additional compute resources beyond the Model Cloud Service into a unified compute pool.
   * Optimize distribution based on task priority, latency sensitivity, and load balancing.

## 📒 ChangeLog

[CHANGELOG.md](CHANGELOG.md)

## 🔰 Installation

**pip install**
```bash
pip install qreward
```

**from source code**
```shell
# normal way to install from source code
$ git clone https://github.com/AQ-MedAI/QReward.git
$ cd QReward
$ pip install -r requirements.txt
$ python setup.py install

# or you can use make file
$ make install
```

## 📝 Usage

* Pure accelerate examples: [Examples](https://github.com/AQ-MedAI/QReward/tree/main/examples/normal)
* With verl Framework examples: [Examples](https://github.com/AQ-MedAI/QReward/tree/main/examples/verl_example)
* With slime Framework examples: [Examples](https://github.com/AQ-MedAI/QReward/tree/main/examples/slime_example)

## ⛏ Code Quality

### Unit Tests

```shell
$ pip install -r tests/requirements.txt
$ make
```

## 😉 Authors

QReward is primarily developed and maintained by the following developers:

* [@sunhailin-Leo](https://github.com/sunhailin-Leo)
* [@Vignetting](https://github.com/Vignetting)

For more contributor information, please visit [QReward/graphs/contributors](https://github.com/AQ-MedAI/QReward/graphs/contributors)

## 💡 Contributing

We look forward to more developers participating in the development of QReward. We will ensure prompt review of PRs and timely responses. However, when submitting a PR, please ensure:

1. Pass all unit tests; if it's a new feature, please add corresponding unit tests
2. Follow development guidelines, format code using black and flake8 (`$ pip install -r requirements-dev.txt`)
3. Update corresponding documentation if necessary

## 📃 License

LEGAL.md [©AQ-MedAI](LEGAL.md)
