from pathlib import Path
import os
import tempfile
from shutil import which
from dotenv import load_dotenv
import sys
import secrets
import string

for tool in [
    "vips",
    "convert",
    "exiftool",
    "pdftoppm",
    "pdftotext",
    "tesseract",
]:
    if not Path(which(tool) or "/does/not/exist").exists():
        sys.exit(f"Couldn't find tool {tool}, please read installation instructions.")


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
BASE_DIR = Path(__file__).resolve().parent.parent

VAR_DIR = os.getenv("JAMA_VAR_DIR") or Path(Path.home(), ".jama")
VAR_DIR = Path(VAR_DIR).resolve()

os.makedirs(VAR_DIR, exist_ok=True)
env_file = Path(VAR_DIR, "env")
if not env_file.exists():
    secret = "".join(secrets.choice(string.ascii_letters) for _ in range(32))
    with open(env_file, "w") as f:
        f.write(f"JAMA_DEBUG=0\nJAMA_SECRET={secret}")
load_dotenv(env_file)

if os.getenv("GDAL_LIBRARY_PATH"):
    GDAL_LIBRARY_PATH = os.getenv("GDAL_LIBRARY_PATH")

if os.getenv("GEOS_LIBRARY_PATH"):
    GEOS_LIBRARY_PATH = os.getenv("GEOS_LIBRARY_PATH")


MODSHIB_CREATE_ACCOUNT = True if os.getenv("MODSHIB_CREATE_ACCOUNT") == "1" else False
JAMA_USE_POSTGIS = True if os.getenv("JAMA_USE_POSTGIS") == "1" else False
JAMA_ROOT_URL_REDIRECT = os.getenv("JAMA_ROOT_URL_REDIRECT")
JAMA_CACHE_BACKEND = os.getenv("JAMA_CACHE_BACKEND") or "file"
JAMA_DB_ADAPTER = os.getenv("JAMA_DB_ADAPTER") or "sqlite"
JAMA_URL_BASE_PATH = os.getenv("JAMA_URL_BASE_PATH") or ""
JAMA_USE_MODSHIB = True if os.getenv("JAMA_USE_MODSHIB", "1") == "1" else False
JAMA_USE_CACHALOT = True if os.getenv("JAMA_USE_CACHALOT", "0") == "1" else False
JAMA_USE_WEBP = True if os.getenv("JAMA_USE_WEBP", "1") == "1" else False
JAMA_USE_ARK = True if os.getenv("JAMA_USE_ARK", "0") == "1" else False
JAMA_SQLITE_DB_PATH = os.getenv("JAMA_SQLITE_DB_PATH") or Path(VAR_DIR, "db.sqlite3")
JAMA_IIIF_PROCESSING_DIR = os.getenv(
    "JAMA_IIIF_PROCESSING_DIR", Path(VAR_DIR, "processing")
)
PARTIAL_UPLOADS_DIR = os.getenv("JAMA_PARTIAL_UPLOADS_DIR") or str(
    Path(VAR_DIR, "partial_uploads").resolve()
)
os.makedirs(PARTIAL_UPLOADS_DIR, exist_ok=True)

MEDIA_FILES_DIR = os.getenv("JAMA_FILES_DIR") or str(
    Path(VAR_DIR, "media_source_files").resolve()
)
os.makedirs(MEDIA_FILES_DIR, exist_ok=True)

TMP_THUMBNAILS_DIR = os.getenv("JAMA_TMP_THUMBNAILS_DIR") or tempfile.gettempdir()

JAMA_SITE = os.getenv("JAMA_SITE") or "http://localhost:8000/"

JAMA_IIIF_UPSCALING_PREFIX = (
    os.getenv("JAMA_IIIF_UPSCALING_PREFIX")
    if os.getenv("JAMA_IIIF_UPSCALING_PREFIX") is not None
    else "^"
)
IIIF_DIR = os.getenv("JAMA_IIIF_DIR") or str(Path(VAR_DIR, "iiif").resolve())
os.makedirs(IIIF_DIR, exist_ok=True)
IIIF_PATH_SEPARATOR = os.getenv("JAMA_IIIF_PATH_SEPARATOR") or os.path.sep


ARK_SERVER = os.getenv("JAMA_ARK_SERVER", "")
ARK_APP_ID = os.getenv("JAMA_ARK_APP_ID", "")
ARK_SECRET_KEY = os.getenv("JAMA_ARK_SECRET_KEY", "")
CACHE_FILE_LOCATION = os.getenv("CACHE_LOCATION", str(Path(VAR_DIR, "cache").resolve()))
CACHE_FILE_LOCATION = Path(CACHE_FILE_LOCATION).resolve()
os.makedirs(CACHE_FILE_LOCATION, exist_ok=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = (
    os.getenv("JAMA_SECRET") or "7d*_8c!d$vv963qpr45_x)@f2t-x6fu2&yi+m+d6s!p!lt+_j+"
)

# SECURITY WARNING: don't run with debug  on in production!
DEBUG = True if os.getenv("JAMA_DEBUG") == "1" else False

# This is the IIIF endpoint used to build manifests URLS
JAMA_IIIF_ENDPOINT = os.getenv("JAMA_IIIF_ENDPOINT") or "http://localhost/iip/IIIF="
# This is the IIIF endpoint used to proxy requests to the IIIF server
JAMA_IIIF_UPSTREAM_URL = os.getenv("JAMA_IIIF_UPSTREAM_URL") or JAMA_IIIF_ENDPOINT
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [JAMA_SITE[:-1]]

# Application definition

INSTALLED_APPS = [
    "corsheaders",
    "resources.apps.ResourcesConfig",
    "rpc.apps.RpcConfig",
    "django.contrib.auth",
    "revproxy.apps.RevProxyConfig",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "huey.contrib.djhuey",
    "authcli.apps.AuthcliConfig",
    "annotations.apps.AnnotationsConfig",
    "nui.apps.NuiConfig",
    "jama.apps.JamaConfig",
    "django_extensions",
    "django_cotton",
    "debug_toolbar",
    "django.contrib.humanize",
    "iiif.apps.IiifConfig",
]


if JAMA_USE_CACHALOT:
    INSTALLED_APPS.append("cachalot")

if JAMA_USE_MODSHIB:
    MODSHIB_SHOW_LOCAL_LOGIN = (
        True if os.getenv("MODSHIB_SHOW_LOCAL_LOGIN", "1") == "1" else False
    )
    MODSHIB_SHOW_SSO_LOGIN = (
        True if os.getenv("MODSHIB_SHOW_SSO_LOGIN", "0") == "1" else False
    )
    INSTALLED_APPS.append("modshib.apps.ModshibConfig")


AUTO_REGISTER_APPS = []
STATICFILES_DIRS = []
for app in os.getenv("JAMA_APPS", "").split(","):
    app = app.strip()
    if app:
        if app == "bibnum":
            INSTALLED_APPS.append("django_vite")
        INSTALLED_APPS.append(f"{app}.apps.{app.capitalize()}Config")
        AUTO_REGISTER_APPS.append(app)


MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "unpoly.contrib.django.UnpolyMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "X-Api-Key",
    "X-file-chunk",
    "X-file-hash",
    "X-file-name",
    "X-origin-dir",
    "X-Project",
]

ROOT_URLCONF = "jama.urls"

context_processors = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
]

if JAMA_USE_MODSHIB:
    context_processors.append("modshib.context_processors.modshib_context")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": context_processors,
        },
    },
]

WSGI_APPLICATION = "jama.wsgi.application"


if JAMA_DB_ADAPTER == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": JAMA_SQLITE_DB_PATH,
            "OPTIONS": {
                "init_command": (
                    "PRAGMA foreign_keys=ON;"
                    "PRAGMA journal_mode = WAL;"
                    "PRAGMA synchronous = NORMAL;"
                    "PRAGMA busy_timeout = 5000;"
                    "PRAGMA temp_store = MEMORY;"
                    "PRAGMA mmap_size = 134217728;"
                    "PRAGMA journal_size_limit = 67108864;"
                    "PRAGMA cache_size = 2000;"
                ),
                "transaction_mode": "IMMEDIATE",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis"
            if JAMA_USE_POSTGIS
            else "django.db.backends.postgresql",
            "HOST": os.getenv("JAMA_DB_HOST") or "localhost",
            "PORT": os.getenv("JAMA_DB_PORT") or "5432",
            "NAME": os.getenv("JAMA_DB_NAME") or "django",
            "USER": os.getenv("JAMA_DB_USER") or "django",
            "PASSWORD": os.getenv("JAMA_DB_PASSWORD") or "django",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_ROOT = os.getenv("JAMA_STATIC_ROOT") or Path(VAR_DIR, "static")
STATIC_URL = JAMA_URL_BASE_PATH + "/static/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {"format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"},
        "file": {"format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {"level": "INFO", "handlers": ["console"]},
    },
}

INTERNAL_IPS = [
    "127.0.0.1",
]

HUEY = {
    "huey_class": "huey.SqliteHuey",  # Huey implementation to use.
    "filename": Path(VAR_DIR, "huey.db").resolve(),
    "results": True,  # Store return values of tasks.
    "store_none": False,  # If a task returns None, do not save to results.
    "immediate": False,  # If DEBUG=True, run synchronously.
    "utc": True,  # Use UTC for all times internally.
    "consumer": {
        "workers": 1,
        "worker_type": "thread",
        "initial_delay": 0.1,  # Smallest polling interval, same as -d.
        "backoff": 1.15,  # Exponential backoff using this rate, -b.
        "max_delay": 10.0,  # Max possible polling interval, -m.
        "scheduler_interval": 1,  # Check schedule every second, -s.
        "periodic": True,  # Enable crontab feature.
        "check_worker_health": True,  # Enable worker health checks.
        "health_check_interval": 1,  # Check worker health every second.
    },
}

if JAMA_CACHE_BACKEND == "memcached":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": "127.0.0.1:11211",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": CACHE_FILE_LOCATION,
            "OPTIONS": {"MAX_ENTRIES": 10000},
        }
    }

LOGIN_REDIRECT_URL = "/ui/"

if "bibnum" in AUTO_REGISTER_APPS:
    # DJANGO_VITE_ASSETS_PATH = Path(BASE_DIR, "static", "bibnum")
    DJANGO_VITE_DEV_MODE = DEBUG
    DJANGO_VITE_STATIC_URL_PREFIX = "bibnum"
    # DJANGO_VITE_MANIFEST_PATH = Path(BASE_DIR, "static", "bibnum", "manifest.json")

if "ui" in AUTO_REGISTER_APPS:
    STATICFILES_DIRS.append(Path(BASE_DIR, "ui", "front", "dist"))
