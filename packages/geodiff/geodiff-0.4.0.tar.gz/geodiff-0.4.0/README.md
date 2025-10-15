Differentiable geometry representations for shape parameterization and optimization.


## Project Plan
### Stage 1: Initial Setup
- [x] Add Github Actions workflow for Github Pages.
- [x] Create first cut User Docs using Jupyter Books and MyST markdown.
    - [x] What is this package for?
    - [x] Add .gitignore for MyST markdown.
- [x] Launch Github Discussions for the project.
    - [x] Create introductory dicussion post.
- [x] Add MIT License.
- [x] Update pyproject.toml.
    - [x] Maintainers, license, license-file, keywords, classifiers, project urls.
- [x] Add Github Actions workflow for Github Release and PyPI publishing.
- [x] Add CHANGELOG.md to maintain release details.
- [x] Create first tag and push it to initiate first release and publish.

### Stage 2: Implement Geometry Representations
- [x] Install necessary dependencies
    - [x] numpy, matplotlib and pytorch.
- [x] Implement loss functions.
    - [x] Start with Chamfer loss.
- [x] Hicks-Henne bump functions.
    - [x] Implement the Hicks-Henne class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [x] CST parameterization.
    - [x] Implement the CST class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [x] Create a tag and push it to create a release.
- [ ] NICE normalizing flow parameterization.
    - [x] Implement the NICE class.
    - [x] Add visualization method.
    - [x] Add type hints and docstrings.
    - [x] Add test script.
    - [x] Add documentation.
    - [x] Merge with main branch.
    - [ ] Create a tag and push it to create a release.