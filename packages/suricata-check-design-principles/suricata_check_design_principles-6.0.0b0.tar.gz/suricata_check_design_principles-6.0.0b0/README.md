# The `suricata-check` project - Design Principles

[![Static Badge](https://img.shields.io/badge/docs-suricata--check-blue)](https://suricata-check-design-principles.teuwen.net/)
[![GitHub License](https://img.shields.io/github/license/Koen1999/suricata-check-design-principles)](https://github.com/Koen1999/suricata-check-design-principles/blob/master/LICENSE)

[![Quick Test, Build, Lint](https://github.com/Koen1999/suricata-check-design-principles/actions/workflows/python-pr.yml/badge.svg?event=push)](https://github.com/Koen1999/suricata-check-design-principles/actions/workflows/python-pr.yml)
[![Extensive Test](https://github.com/Koen1999/suricata-check-design-principles/actions/workflows/python-push.yml/badge.svg)](https://github.com/Koen1999/suricata-check-design-principles/actions/workflows/python-push.yml)

[`suricata-check`](https://github.com/Koen1999/suricata-check) is a command line utility to provide feedback on [Suricata](https://github.com/OISF/suricata) rules.
The tool can detect various issues including those covering syntax validity, interpretability, rule specificity, rule coverage, and efficiency.

This extension is an additional checker for design issues, which can be installed by running the following command:

```bash
pip install suricata-check-design-principles
```

Rules starting with prefix _P_ indicate issues relating to rule design principles posed in the [Ruling the Unruly](https://doi.org/10.1145/3708821.3710823) paper.
Rules with _P_-type issues can relate to a specificity and coverage.

## Contributing

If you would like to contribute, please check out [CONTRIBUTING.md](https://github.com/Koen1999/suricata-check-design-principles/blob/master/CONTRIBUTING.md) some helpful suggestions and instructions.

## License

This project is licensed under the [European Union Public Licence (EUPL)](https://github.com/Koen1999/suricata-check-design-principles/blob/master/LICENSE).
