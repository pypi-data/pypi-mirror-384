
# SpeakUB 📚

A modern, feature-rich terminal EPUB reader with **Text-to-Speech** support, built with Rich/Textual for a beautiful CLI experience.

## ✨ Features

- 🎨 **Rich Terminal UI** - Beautiful interface with Rich and Textual
- 📖 **Full EPUB Support** - Handles EPUB 2 and EPUB 3 formats
- 🔊 **Text-to-Speech** - Built-in TTS using Microsoft Edge-TTS
- 📑 **Smart Navigation** - Table of contents with hierarchical chapters
- 💾 **Progress Tracking** - Automatically saves your reading position
- 🎯 **Seamless Reading** - Navigate between chapters without interruption
- 🖼️ **Image Support** - View embedded images (optional)
- ⌨️ **Keyboard Shortcuts** - Efficient navigation with familiar keys
- 🎛️ **TTS Controls** - Play, Pause, Stop with speed/volume control
- 🗣️ **Chinese Pronunciation Corrections** - Optional pronunciation correction system

## 🚀 Installation

### Quick Install
```bash
pip install speakub
```

### Development Install
```bash
git clone https://github.com/eyes1971/SpeakUB.git
cd SpeakUB
pip install -e .
```

### With TTS Support
```bash
pip install speakub[tts]
```

### With All Features
```bash
pip install speakub[all]
```

## �️ Desktop Integration

SpeakUB automatically creates a desktop entry on first run, allowing you to:
- Right-click EPUB files and select "Open with SpeakUB"
- Double-click EPUB files to open them directly

The desktop entry uses `speakub %f` command, which automatically detects and launches in your preferred terminal emulator.

## �📋 Requirements

- Python 3.8+
- Terminal with Unicode support

### Optional Dependencies

- **TTS**: `edge-tts` and `pygame` for text-to-speech
- **Images**: `fabulous` and `Pillow` for image display

## 🎮 Usage

### Basic Usage
```bash
speakub book.epub
```

### Dump to Text
```bash
speakub book.epub --dump --cols 80
```

## ⌨️ Keyboard Shortcuts

### Global Controls
| Key | Action |
|-----|---------|
| `Esc` / `q` | Quit application |
| `Tab` | Switch focus between panels |
| `F1` | Toggle table of contents |
| `F2` | Toggle TTS panel |

### Table of Contents (TOC)
| Key | Action |
|-----|---------|
| `↑` / `↓` | Navigate chapters |
| `PgUp` / `PgDn` | Page up/down |
| `Enter` / `→` | Open chapter or expand group |
| `←` | Collapse group |

### Content Reading
| Key | Action |
|-----|---------|
| `↑` / `↓` | Scroll content (seamless across chapters) |
| `PgUp` / `PgDn` | Page up/down |
| `Home` / `End` | Go to start/end of chapter |
| `i` | Open images in browser (if available) |

### TTS Controls
| Key | Action |
|-----|---------|
| `Space` / `p` | Play/Pause |
| `s` | Stop |
| `+` / `=` | Increase volume |
| `-` | Decrease volume |
| `[` | Decrease speed |
| `]` | Increase speed |
| `←` / `→` | Navigate TTS controls |

## 🏗️ Architecture

```
speakub/
├── speakub/              # Main package
│   ├── core/             # Core functionality
│   │   ├── epub_parser.py      # EPUB parsing
│   │   ├── content_renderer.py # HTML to text conversion (with adaptive cache)
│   │   ├── chapter_manager.py  # Chapter navigation
│   │   └── progress_tracker.py # Reading progress
│   ├── tts/              # Text-to-Speech
│   │   ├── engine.py           # TTS abstraction
│   │   ├── edge_tts_provider.py # Edge-TTS with state machine
│   │   ├── ui/runners.py       # TTS workers (English comments)
│   │   └── audio_player.py     # Audio playback
│   ├── ui/               # User interfaces
│   │   └── widgets/            # Reusable components
│   ├── utils/            # Utility functions
│   │   ├── performance_monitor.py # Performance monitoring
│   │   └── text_utils.py        # Text processing utilities
│   ├── cli.py            # Command-line interface
│   └── desktop.py        # Desktop integration
├── tests/                # Test suite
│   ├── test_performance_benchmarks.py # Performance benchmarks
│   └── test_tts_state_machine.py      # TTS state machine tests
└── docs/                 # Documentation
```

## 🔊 Text-to-Speech Features

The TTS system provides:

- **Multiple Voices** - Support for various languages and voices
- **Speed Control** - Adjust playback speed (0.5x - 2.0x)
- **Volume Control** - Fine-tune audio levels
- **Chapter Navigation** - Skip to previous/next chapters
- **Progress Tracking** - Visual progress bar with time display
- **Background Processing** - Non-blocking audio synthesis

### TTS Panel Controls

```
┌──────────────────────────────────────────┐
│ TTS: PLAYING (Smooth) | 23% | Vol: 100% | Speed: +30% | Pitch: +0Hz │
└──────────────────────────────────────────┘
```

## 🛠️ Configuration

### Automatic Configuration

The reader automatically saves:
- Reading progress for each book
- Last position in each chapter
- TTS settings (volume, speed)

Progress is stored in `~/.speakub_progress.json`

### Manual Configuration

You can customize the reader's behavior through environment variables:

#### Display Settings
```bash
# Set default content width (default: 80)
export SPEAKUB_WIDTH=100

# Enable/disable trace logging
export SPEAKUB_TRACE=1

# Set maximum cache size for content rendering
export SPEAKUB_CACHE_SIZE=100
```

#### TTS Configuration
```bash
# Set default TTS voice
export SPEAKUB_VOICE="en-US-AriaRUS"

# Set default TTS speed (0.5-2.0)
export SPEAKUB_TTS_SPEED=1.2

# Set default TTS volume (0-100)
export SPEAKUB_TTS_VOLUME=80
```

#### Performance Tuning
```bash
# Set chapter cache size (default: 50)
export SPEAKUB_CHAPTER_CACHE=100

# Enable/disable background processing
export SPEAKUB_BACKGROUND=1

# Set polling frequency for UI updates (milliseconds)
export SPEAKUB_POLL_INTERVAL=100
```

### Configuration File

Create a configuration file at `~/.speakub_config.json`:

```json
{
  "display": {
    "width": 100,
    "trace": false,
    "cache_size": 100
  },
  "tts": {
    "default_voice": "en-US-AriaRUS",
    "speed": 1.2,
    "volume": 80
  },
  "performance": {
    "chapter_cache": 100,
    "background_processing": true,
    "poll_interval": 100
  }
}
```

### Cache Management

The reader implements intelligent caching to improve performance:

- **Chapter Content Cache**: Stores parsed chapter content (LRU with 50 entries)
- **Width Calculation Cache**: Caches display width calculations (LRU with 100 entries)
- **Adaptive Renderer Cache**: Caches HTML-to-text renderers by width with TTL and statistics

#### Adaptive Cache Features

The new adaptive cache system provides:

- **TTL (Time-To-Live)**: Automatically expires cached items after 5 minutes to prevent memory leaks
- **LRU Eviction**: Removes least recently used items when cache is full
- **Performance Statistics**: Tracks hit rates, cache size, and access patterns
- **Memory-Aware Sizing**: Automatically adjusts cache size based on system memory

### Performance Monitoring

SpeakUB includes built-in performance monitoring to track system health:

```bash
# Run performance benchmarks
python tests/test_performance_benchmarks.py

# Monitor cache statistics in real-time
from speakub.core.content_renderer import ContentRenderer
renderer = ContentRenderer()
stats = renderer.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1%}")
```

#### Performance Metrics

- **Cache Hit Rate**: Percentage of cache requests that hit
- **Memory Usage**: Current and peak memory consumption
- **TTS State Changes**: Number of TTS state transitions
- **Render Time**: Time spent rendering content

To clear all caches, delete the progress file:
```bash
rm ~/.speakub_progress.json
```

## 🗣️ Chinese Pronunciation Corrections

SpeakUB supports optional pronunciation corrections for Chinese text. This feature allows you to customize how specific Chinese characters or words are pronounced by the TTS system.

### Setting Up Corrections

1. **Automatic Setup**: The first time you run SpeakUB, it will create a corrections file at `~/.config/speakub/corrections.json` with instructions and examples.

2. **Manual Setup**: You can also create the file manually:
```bash
mkdir -p ~/.config/speakub
touch ~/.config/speakub/corrections.json
```

### Corrections File Format

The corrections file is a JSON object where each key is the original text and the value is the corrected pronunciation:

```json
{
  "_comment": "Chinese Pronunciation Corrections Configuration",
  "_instructions": "Add your correction rules below in format: 'original': 'corrected'",
  "_examples": {
    "生長": "生掌",
    "長": "常"
  },
  "生長": "生掌",
  "長": "常",
  "银行": "yínháng",
  "给予": "jǐyǔ"
}
```

### How It Works

- **Keys starting with `_`**: These are treated as comments and instructions, not correction rules
- **Regular keys**: These are the actual correction mappings
- **Automatic filtering**: The system automatically filters out instruction keys when loading corrections
- **Optional feature**: If the corrections file doesn't exist, SpeakUB works normally without corrections

### Common Use Cases

- **Polyphonic characters**: Characters that can be pronounced differently in different contexts
- **Proper nouns**: Names, places, or terms that need specific pronunciation
- **Technical terms**: Specialized vocabulary that needs consistent pronunciation
- **Regional variations**: Different pronunciation preferences

### Examples

```json
{
  "行": "xíng",        // 行走 (walking)
  "银行": "yínháng",   // 银行 (bank)
  "银行家": "yínhángjiā", // 银行家 (banker)
  "长": "cháng",       // 长度 (length)
  "长江": "chángjiāng" // 长江 (Yangtze River)
}
```

### Tips

- Use Pinyin with tone marks for best results
- Test corrections with short text first
- The corrections are applied before TTS processing
- You can have multiple corrections for the same character in different contexts

## 📋 Version History

### Version 1.1.0 (Latest)
- ✨ **New Feature**: Added Chinese pronunciation corrections system
- 🔧 **Enhancement**: Improved content widget with better text processing
- 🐛 **Bug Fix**: Fixed Flake8 linting issues
- 📚 **Documentation**: Updated README with corrections usage guide
- 🏗️ **Build**: Updated build system and version management

### Version 1.0.0
- 🎉 Initial release with full EPUB reading capabilities
- 🔊 Text-to-Speech support with Microsoft Edge-TTS
- 🎨 Rich terminal UI with Textual framework
- 📑 Smart table of contents navigation
- 💾 Automatic progress tracking
- 🎛️ Comprehensive TTS controls

## 🔧 Development

### Setup Development Environment
```bash
git clone https://github.com/eyes1971/SpeakUB.git
cd SpeakUB
pip install -e .[dev]
pre-commit install
```

### Development Tools
The `tools/` directory contains helpful scripts for development and debugging:

```bash
# Check available TTS voices
python tools/check_voices.py

# Debug voice data structures
python tools/debug_voices.py

# Test TTS provider functionality
python tools/simple_test.py

# Interactive voice selector demo
python tools/voice_selector_demo.py

# Verify UI layout changes
python tools/simple_layout_check.py
```

See [tools/README.md](tools/README.md) for detailed information about each tool.

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black speakub/
isort speakub/
flake8 speakub/
```

### Type Checking
```bash
mypy speakub/
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository at [https://github.com/eyes1971/SpeakUB](https://github.com/eyes1971/SpeakUB)
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

- **Author**: Sam Weng
- **Email**: eyes1971@gmail.com
- **GitHub**: [https://github.com/eyes1971/SpeakUB](https://github.com/eyes1971/SpeakUB)

## 🙏 Acknowledgments

- **Rich** - For the beautiful terminal UI framework
- **Textual** - For the modern TUI components  
- **BeautifulSoup** - For robust HTML parsing
- **Edge-TTS** - For high-quality text-to-speech
- **html2text** - For HTML to text conversion

## 🐛 Known Issues

- Image display requires `fabulous` and may not work in all terminals
- TTS seeking is not supported with the pygame audio backend
- Very large EPUB files may consume significant memory

## 📚 Similar Projects

- [epr](https://github.com/wustho/epr) - CLI EPUB reader
- [epub](https://github.com/rupa/epub) - Simple EPUB reader

---

**Happy Reading!** 📖✨

For more information, visit our [documentation](https://speakub.readthedocs.io/) or [report issues](https://github.com/eyes1971/SpeakUB/issues).
