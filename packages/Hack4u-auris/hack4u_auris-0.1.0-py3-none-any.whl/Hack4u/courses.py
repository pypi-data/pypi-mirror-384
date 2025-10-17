#!/usr/bin/env python3

class Course:

    def __init__(self, name, duration, link):
        self.name = name
        self.duration = duration
        self.link = link

    def __repr__(self): # permite representar los datos por indice, si se usa con for course in courses, representa como __str__
        return f"{self.name}, [{self.duration} horas]: ({self.link})"

courses = [
    Course("Introducción a Linux", 15, "https://hack4u.io/cursos/introduccion-a-linux/"),
    Course("Personalización de Linux", 3, "https://hack4u.io/cursos/personalizacion-de-entorno-en-linux/"),
    Course("Python Ofensivo", 35, "https://hack4u.io/cursos/python-ofensivo/"),
    Course("Introducción al Hacking", 53, "https://hack4u.io/cursos/introduccion-al-hacking/"),
    Course("Hacking Web", 51, "https://hack4u.io/cursos/hacking-web/")
]

#print(courses[2])   # permite mostrar asi debido al __repr__

def list_courses():
    for course in courses:  # mismo resultado con __repr__ y __str__
        print(course)

def search_course_by_name(name):
    for course in courses:
        if course.name == name:
            return course
    return '[!] Curso no encontrado'
