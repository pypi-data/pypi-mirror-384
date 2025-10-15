# Jamā (जमा)

APIs et interfaces de stockage de médias.

## Pré-requis

- uv `curl -LsSf https://astral.sh/uv/install.sh | sh`
- imagemagick
- pdftoppm, pdftotext (poppler-utils)
- vips (libvips-tools)
- tesseract
- exiftool

## Installation

### Installation de JAMA, création d'un super-utilisateur et d'un projet de test

    make install

## Démarrage (développement)

    make run

Vous avez alors accès à la page d'accueil (par défaut http://localhost:8000).  

## Configuration

Au moment de l'installation, un fichier d'environnement est créé dans `$HOME/.jama/env`. Vous pouvez modifier
ce fichier pour modifier la configuration de Jama.

Variables disponibles:

    CACHE_LOCATION="var/cache"
    JAMA_APPS=""
    JAMA_ARK_APP_ID=""
    JAMA_ARK_SECRET_KEY=""
    JAMA_ARK_SERVER=""
    JAMA_DB_ADAPTER="sqlite"  # sqlite ou potgresql
    JAMA_DB_HOST="localhost"  # si JAMA_DB_ADAPTER est postgresql
    JAMA_DB_NAME="django"  # si JAMA_DB_ADAPTER est postgresql
    JAMA_DB_PASSWORD="django"  # si JAMA_DB_ADAPTER est postgresql
    JAMA_DB_PORT="5432"  # si JAMA_DB_ADAPTER est postgresql
    JAMA_DB_USER="django"  # si JAMA_DB_ADAPTER est postgresql
    JAMA_DEBUG="0"
    JAMA_FILES_DIR="var/media_sources_files"  # dossier où seront stockés les fichiers d'origine
    JAMA_IIIF_DIR="var/iiif"  # dossier où seront stockés les fichiers tuilés pour le serveur IIIF
    JAMA_IIIF_ENDPOINT="http://localhost/iip/IIIF="  # URL de base du serveur IIIF
    JAMA_IIIF_PROCESSING_DIR="var/processing"
    JAMA_IIIF_UPSCALING_PREFIX="^"
    JAMA_LOG_FILE="var/jama.log"
    JAMA_PARTIAL_UPLOADS_DIR="var/partial_uploads"
    JAMA_SECRET="7d*_8c!d$vv963qpr45_x)@f2t-x6fu2&yi+m+d6s!p!lt+_j+"
    JAMA_SITE="http://localhost:8000/"
    JAMA_SQLITE_DB_PATH=""
    JAMA_STATIC_ROOT="var/static"  # dossier des ressources statiques (pour mise en production)
    JAMA_URL_BASE_PATH=""
    JAMA_USE_ARK="0"  # "1" pour activer les URLs ARK
    JAMA_USE_CACHALOT="0"  # "1" pour utiliser le cache de base de donnée
    JAMA_USE_MODSHIB="1"
    JAMA_USE_WEBP="0"  # "1" pour utiliser la compression webp pour le tuilage des images (vérifier la compatibilité du serveur IIIF: à ce jour, IIP server est ok, pas Cantaloupe)
    JAMA_VAR_DIR="var"  # Dossier par défaut pour toutes les données
    MODSHIB_SHOW_LOCAL_LOGIN="1"
    MODSHIB_SHOW_SSO_LOGIN="0"

Concernant le serveur IIIF, pour un fonctionnement avec un serveur Cantaloupe par défaut :

    JAMA_USE_WEBP=0  # pas de prise en charge du WEBP par Cantaloupe 5.x. Utilisez IIPImage à la place
    JAMA_IIIF_PATH_SEPARATOR="%2F" # Le séparateur de dossier doit être URL-encoded
    JAMA_IIIF_ENDPOINT="http://localhost:8182/iiif/2/" # endpoint IIIF v2 par défaut

### Utilisation avec PostgreSQL

Si vous prévoyez d'utiliser Jama avec un nombre important d'utilisateurs en simultané, il est 
préférable d'utiliser PostgreSQL plutôt que SQLite.

Crééz une base de données :

```bash
source .env
sudo -u postgres psql -p $JAMA_DB_PORT -dpostgres -t -c "CREATE ROLE $JAMA_DB_USER ENCRYPTED PASSWORD '$JAMA_DB_PASSWORD' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;"
sudo -u postgres createdb -p $JAMA_DB_PORT -O $JAMA_DB_USER -E UTF8 $JAMA_DB_NAME;
```

Modifiez `$HOME/.jama/env`:

    JAMA_DB_ADAPTER="postgresql"
    JAMA_DB_HOST="$JAMA_DB_HOST"
    JAMA_DB_NAME="$JAMA_DB_NAME"
    JAMA_DB_PASSWORD="$JAMA_DB_PASSWORD"
    JAMA_DB_PORT="$JAMA_DB_PORT"
    JAMA_DB_USER="$JAMA_DB_USER"

Lancez à nouveau l'installation :

    make install

## Commandes CLI

### Ajout de fichiers locaux

Une commande permet d'ajouter des fichiers locaux à Jama au nom d'un
utilisateur Jama :

    uv run jama addlocalfiles /var/fichiers_a_ajouter/ jacques 1 --extensions .jpg .tif

Ici, le dossier `fichiers_a_ajouter` sera parcouru récursivement et les fichiers
avec une extension _.jpg_ ou _.tif_ seront ajoutés dans Jama dans le project ayant l'identifiant 1,
par l'utilisateur jacques. L'utilisateur comme le projet doivet exister préalablement dans Jama.

## Création d'un nouveau projet :

    (venv) code/jama: uv run jama newjamaproject "mon projet"
    Projet "mon projet" créé avec le compte administrateur "admin_mon_projet" et la clef d'API "EOwy6laNTMBDUvH6pGuOvGdMEpYM2F9M"

## Étendre JAMA

Les fonctionnalités de JAMA peuvent être étendues par le biais habituel des
[applications Django](https://docs.djangoproject.com/fr/4.0/ref/applications/).

### Applications Django et ajout de vues

Afin de faciliter l'installation d'applications Django sans avoir besoin de toucher au fichier `jama/settings.py`, une
variable d'environnement `JAMA_APPS` peut contenir une liste (séparée par des virgules) de modules python à charger en
tant
qu'applications Django.

### Point de montage des URLs de l'application

Soit une application fictive `mon_application`, si la variable `endpoint` est définie dans le fichier
`mon_application/__init__.py`, alors `endpoint` est utilisé comme point de montage pour les URLs définies dans
l'application Django (fichier `mon_application/urls.py`).

Exemple :

Dans le fichier `mon_application/__init__.py`:

```
endpoint = "mon-appli/"
```

Dans `mon_application/urls.py`:

```
from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.test),
]
```

La vue Django `test` sera accessible à l'URL `/mon-appli/test/`.

### Ajout de méthodes RPC

Il est possible d'ajouter des méthodes au point de montage RPC. Il suffit pour cela d'ajouter des fonctions dans un
module `mon_application/rpc/methods.py`. Toute fonction déclarée dans ce fichier sera ajoutée à la liste des fonctions
RPC, à l'exception des fonctions dont le nom commence par `_`.

Exemple, dans le fichier `mon_application/rpc/methods.py`:

```
from django.contrib.auth.models import User


def test_from_my_app(user: User, test_string: str) -> str:
    return test_string
```

Le premier argument de la méthode RPC est __toujours__ une instance de
[django.contrib.auth.models.User](https://docs.djangoproject.com/fr/4.0/ref/contrib/auth/#django.contrib.auth.models.User).

Le type des arguments et du retour de la fonction **doivent** être spécifiés.

⚠️ Il est possible d'écraser une méthode définie précédemment. À votre charge d'assurer l'unicité du nom de votre
méthode.
Une possibilité est de préfixer le nom de la méthode avec le nom de votre application.

⚠️ Le retour de la méthode RPC __doit__ être sérialisable par l'encodeur par défaut du module standard `json`.


### FAQ

## Relancer un tuilage en échec
```
$ uv run jama repl
Python 3.13.1 (main, Jan 14 2025, 22:47:38) [Clang 19.1.6 ] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> f = File.objects.filter(title="the_failed_filename").first()
>>> make_iiif(f, True)
```

## Lister le nombre de tuilages manquant
```
$ uv run jama repl
Python 3.13.1 (main, Jan 14 2025, 22:47:38) [Clang 19.1.6 ] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> File.objects.filter(tiled=False).count()
1481
```
_Attention, certains types de fichiers ne seront jamais tuilés, il conviendra de filtrer le champ file\_type pour s'assurer d'un résultat cohérent_