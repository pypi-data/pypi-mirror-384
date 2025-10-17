# 🧠 Hack4U Academy Courses Library

Una biblioteca **Python** para consultar cursos de la academia **Hack4U**.

---

## 📚 Cursos disponibles

* **Introducción a Linux** — *15 horas*
* **Personalización de Linux** — *3 horas*
* **Python Ofensivo** — *35 horas*
* **Introducción al Hacking** — *53 horas*
* **hacking Web** — *51 horas*

---

## ⚙️ Instalación

Instala el paquete usando **pip3**:

```bash
pip3 install hack4u
```

---

## 🚀 Uso básico

### 🔹 Listar todos los cursos

```python
from hack4u import list_courses

for course in list_courses():
    print(course)
```

---

### 🔹 Obtener un curso por nombre

```python
from hack4u import get_course_by_name

course = get_course_by_name("Introducción a Linux")
print(course)
```

---

### 🔹 Calcular duración total de los cursos

```python
from hack4u.utils import total_duration
```

---

## 🧬 Autor

Desarrollado con ❤️ por **Aurisssss for Hack4U Academy**
📧 Contacto: [soporte@hack4u.io](mailto:soporte@hack4u.io)
🌐 [https://hack4u.io](https://hack4u.io)

