<div align="center">
    <a href="https://github.com/r0075h3ll/FireEye"><img alt="FireEye" src="https://i.ibb.co/LYvR0yw/Untitled-design-2-removebg-preview.png"/></a>
    <h2>
    FireEye
    </h2>
</div>

<h4 align="center">AWS Monitoring Toolkit</h4>

<div align="center">
<img src="https://img.shields.io/badge/License-Apache%202.0-blue">
<img src="https://img.shields.io/badge/Python-3.12-blue">
<img src="https://img.shields.io/badge/Release-0.6.0 (dev)-green">
</div>

\
FireEye is an AWS monitoring toolkit for DevOps, Security, and IT teams. It can currently trace strings in AWS Lambda function(s) output logs via CloudWatch using simple [commands](#monitor-lambda-functions-w-cloudwatch-logs-insights).

[//]: # (insert gif)
[![asciicast](https://asciinema.org/a/696182.svg)](https://asciinema.org/a/696182)

### Installation

```bash
pip install setuptools
python3 setup.py install
```

### Features

##### Monitor lambda functions w/ CloudWatch Logs Insights

```python
fireeye --trace Bill --resource-name lambda_name
```

[//]: # (##### Get alerts on a slack channel)

[//]: # ()

[//]: # (```python)

[//]: # (fireeye --trace Bill --resource-name lambda_name --slack-url https://slack-webhook-url)

[//]: # (```)

### To Do

- [ ] EC2 Log Monitoring
- [ ] Send alerts on slack channel
- [ ] Improved search capabilities

### Contributions

You're welcome to open PR for making direct contributions to the project. Additionally, "Issues" section will
be considered for
- bug reports
- feature requests