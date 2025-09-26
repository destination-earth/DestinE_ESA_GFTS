# Documentation Generation

## Overview

This section outlines the tools and processes used to generate and maintain the GFTS documentation. By understanding the documentation workflow, contributors can ensure consistency and accuracy in updates.

## Tools and Technologies

- **Markdown**: The primary format for writing documentation, allowing for easy readability and formatting.
- **Jupyter Book**: Utilized for compiling and rendering markdown files into a cohesive, navigable book format.
- **GitHub Pages**: Used for hosting the generated HTML documentation, providing public access and easy updates.
- **GitHub Actions**: Automates tasks such as linting, formatting, and the generation and deployment of Jupyter Book, ensuring consistency and efficiency.

## Workflow

- **Writing Documentation**:
  - Documentation is authored in markdown files, organized into directories and sections for clarity.
  - Contributors should adhere to established writing guidelines and formats.
- **Building Documentation**:
  - Jupyter Book builds the documentation by converting markdown files into a structured HTML site.
  - The build process incorporates any custom configurations or themes defined in the repository.
- **Deployment**:
  - Automated via GitHub Actions, the deployment process triggers on changes to the documentation files.
  - Successful builds are pushed to the gh-pages branch, making them publicly accessible on GitHub Pages.

## Best Practices

- **Version Control**: Use branches and pull requests to manage changes and reviews before merging updates into the main branch.
- **Regular Updates**: Ensure documentation reflects the latest system changes and enhancements to maintain relevance and accuracy.
- **Feedback Loop**: Encourage users to report issues or suggest improvements to continuously refine the documentation.
