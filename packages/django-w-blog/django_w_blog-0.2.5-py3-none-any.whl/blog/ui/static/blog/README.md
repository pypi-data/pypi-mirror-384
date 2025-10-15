# UI Styles

Basic commands to get started.

First `cd` into dir:

```console
cd blog/ui/static/blog
```

To generate the styles:

```console
npm install
cd blog/ui/static/blog
npx @tailwindcss/cli -i ../static/blog/css/app.css -o ../static/blog/css/styles.css --cwd ../../templates -m -w
```

To format the templates:

```console
npx prettier -w ../../templates
```
