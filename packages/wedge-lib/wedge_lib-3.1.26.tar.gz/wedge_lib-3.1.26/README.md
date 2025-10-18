# Wedge Library

## Démarrage rapide

```bash
$ pip install wedge-lib
```

### Mode maintenance

#### Middleware

```python
MIDDLEWARE=[
    "w.drf.middlewares.maintenance_mode_middleware.MaintenanceModeMiddleware",
],
```


#### Command

Ajouter la commande maintenance_mode :

```python
from w.django.commands.abstract_maintenance_mode_command import (
    AbstractMaintenanceModeCommand,
)


class Command(AbstractMaintenanceModeCommand):
    pass
```

Utilisation :

```bash
$ python manage.py maintenance_mode <on/off>
```

### Configuration pour certains services

#### MailService
TBD
#### GoogleMapService
TBD
#### YousignService
TBD

## Development

### Installation

```bash
poetry install --sync
poetry shell
```

### Run test

```bash
$ pytest
```

### Before commit

Pour éviter de faire échouer le CI, lancer la commande:

```bash
$ ./before_commit.zsh
```

### Publier manuellement sur PyPI

Pour cela, il faut créer une nouvelle release sur GitHub avec le tag correspondant à la version de la librairie c'est à dire la version renseignée dans `pyproject.toml`.

- Aller sur la page GitHub du repository : https://github.com/Wedge-Digital/w
- Cliquer sur `Tags`
- Cliquer sur `Releases`
- Cliquer sur `Draft a new release`
- Dans Choose a tag saisir la version de la raison = version renseignée dans `pyproject.toml`
- Cliquer sur `Generate release notes`
- Cliquer sur `Publish release`

Le CI s'occupera ensuite de publier la librairie sur PyPi si les tests ne sont pas KO.




