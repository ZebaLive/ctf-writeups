# CTF Writeups & Solutions

This repository serves as my **personal archive of Capture The Flag (CTF)** challenges that I've solved across different competitions.  
It contains **detailed writeups, exploit scripts, and technical notes** documenting how each problem was approached, analyzed, and solved.

🌐 **[Browse writeups online](https://zebalive.github.io/ctf-writeups/)**

---

## 2025 Competitions

| Competition          | Rank         | Challenges       | Points                | Links                                                                                          |
| -------------------- | ------------ | ---------------- | --------------------- | ---------------------------------------------------------------------------------------------- |
| **ECSC 2025**        | 30th         | 11 (4 personal)  | 1459                  | [Writeups](https://zebalive.github.io/ctf-writeups/2025/ecsc/) |
| **Mārtiņa-CTF 2025** | 1st (Remote) | 44 (12 personal) | 15213 (4751 personal) | [Writeups](https://zebalive.github.io/ctf-writeups/2025/martina-ctf/)                          |
| **openECSC 2025**    | 14th         | 21               | 3923                  | [Writeups](https://zebalive.github.io/ctf-writeups/2025/openecsc/)                             |

---

## Local Development

This site is built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

The project uses [asdf](https://asdf-vm.com/) for Python version management and [direnv](https://direnv.net/) for automatic environment activation. Dependencies are automatically installed when entering the directory.

```bash
# First time setup
asdf plugin add python

asdf install

direnv allow

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

---

## License

This project is licensed under the terms of the MIT license. 
All materials here are for **educational and research purposes only**. 
Use responsibly and respect competition rules.
