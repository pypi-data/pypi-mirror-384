# LeRobot Robot BI SO101 Leader

A LeRobot integration package for the BI SO101 bimanual robot configuration.

## Description

This package provides integration between LeRobot and the BI SO101 bimanual robot setup, enabling robot learning and control capabilities for dual-arm manipulation tasks. This is specifically for the leader arms. For the follower arms, please visit [here](https://pypi.org/project/lerobot-robot-bi-so101-follower/).

## Features

- Bimanual robot configuration support
- Integration with LeRobot framework
- SO101 robot-specific implementations

## Installation

### From PyPI (when published)

```bash
pip install lerobot_teleoperator_bi_so101_leader
```

### From Source

```bash
git clone https://github.com/SIGRobotics-UIUC/lerobot_teleoperator_bi_so101_leader.git
cd lerobot_teleoperator_bi_so101_leader
pip install -e .
```

## Requirements

- Python >= 3.8
- LeRobot >= 1.0.0

## Usage

```python
from lerobot_teleoperator_bi_so101_leader import BiSo101Leader

# Initialize the robot follower
leader = BiSo101Leader()

# Use with LeRobot
# ... your robot learning code here ...
```

## Development

To set up the development environment:

```bash
git clone https://github.com/SIGRobotics-UIUC/lerobot_teleoperator_bi_so101_leader.git
cd lerobot_teleoperator_bi_so101_leader
pip install -e ".[dev]"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- Aarsh Mittal: aarshm2@illinois.edu
- Keshav Badrinath: keshavb3@illinois.edu
- Leo Lin: leolin3@illinois.edu

## Acknowledgments

- Built on top of the LeRobot framework
- Designed for BI SO101 bimanual robot configuration
