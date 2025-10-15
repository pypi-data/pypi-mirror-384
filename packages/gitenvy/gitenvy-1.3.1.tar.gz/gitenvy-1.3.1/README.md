# 🧰 gitenvy

Securely store, version, and share your `.env` files using Git repositories — with built-in encryption and version tracking.

---

## ✨ Features

- 🔐 AES (Fernet) encryption for `.env` files  
- 🕓 Versioning — every push creates a new version  
- 🧩 Multi-repo support — manage multiple environments or teams easily  
- 🌿 Branch-aware cloning and pushing  
- ⚙️ Simple YAML-based config  
- 🪄 Fully CLI-driven workflow  

---

## 📦 Installation

```bash
pip install gitenvy
```

---

## ⚙️ Configuration

Configuration is stored in:

```
~/.gitenvy/config.yml
```

Example:

```yaml
configs:
  dotenvy-store:
    branch: feature-test-checkout
    key_path: ~/.gitenvy/keys/dotenvy-store.key
    repo_path: C:\Users\swapn/.gitenvy/repos\dotenvy-store
    repo_url: https://github.com/swapnilravi10/dotenvy-store
default: dotenvy-store
```

Each `config` entry represents one git-backed store for `.env` files.  
You can manage multiple repositories and set one as default.
You do not manually create the config, instead use the init command.

---

## 🧩 Usage

### 🏁 Initialize gitenvy

Initialize and configure your environment store.

```bash
gitenvy init <repo_url>
```

#### Examples

```bash
# Clone and initialize repo
gitenvy init git@github.com:your-org/env-storage.git

# Clone to a custom local path
gitenvy init git@github.com:your-org/env-storage.git --path ~/.gitenvy/repos/custom-repo

# Clone and checkout a specific branch
gitenvy init git@github.com:your-org/env-storage.git --branch feature/config-refactor
```

🗂️ This automatically saves the repo info in your config file.

---

### 🚀 Push a .env file

Push a local `.env` file to your encrypted environment store.

```bash
gitenvy push --project <PROJECT> --env <ENV>
```

#### Examples

```bash
# Push using the default repo config
gitenvy push --project myapp --env dev

# Push using a specific repo config
gitenvy push --project myapp --env prod --repo-name dotenvy-store
```

Each push creates a new version under:
```
<repo>/<project>/<env>/<version>/
```

---

### 📥 Pull and decrypt a .env file

Retrieve and decrypt an environment file from the repo.

```bash
gitenvy pull --project <PROJECT> --env <ENV> [--version <VERSION>] [--out-path <PATH>] [--repo-name <REPO_NAME>]
```

#### Examples

```bash
# Pull latest .env for a project
gitenvy pull --project myapp --env dev

# Pull a specific version
gitenvy pull --project myapp --env dev --version 3

# Pull and save to a custom path
gitenvy pull --project myapp --env dev --out-path ./envs/.env.dev

# Pull from a specific repo config
gitenvy pull --project myapp --env staging --repo-name dotenvy-store
```

---

### 📋 List projects, environments, or versions

List what’s stored in your encrypted repo.

```bash
gitenvy list
gitenvy list --project <PROJECT>
gitenvy list --project <PROJECT> --env <ENV>
```

- `gitenvy list` — Lists all projects.  
- `gitenvy list --project <PROJECT>` — Lists all environments for a project.  
- `gitenvy list --project <PROJECT> --env <ENV>` — Lists all versions for an environment.

---

### ⚙️ Manage config defaults and keys

#### Set the default repo
```bash
gitenvy set-default <REPO_NAME>
```
Sets which repo is used when no `--repo-name` is specified.

#### Get the Fernet key for a repo
```bash
gitenvy get-key <REPO_NAME>
```

#### Set the Fernet key for a repo
```bash
gitenvy set-key <REPO_NAME> <KEY>
```

---
## 👥 Working with a Team

When multiple teammates need to manage `.env` files securely in the same repo, `gitenvy` makes collaboration simple.

---

### 🧑‍💻 Team Member 1 — Initializes and Pushes

1. **Initialize the repo**
   ```bash
   gitenvy init git@github.com:your-org/your-storage-repo.git
   ```

2. **Push a `.env` file**
   ```bash
   gitenvy push --project <PROJECT> --env <ENV>
   ```

3. **Get the encryption key**
   ```bash
   gitenvy get-key <REPO_NAME>
   ```

   Share this key **securely** with your teammates (e.g., using a secret manager or encrypted channel).  
   ⚠️ **Never commit or share the key publicly.**

---

### 👩‍💻 Team Member 2 — Sets Up and Uses the Same Key

1. **Initialize the same repo**
   ```bash
   gitenvy init git@github.com:your-org/your-storage-repo.git
   ```

2. **Set the Fernet key received from teammate**
   ```bash
   gitenvy set-key <REPO_NAME> <KEY>
   ```

3. **Start using it**
   ```bash
   gitenvy pull --project <PROJECT> --env <ENV>
   gitenvy push --project <PROJECT> --env <ENV>
   ```

Now both teammates can **encrypt, push, and pull** environment files securely using the same shared key.

---

## 🔄 Example Multi-Repo Workflow

You can maintain multiple repo configs and easily switch between them:

```bash
# Initialize two repos
gitenvy init git@github.com:org1/env-store.git
gitenvy init git@github.com:org2/env-store.git --branch secure-configs

# Push to a specific repo
gitenvy push --project webapp --env staging --repo-name org2-env-store

# Set default repo
gitenvy set-default org1-env-store
```

---

## 🧠 Notes

- Supports both **HTTPS** and **SSH** Git URLs seamlessly.
- `.env` files are encrypted before every commit.
- Each repo stores its own encryption key at `~/.gitenvy/keys/<repo>.key`.

---

## 🛠️ Tech Stack

- Python 3.10+
- [Click](https://click.palletsprojects.com/) for CLI
- [GitPython](https://gitpython.readthedocs.io/) for Git operations
- [cryptography](https://cryptography.io/) for encryption

---

## 📜 License

This project is licensed under the [MIT License](./LICENSE).

---

## 🙌 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check out the [issues page](https://github.com/swapnilravi10/gitenvy/issues) to get started.
Before contributing, please read our [Code of Conduct](CODE_OF_CONDUCT.md).  

Thank you for helping improve Gitenvy! 💜