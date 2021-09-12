<div align="center">

<h1>Markdown URL Checker</h1>
<strong>>> <i>Simple CLI tool to check URL health in markdown files</i> <<</strong>

&nbsp;

![img](./art/logo.png)

</div>


This CLI tool traverses down a markdown file, extracts all the valid URLs, and checks whether they're accessible or not. In case it encounters a broken link, it raises an error. Internally, this is optimized for larger markdown files and tested for huge markdown files with thousands of links.

## Installation

Install the CLI using pip:

```
pip install md-url-checker
```


## Usage

* To check the URLs in a single markdown file, run:

    ```
    md-url-check -f file.md
    ```

* To check the URLs in multiple markdown files, run:

    ```
    echo 'file1.md file2.md' | xargs -n 1 md-url-check -f
    ```

* To check the URLs in multiple files in a folder, run:

    ```
    find . -name '*.md' | xargs -n 1 --no-run-if-empty md-url-check -f
    ```

* Suppress intermediate output:

    ```
    md-url-check -f file.md -s
    ```

* Provide the number of threads to be used while making the requests:

    ```
    md-url-check -f file.md -s -t 32
    ```

    This uses 32 interleaving threads to make the requests concurrently. Default is 8.

## Know Issues

Currently, the checker fails for urls with parenthesis in them, for example:

```
https://en.wikipedia.org/wiki/John_Gall_(author)
```

<div align="center">
<i> ✨ 🍰 ✨ </i>
</div>
