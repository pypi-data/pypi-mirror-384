# Statsig Python Server SDK
[![tests](https://github.com/statsig-io/python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/statsig-io/python-sdk/actions/workflows/test.yml)

The python SDK for server/multi-user environments.

Statsig helps you move faster with Feature Gates (Feature Flags) and Dynamic Configs. It also allows you to run A/B tests to validate your new features and understand their impact on your KPIs. If you're new to Statsig, create an account at [statsig.com](https://www.statsig.com).

## Getting Started

Visit our [getting started guide](https://docs.statsig.com/server/pythonSDK).

## Testing

Each server SDK is tested at multiple levels - from unit to integration and e2e tests.  Our internal e2e test harness runs daily against each server SDK, while unit and integration tests can be seen in the respective github repos of each SDK.

Run local unit tests separately for now:

```
python3 -m unittest tests/server_sdk_consistency_test.py
python3 -m unittest tests/test_statsig_e2e.py
```

## Guidelines

- Pull requests are welcome! 
- If you encounter bugs, feel free to [file an issue](https://github.com/statsig-io/python-sdk/issues).
- For integration questions/help, [join our slack community](https://join.slack.com/t/statsigcommunity/shared_invite/zt-pbp005hg-VFQOutZhMw5Vu9eWvCro9g).
