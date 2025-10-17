# LeRobot Robot BI SO101 Follower

A LeRobot integration package for the BI SO101 bimanual robot configuration.

## Description

This package provides integration between LeRobot and the BI SO101 bimanual robot setup, enabling robot learning and control capabilities for dual-arm manipulation tasks. This is specifically for the follower arms. For the leader arms, please visit [here](https://pypi.org/project/lerobot-teleoperator-bi-so101-leader/).

## Features

- Bimanual robot configuration support
- Integration with LeRobot framework
- SO101 robot-specific implementations

## Installation

### From PyPI (when published)

```bash
pip install lerobot_robot_bi_so101_follower
```

### From Source

```bash
git clone https://github.com/SIGRobotics-UIUC/lerobot_robot_bi_so101_follower.git
cd lerobot_robot_bi_so101_follower
pip install -e .
```

## Requirements

- Python >= 3.8
- LeRobot >= 1.0.0

## Usage

```python
from lerobot_robot_bi_so101_follower import BiSo101Follower

# Initialize the robot follower
follower = BiSo101Follower()

# Use with LeRobot
# ... your robot learning code here ...
```

## Development

To set up the development environment:

```bash
git clone https://github.com/SIGRobotics-UIUC/lerobot_robot_bi_so101_follower.git
cd lerobot_robot_bi_so101_follower
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

- Leo and Keshav
- Email: gyattman123@gmail.com

## Acknowledgments

- Built on top of the LeRobot framework
- Designed for BI SO101 bimanual robot configuration
