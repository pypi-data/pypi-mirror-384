# django-chamber

[![Django CI](https://github.com/skip-pay/django-chamber/actions/workflows/django.yml/badge.svg)](https://github.com/skip-pay/django-chamber/actions/workflows/django.yml)

Chamber contains a collection of useful base model classes, form fields, model fields, decorators, or other shortcuts to aid web development in Django.

One can think of it as a toolbox with utilities that were too small to justify creating a standalone library and therefore ended up here. Hence the name **Chamber**.

## Features

The most noteworthy part of Chamber is the alternative base class for Django models called `SmartModel`. It provides following additional features:

Other useful components include:

* AuditModel -- adds `created_at` and `changed_at` fields to the basic Django model,
* SmartQuerySet -- adds `fast_distinct` method to querysets (useful for PostgreSQL),
* several enum classes such as `ChoicesNumEnum` or `SequenceChoiceEnum`,
* new Django-style shortcuts such as `get_object_or_none`, `change_and_save`, or `bulk_change_and_save`.
* `MigrationLoadFixture` class that supports loading Django fixtures inside a database migration
* ...and more.

## Contributing & Documentation

You are welcomed to contribute at https://github.com/druids/django-chamber. There is an example project in the repository. Your feature should be added to this example project with tests as well as the documentation.

1. Go to the `example` directory and call `make install` to install it.
2. Run tests using `make test`.

## Known Issues

* documentation of this library is a work in progress, needs a lot of attention
* SmartModel extends the AuditModel and therefore always adds `created_at` and `changed_at` fields to the model which is not always desirable

## License

This library is licenced under MIT licence. See the LICENCE file for details.
