cp -r pages/utilities/theme docs/
cp -r pages/utilities/assets docs/
cat pages/utilities/template.mkdocs.yml >> mkdocs.yml
mkdocs serve
