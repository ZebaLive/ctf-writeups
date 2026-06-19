# CTF Writeups & Solutions

This repository serves as my **personal archive of Capture The Flag (CTF)** challenges that I've solved across different competitions.  
It contains **detailed writeups, exploit scripts, and technical notes** documenting how each problem was approached, analyzed, and solved.

🌐 **[Browse writeups online](https://ctf.zeba.dev)**

---

## 2025 Competitions

| Competition             | Rank         | Challenges       | Points                | Links                                                 |
| ----------------------- | ------------ | ---------------- | --------------------- | ----------------------------------------------------- |
| **ECSC 2025**           | 30th         | 11 (4 personal)  | 1459                  | [Writeups](https://ctf.zeba.dev/2025/ecsc/)           |
| **Mārtiņa-CTF 2025**    | 1st (Remote) | 44 (12 personal) | 15213 (4751 personal) | [Writeups](https://ctf.zeba.dev/2025/martina-ctf/)    |
| **openECSC 2025**       | 14th         | 21               | 3923                  | [Writeups](https://ctf.zeba.dev/2025/openecsc/)       |
| **BSides Vilnius 2026** | 4th          | 25               | 3050                  | [Writeups](https://ctf.zeba.dev/2025/bsides-vilnius/) |

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

## Disclaimer

All materials are provided for **educational and research purposes only**.  
Use responsibly and respect CTF competition rules.

## License

This project is licensed under the [MIT License](https://github.com/ZebaLive/ctf-writeups/blob/main/LICENSE).
