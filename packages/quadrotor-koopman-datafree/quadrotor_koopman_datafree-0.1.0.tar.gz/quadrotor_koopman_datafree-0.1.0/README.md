# quadrotor_koopman_datafree

A lightweight Python package for **Koopman-based data-free lifting of quadrotor dynamics on SE(3)**. This package analytically constructs lifted linear representations of quadrotor dynamics without requiring any trajectory data or machine learning. It supports both **NumPy** (numerical) and **CasADi** (symbolic) versions of the Koopman lifting maps for control and Model Predictive Control (MPC) applications.

---

## ✨ Key Features

- ✅ Koopman state lifting on **SE(3)** for quadrotors  
- ✅ Analytical (data-free) Koopman operators  
- ✅ Compatible with **linear MPC, LQR, and optimal control**  
- ✅ Supports **CasADi symbolic modeling**  
- ✅ Includes utilities for state conversion, noise, rotation matrices  
- ✅ Maps between actual and lifted control spaces (`u ↔ U`, `u_tilde`)  
- ✅ Clean and modular implementation  

---

## 📦 Installation

From PyPI:
```bash
pip install quadrotor_koopman_datafree
