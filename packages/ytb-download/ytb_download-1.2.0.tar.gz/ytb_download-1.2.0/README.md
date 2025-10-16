# YouTube Downloader

[![PyPI](https://img.shields.io/pypi/v/ytb-download?registry_uri=https://pypi.org/simple/)](https://pypi.org/project/ytb-download/)

Un utilitaire simple et efficace pour télécharger des vidéos YouTube et des playlists entières avec choix de qualité et répertoire personnalisable.


## Installation

### Installation depuis pypi

```bash
pip install ytb-download
```

## Utilisation

### Commande de base

```bash
# Vidéo unique
ytb-download "https://www.youtube.com/watch?v=VIDEO_ID"

# Playlist entière
ytb-download "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Options disponibles

| Option | Raccourci | Description | Défaut |
|--------|-----------|-------------|---------|
| `--quality` | `-q` | Qualité vidéo (worst, 360p, 480p, 720p, 1080p, 1440p, 2160p, best) | best |
| `--output` | `-o` | Répertoire de téléchargement | ~/Downloads/youtube-downloads |
| `--audio-only` | `-a` | Télécharger uniquement l'audio | False |
| `--format` | `-f` | Format de sortie | mp4 |
| `--info` | `-i` | Afficher les informations sans télécharger | False |
| `--list-formats` | `-l` | Lister tous les formats disponibles | False |
| `--playlist-start` | `-ps` | Index de début pour les playlists | 1 |
| `--playlist-end` | `-pe` | Index de fin pour les playlists | None |
| `--list-videos` | `-lv` | Lister toutes les vidéos d'une playlist | False |

### Exemples d'utilisation

#### Téléchargement de vidéo unique
```bash
ytb-download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### Téléchargement de playlist entière
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl"
```

#### Téléchargement partiel de playlist (vidéos 5 à 10)
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl" -ps 5 -pe 10
```

#### Téléchargement playlist en audio MP3 uniquement
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl" -a -f mp3
```

#### Lister les vidéos d'une playlist
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl" -lv
```

#### Informations d'une playlist
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl" -i
```

#### Téléchargement playlist en 720p dans dossier spécifique
```bash
ytb-download "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl" -q 720p -o "C:\Downloads\MaPlaylist"
```

## Organisation des fichiers

### Vidéo unique
```
Downloads/youtube-downloads/
└── Titre de la vidéo.mp4
```

### Playlist
```
Downloads/youtube-downloads/
└── Nom de la Playlist/
    ├── 01 - Première vidéo.mp4
    ├── 02 - Deuxième vidéo.mp4
    └── 03 - Troisième vidéo.mp4
```

## Formats supportés

### Vidéo
- mp4 (défaut)
- webm
- mkv
- avi

### Audio
- mp3 (défaut)
- m4a
- wav
- aac

## Qualités disponibles

- `worst` : Plus basse qualité disponible
- `360p` : 360p maximum
- `480p` : 480p maximum
- `720p` : 720p maximum (HD)
- `1080p` : 1080p maximum (Full HD)
- `1440p` : 1440p maximum (2K)
- `2160p` : 2160p maximum (4K)
- `best` : Meilleure qualité disponible (défaut)

## Prérequis

- Python 3.8+
- FFmpeg pour la conversion audio (généralement forcément pas réquise)

### Vidéos non disponibles dans une playlist
L'outil ignore automatiquement les vidéos privées ou supprimées et continue avec les suivantes.

### Playlist très longue
Utilisez les options `-ps` et `-pe` pour télécharger par segments.

## Licence

MIT License - voir le fichier LICENSE pour plus de détails.

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou soumettre une pull request.
