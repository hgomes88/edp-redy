<div id="top"></div>


<!-- PROJECT SHIELDS -->

[![Release][release-shield]][release-url]
[![Build][build-shield]][build-url]
[![MIT License][license-shield]][license-url]

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

[![LinkedIn][linkedin-shield]][linkedin-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">Edp Redy</h3>

  <p align="center">
    EDP Redy API
    <br />
    <a href="https://github.com/hgomes88/edp-redy"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/hgomes88/edp-redy">View Demo</a>
    ·
    <a href="https://github.com/hgomes88/edp-redy/issues">Report Bug</a>
    ·
    <a href="https://github.com/hgomes88/edp-redy/issues">Request Feature</a>
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#the-reason-behind">The Reason Behind</a></li>
        <li><a href="#interface">Interface</a></li>
        <ul>
            <li><a href="#wiring">Wiring</a></li>
            <ul>
                <li><a href="#uart-pinout-and-configuration">Uart Pinout and Configuration</a></li>
            </ul>
            <li><a href="#protocol">Protocol</a></li>
            <ul>
                <li><a href="#frames">Frames</a></li>
            </ul>
        </ul>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About the Project

### The Reason Behind

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

### Installation

The installation of the library, including the CLI, is as simple as run:
```
$ pip install .
```

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

- [ ] Complete documentation

See the [open issues](https://github.com/hgomes88/edp-redy/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

To contribute to this project, you need to execute the following steps:

1. Install
    1. Create a virtual environment (see how to [here][venv-website]):

    2. Activate the virtual environment (see how to [here][venv-website]):

    3. Install all the requirements for development:

        `pip install -e ".[dev]"`

    4. Install pre-commit:

        `pre-commit install`

2. Create new feature and commit the changes

    1. Create a new feature branch based from the main branch:

        `git checkout -b feature/<feature_name>`

    2. Implement the changes for the feature

    3. Run formatters/linters:

        1. Autopep8:

            `autopep8 src/ tests/`

        1. Flake8:

            `flake8 src/ tests/`

        1. Mypy:

            `mypy src/ tests/`

    4. Commit the changes (this should run pre-commit to format/lint anyway)

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the Apache License Version 2.0. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Hugo Gomes - hgomes88@gmail.com

Project Link: [https://github.com/hgomes88/edp-redy](https://github.com/hgomes88/edp-redy)

Pipy Releases: [https://pypi.org/project/edp-redy-api](https://pypi.org/project/edp-redy-api)


<p align="right">(<a href="#top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [[othneildrew] Best Readme Template](https://github.com/othneildrew/Best-README-Template/blob/master/README.md)


<p align="right">(<a href="#top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->

[build-shield]: https://img.shields.io/github/workflow/status/hgomes88/edp-redy/Test/main?style=for-the-badge
[build-url]: https://github.com/hgomes88/edp-redy/actions/workflows/on-push.yml

[release-shield]:https://img.shields.io/pypi/v/edp-redy-api?label=Release&style=for-the-badge
[release-url]: https://pypi.org/project/edp-redy-api/

[contributors-shield]: https://img.shields.io/github/contributors/hgomes88/edp-redy.svg?style=for-the-badge
[contributors-url]: https://github.com/hgomes88/edp-redy/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/hgomes88/edp-redy.svg?style=for-the-badge
[forks-url]: https://github.com/hgomes88/edp-redy/network/members

[stars-shield]: https://img.shields.io/github/stars/hgomes88/edp-redy.svg?style=for-the-badge
[stars-url]: https://github.com/hgomes88/edp-redy/stargazers

[issues-shield]: https://img.shields.io/github/issues/hgomes88/edp-redy.svg?style=for-the-badge
[issues-url]: https://github.com/hgomes88/edp-redy/issues

[license-shield]: https://img.shields.io/github/license/hgomes88/edp-redy.svg?style=for-the-badge
[license-url]: https://github.com/hgomes88/edp-redy/blob/main/LICENSE

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/hugohomes

[venv-website]: https://docs.python.org/3/library/venv.html
