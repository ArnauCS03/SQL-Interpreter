# PandaQ
## Intérprete de consultas SQL
# Autor: Arnau Claramunt
---
### Práctica GEI-LP 2023-2024 Q1


- La práctica consiste en implementar un pequeño intérprete llamado PandaQ con las características principales:
    - Entrada: subconjunto de consultas SQL
    - Datos: archivos en formato csv
    - Tratamiento: librería pandas
    - Interficie: Streamlit

- Este proyecto está dividido en 8 tareas:
1. Integración básica: select *
2a. Campos: select varias columnas 
2b. Campos calculados: tener operaciones aritméticas básicas y alias
3. Order by: poder ordenar las filas
4. Where: aplicar filtros con operaciones relacionales y booleanas básicas
5. Inner join: poder juntar varias tablas
6. Tabla de símbolos: asignación, guardar consulta en una variable
7. Plots: poder mostrar gráficamente los valores numéricos
8. Subqueries: hacer subconsultas, otro select


- Para realizar la práctica se ha usado:
    - Python para el codigo y el correcto funcionamiento principal
    - Antlr4 para la gramática
    - Pandas libreria para tratar las tablas de datos
    - Streamlit para mostrar una interficie grafica

---

#### Requisitos de la práctica

- Tener un directorio `data` donde contiene todos los ficheros con las tablas .csv
    - El directorio de la práctica contiene:  `pandaQ.g4`  `pandaQ.py`  `data`
    - El fichero .g4 contiene la gramática y el .py el script principal con estilo PEP 8, donde se implementan 
      los visitors y el tratamiento con pandas y la interficie de Streamlit
- También tener instalado el antlr4 y Streamlit


---

#### Compilación y Ejecución

Para ver la interfaz gráfica de la práctica y poder introducir las queries, hay que ejecutar en una terminal Linux:

`streamlit run pandaQ.py`

Para compilar, solo hay que hacerlo cuando se ha cambiado la gramática en el fichero .g4, y no es necesario hacerlo
ya que la práctica entregada ya está compilada previamente. Pero la comanda es:

`antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4`


---

#### Usage

Una vez abierta la ventana de Streamlit, hay que introducir las consultas SQL en el espacio para el texto y pulsar el botón de enviar.
Después se muestra la tabla como resultado o la gráfica asociada.

Para las consultas, en la parte inferior donde se puede introducir el texto, hay ejemplos de consultas, para que le sea fácil as usuario copiarlas
o servirle como inspiración.

---

#### Aclaramientos:

- Cuando se muestra los valores de las tablas en Streamlit los valores de más de 3 cifras llevan coma para indicar que son miles: por ejemplo el salary 4200  se muestra 4,200.  Pero es algo solo visual, por tanto si se quiere hacer un where hay que poner los valores sin la coma

Ejemplo de tabla jobs.csv (resultado de una query en la práctica):
    
| job_id | job_title | min_salary | max_salary |
| ------ | --------- | ---------- | ---------- |
| 1	| Public Accountant | 4,200	| 9,000 |
| 2 | Accounting Manager | 8,200 | 16,000 |


- La práctica no contiene control de errores, se asume que las queries son correctas, o como los juegos de pruebas mostrados en el enunciado: https://github.com/gebakx/lp-pandaQ-23

- En la tarea 6, se usa el *session_state* de streamlit. Es como una variable global de la sesión que está activa y se acuerda de lo que guardas

- El Plot solo se puede hacer de datos numéricos, por lo tanto, la consulta que se haga previamente en una variable tiene que contener alguna columna numérica

---

#### Funcionalidades Extra


- Poner abajo de las consultas ejemplos en SQL escritos en Markdown (este `README.md` también está hecho con este lenguaje) para que el usuario pueda copiarlos o tener una guía

- Hacer que las palabras clave se puedan escribir todo en mayúsculas, en el codigo hay .lower() que lo convierte a minusculas, 
  para poder abrir bien el fichero con las tablas o el nombre de las columnas  

- Hacer plots, con otros tipos de plot, por defecto si se hace `plot q;` hace un line_chart que es el que se pide en el apartado 7.
  Los que yo he añadido son:
  `scatter q;`  muestra los puntos del gráfico
  `area q;`     muestra el área bajo la línea del gráfico
  `bar q;`      muestra un diagrama de barras


- La posibilidad de hacer una funcionalidad en el where que no se especifica: poder hacer dos veces un boolenano not not por ejemplo. Anteriormente no lo tenia permitido, 
  pero lo cambié para que sea posible

- Poder enviar la consulta sin pulsar el botón de enviar, con el atajo:  `ctrl+Enter` 


---


#### Mejoras extra pendientes

Principalmente, son ideas que he tenido y que al final no las he hecho o no he tenido suficiente tiempo para implementarlas.

- Un botón para eliminar el texto escrito en la interfaz gráfica. Es un poco lento eliminar manualmente las líneas de las consultas cada vez
  especialmente si son consultas largas o de varias líneas.

- Crea un desplegable en el lateral que contenga información o créditos o un enlace al enunciado de la práctica en el GitHub

- Que en el alias deje escribir un número, de momento da error de sintaxis

- Un botón que genere una query aleatoria, por si el usuario se ha quedado sin ideas o tiene curiosidad

- Cuando se hace un order by, que se modifique internamente el orden de las filas, para que si luego se hace un plot, salga con un orden correcto

- Indicarle al usuario, todos los nombres de los ficheros disponibles, para que sepa que tablas hay y las pueda consultar.


