<!-- Author: Mitchell Then -->

# Recipe Formatter

Contains small python script that reads recipes in defined YAML format and uses LaTeX to generate nice looking PDFs. Uses Docker container to make things easy.

## Usage

```
git clone <repo>
cd <repo>
docker build -t "latex" .
docker run --rm -v <source dir>:/data latex /root/make_pdfs.py /data/Recipes_src/ /data/Recipes/
```

Where `<source dir>` is the directory where `Recipes_src/` and `Recipes/` reside.

## Author

Mitchell Then
