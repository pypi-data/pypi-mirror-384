<p align="center">
    <img src="https://raw.githubusercontent.com/jorgelizarazo94/NestlingGrowthApp/7a9916a809009ea6359db6b8e02645db32c0a28d/nestling_app/api/assets/ngapp_log.png" alt="Nestling Growth App" width="200px">
</p>

# 🐣 Nestling Growth App

The Nestling Growth App is a web-based tool designed for ornithologists, ecologists, and researchers working on nestling development. It allows users to visualize and model growth metrics such as weight, wing, and tarsus length using classic biological growth functions:
- Logistic  
- Gompertz  
- Richards  
- Von Bertalanffy  
- Extreme Value Function (EVF)  

It includes language support (English, Spanish, Portuguese) and dynamic content based on user selection.

---

## ✨ Features

✔ Upload your own CSV with growth data  
✔ Dynamically select variables (e.g., weight, wing, tarsus)  
✔ Automatically fits multiple growth models  
✔ Exports results (tables and graphs) as CSV and PNG  
✔ Interactive interface with tabs for **Weight** and **Wing & Tarsus**  
✔ Multilingual: 🇬🇧 English, 🇪🇸 Español, 🇵🇹 Português  

---

## 📥 Input Format

Your CSV must include:
- A column for day (e.g., `Day`, `Age`, `Día`, etc.)
- At least one of the following: `Weight`, `Wing`, or `Tarsus`

---

## 📤 Output

- Growth curves with fitted models  
- AIC/BIC comparison tables  
- Model parameters including k and T  
- Exportable graphs (PNG, 300dpi) and results table (CSV)  

---

## 📦 Installation (One Time Setup)

Just install once using one of the following methods. After that, you can launch the app anytime by running:

```
nestling-app
```

### ✅ Option 1: PyPI (recommended)

```bash
pip install nestling-growth-app
```

### ✅ Option 2: Install directly from GitHub

```bash
pip install git+https://github.com/jorgelizarazo94/NestlingGrowthApp.git
```

### 🧪 Option 3: Conda environment (clean setup)

```bash
conda create -n nestlings python=3.9 -y
conda activate nestlings
pip install git+https://github.com/jorgelizarazo94/NestlingGrowthApp.git
```

### 🧑‍💻 Option 4: Clone the repository

```bash
git clone https://github.com/jorgelizarazo94/NestlingGrowthApp.git
cd NestlingGrowthApp
pip install -e .
```

Then launch the app with:

```
nestling-app
```

Once started, the app will open automatically or can be accessed via:  
[http://localhost:8050](http://localhost:8050)

---

## 🌐 Live Deployment

You can try the online version (if available) here:  
🔗 [Nestling Growth App on Render](https://nestling-growth-app.onrender.com)

---

## 🗂️ Folder Structure

```
NestlingGrowthApp/
│
├── nestling_app/
│   ├── api/
│   │   ├── app.py              # Main Dash app
│   │   ├── translations.py     # Multilingual content
│   │   └── assets/             # Images and logo
│   ├── models/
│   │   └── growth_models.py    # Growth models
│   ├── components/             # (Optional) Modular UI parts
│   ├── data/                   # Example datasets
├── setup.py
├── README.md
├── requirements.txt
```

---

## 📊 Example Datasets

Sample data for testing is available here:  
[📁 Sample Data Folder](https://github.com/jorgelizarazo94/NestlingGrowthApp/tree/d910ec6f4befb22dc730157e6a9bd1a66e7de863/nestling_app/data)

---

## 📬 Contact

For questions, suggestions, or collaborations:  
📧 jorge.lizarazo.b@gmail.com  
🐛 [GitHub Issues](https://github.com/jorgelizarazo94/NestlingGrowthApp/issues)

---

<p align="center">
  <a href="https://wildlabs.net/" target="_blank">
    <img src="https://raw.githubusercontent.com/jorgelizarazo94/NestlingGrowthApp/7a9916a809009ea6359db6b8e02645db32c0a28d/nestling_app/api/assets/logo.png" width="800px" />
  </a>
</p>