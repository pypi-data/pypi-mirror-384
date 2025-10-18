#> This is the litterate configuration file for litterate itself.

name = "Litterate"
description = """
`litterate` is a tool to generate beautiful literate programming-style
description of your code from comment annotations.

Read more at [the GitHub repo](https://github.com/thesephist/litterate).
"""

#> We can use GitHub Pages to host this generated site
baseURL = "/litterate"

files = [
    "./src/litterate/**/*.py",
    "./litterate.config.py",
]

output_directory = "./docs/"
