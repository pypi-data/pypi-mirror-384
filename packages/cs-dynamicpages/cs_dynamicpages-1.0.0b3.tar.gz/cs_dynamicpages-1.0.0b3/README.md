# cs_dynamicpages

A new addon for Plone to create web-based dynamic pages.

The concept is pretty similar that of Volto blocks:

- You can build a page using reusable items.
- Each item can have different fields
- Each item can have different views

## Provided Content Types

- DynamicPageFolder: this content type will be created in a given folder, and will be the container
  where all the rows will be added.

- DynamicPageRow: this content type will be the one that will be rendered in a separate row in the view

- DynamicPageRowFeatured: this content type can be used to save static information that can be shown in a
  row. For instance: each of the items of a slider need a title, a description or an image. They can be added
  using this content-type

## Provided View

There is just one view `dynamic_view` registered for Folders and Naviation roots

### Different fields

To provide different fields, you should register standard `behaviors` to the `DynamicPageRow`
content type.

### Custom views

To provide different views, you should register standard views (using `zcml`).

Those views must be registered for implementers of `cs_dynamicpages.content.dynamic_page_row.IDynamicPageRow`
and their name _must_ start by `cs_dynamicpages-`.

To ease installation of such views in your products, `cs_dynamicpages.utils` contains 2 utility functions:

- `add_custom_view`: function to add a given view to the list of available row types
- `enable_behavior`: function to enable the given behavior in the `DynamicPageRow` content type

### Restrict fields in the row edit view

You may register several behaviors for `DynamicPageRow` objects but only use some of the fields
provided by them in a given view.

You can restrict which fields are shown in the edit form of the `DynamicPageRow` going to the
Dynamic Pages Controlpanel, and setting there the list of fields that will be shown when editing
each of the row types.

## Installation

Install cs_dynamicpages with `pip`:

```shell
pip install cs_dynamicpages
```

And to create the Plone site:

```shell
make create-site
```

## Contribute

- [Issue tracker](https://github.com/codesyntax/cs_dynamicpages/issues)
- [Source code](https://github.com/codesyntax/cs_dynamicpages/)

### Prerequisites ✅

- An [operating system](https://6.docs.plone.org/install/create-project-cookieplone.html#prerequisites-for-installation) that runs all the requirements mentioned.
- [uv](https://6.docs.plone.org/install/create-project-cookieplone.html#uv)
- [Make](https://6.docs.plone.org/install/create-project-cookieplone.html#make)
- [Git](https://6.docs.plone.org/install/create-project-cookieplone.html#git)
- [Docker](https://docs.docker.com/get-started/get-docker/) (optional)

### Installation 🔧

1.  Clone this repository, then change your working directory.

    ```shell
    git clone git@github.com:codesyntax/cs_dynamicpages.git
    cd cs_dynamicpages
    ```

2.  Install this code base.

    ```shell
    make install
    ```

### Add features using `plonecli` or `bobtemplates.plone`

This package provides markers as strings (`<!-- extra stuff goes here -->`) that are compatible with [`plonecli`](https://github.com/plone/plonecli) and [`bobtemplates.plone`](https://github.com/plone/bobtemplates.plone).
These markers act as hooks to add all kinds of subtemplates, including behaviors, control panels, upgrade steps, or other subtemplates from `plonecli`.

To run `plonecli` with configuration to target this package, run the following command.

```shell
make add <template_name>
```

For example, you can add a content type to your package with the following command.

```shell
make add content_type
```

You can add a behavior with the following command.

```shell
make add behavior
```

```{seealso}
You can check the list of available subtemplates in the [`bobtemplates.plone` `README.md` file](https://github.com/plone/bobtemplates.plone/?tab=readme-ov-file#provided-subtemplates).
See also the documentation of [Mockup and Patternslib](https://6.docs.plone.org/classic-ui/mockup.html) for how to build the UI toolkit for Classic UI.
```

## License

The project is licensed under GPLv2.

## Credits and acknowledgements 🙏

Generated using [Cookieplone (0.9.7)](https://github.com/plone/cookieplone) and [cookieplone-templates (4d55553)](https://github.com/plone/cookieplone-templates/commit/4d55553d61416df56b3360914b398d675b3f72a6) on 2025-07-17 11:59:12.982862. A special thanks to all contributors and supporters!
