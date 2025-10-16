# ⚙️ Cogworks Engine

**Cogworks Engine** is a small, personal **2D Python game engine** I created for fun.
It’s designed to make building 2D games in Python **quick, enjoyable, and structured**, using **Pygame** for rendering and input, and **Pymunk** for physics simulation.

📘 **Documentation:** [cog-works-engine-docs.vercel.app](https://cog-works-engine-docs.vercel.app)

---

## 🚀 Features

🧩 Component-Based GameObjects – Build flexible and reusable entities with custom behaviour.

⚙️ Physics Integration – Built-in Rigidbody2D and Collider components powered by Pymunk for realistic 2D physics.

🧲 Trigger Collider – Independent collision detection for triggers and interactions without physics simulation.

💨 Particle Effects – Customisable particle systems for explosions, muzzle flash, blood effects.

🔊 Audio Source – Play and control sound effects or background music through component-based audio sources.

🧠 Script Component – Attach Python scripts directly to GameObjects to define custom behaviour and logic.

🎬 Scene Management – Manage levels, menus, and transitions with ease.

🎮 Input Management – Unified keyboard and mouse input handling.

🧱 Extensible & Modular Design – Add new components, systems, and tools without breaking the engine’s core structure.

---

## 📦 Installation

Install via **pip**:

```bash
pip install cogworks
```

---

## 🕹️ Quick Start

Here’s a minimal example to get started:

```python
from cogworks import Engine

# Create a new engine instance
engine = Engine(
    width=800,
    height=600,
    caption="My Game",
    fps=60,
)

# Run the engine
engine.run()
```

---

## 📚 Learn More

Visit the full documentation for examples and guides:
👉 [https://cog-works-engine-docs.vercel.app](https://cog-works-engine-docs.vercel.app)

---