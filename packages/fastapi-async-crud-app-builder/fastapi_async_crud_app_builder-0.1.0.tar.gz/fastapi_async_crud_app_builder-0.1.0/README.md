# 🧩 FastAPI Builder

Build a fully functional **FastAPI + SQLModel** application dynamically from a simple JSON (or Python dict) configuration.  
Define your models, authentication, and app settings in one place — no boilerplate required.

---

## 🚀 Features

- **Config-driven** app generation (models, auth, CRUD endpoints)
- **SQLModel** ORM integration
- **JWT authentication** baked in
- **Role-level security (RLS)** with configurable `owner_id`
- Optional **timestamps** and **soft deletes**
- Works with any **SQLAlchemy-compatible database** (SQLite, Postgres, MySQL, etc.)
- Lightweight — no CLI, no code generation, just pure runtime FastAPI objects

---

## 📦 Installation

```bash
pip install fastapi-builder
