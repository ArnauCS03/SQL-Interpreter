import pandas as pd
import streamlit as st

from antlr4 import *
from pandaQLexer import pandaQLexer
from pandaQParser import pandaQParser
from pandaQVisitor import pandaQVisitor

             
class EvalPandaQVisitor(pandaQVisitor):  

    def __init__(self):
        self.df = pd.DataFrame()  # guardar el dataframe (tabla) del fichero leido, ya que varios visitors lo necesitan tratar
        
    
    def visitQuerySola(self, ctx):
        [query, _] = list(ctx.getChildren()) 
        return self.visit(query)  

    # nos guardamos la variable en el estado (session) y le asociamos/guardamos la query que se introduce
    def visitAssig(self, ctx):
        nombre_variable = ctx.var().getText()

        # ejecutar la query
        resultado_query = self.visit(ctx.query())

        # guardar el resultado en la session de Stremlit (es global) se mantiene mientras esta activa la sesion
        st.session_state[nombre_variable] = resultado_query

        # guardar el resultado en el atributo de dataframe
        self.df = resultado_query 

        return resultado_query

    def visitPlotInstr(self, ctx):
        return self.visit(ctx.plot())


    # devuelve todo el dataframe y posiblemente tratado con  inner join / where / order by
    def visitSelectAll(self, ctx):

        # tenemos un nombre de tabla o una variable con una tabla
        tabla_a_abrir = self.visit(ctx.taula())        # las tablas donde se lee, tienen que estar en una carpeta llamada:  data  que estara dentro del directorio de la gramatica y este script
        self.df = tabla_a_abrir

        # si hay uno o varios inner join
        for inner in ctx.innerJoin():
            self.visit(inner)

        # si hay where
        if ctx.whereInstr() is not None:
            self.visit(ctx.whereInstr())  # filtra el dataframe con las condiciones
        
        # si hay order by
        if ctx.orderBy() is not None:       
            self.visit(ctx.orderBy())  # ordena el dataframe
        
       
        return self.df
            

    # devuelve el df con los campos concretos, seleccionar solo algunas columnas y posiblemente tratado con  inner join / where / order by
    def visitSelectCampos(self, ctx):

        # tenemos un nombre de tabla o una variable con una tabla
        tabla_a_abrir = self.visit(ctx.taula())
        self.df = tabla_a_abrir
    
        # si hay uno o varios inner join
        for inner in ctx.innerJoin():
            self.visit(inner)

        # si hay where 
        if ctx.whereInstr() is not None:
            self.visit(ctx.whereInstr()) # filtra el dataframe con las condiciones

        # Si hay order by
        if ctx.orderBy() is not None:
            self.visit(ctx.orderBy())  # ordena el dataframe
            
        
        # filtrar los campos en el df  (seleccionar solo ciertas columnas)
        self.visit(ctx.campos())


        return self.df


    # filtra el df con el conjunto de campos que se le especifica, puede haber campos calculados o no calculados
    def visitCampos(self, ctx):
       
        # guardar las columnas que se quiere seleccionar
        columnas = []

        # mirar todos los campos que pueden haber, uno o muchos separados por comas
        for campo_ctx in ctx.campo():
            
            # Campo no calculado: mirar si existe la parte de campo no calculado (columna sola)
            if isinstance(campo_ctx, pandaQParser.CampoNoCalculadoContext):

                columna = self.visit(campo_ctx)
                columnas.append(columna)

            # Campo calculado: nos viene un campo con operaciones y un alias, creamos una nueva columna con este campo calculado
            elif isinstance(campo_ctx, pandaQParser.CampoCalculadoContext):

                columna, ali = self.visit(campo_ctx)  # nos devuelve dos parametros el campo calculado

                self.df = self.df.copy()   # para asegurarse que el df es un dataframe que no es una 'view' de otro, para evitar un warning: SettingWithCopyWarning
                
                self.df[ali] = self.df.eval(columna)

                columnas.append(ali)  # es una nueva columna


        self.df = self.df[columnas]  # actualizar el df, para que solo tenga algunas columnas
        

    # ----------- CAMPOS calculados -----------

    # retorna la expresion en formato string con los simbolos de la operacion y el alias de esa columna
    def visitCampoCalculado(self, ctx):
        columnaCalculada = self.visit(ctx.expr())
        alias = ctx.ID().getText()

        return columnaCalculada, alias
    

    def visitParentesis(self, ctx):
        return self.visit(ctx.expr())

    def visitMultiplicacio(self, ctx):
        left =  self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        return f"({left} * {right})"  # el string sin multiplicar todavia

    def visitDivisio(self, ctx):
        left =  self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        return f"({left} / {right})"

    def visitSuma(self, ctx):
        left =  self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        return f"({left} + {right})"

    def visitResta(self, ctx):
        left =  self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        return f"({left} - {right})"


    # ----------- ORDER BY -----------

    # actualiza el df para que las filas tengan el orden que se especifica
    def visitOrderBy(self, ctx):
       
        parametros = list(ctx.getChildren()) 

        columnas = []   # guardar la columnas
        ordenes =  []   # guardar el tipo orden (true significa asc)

        size = len(parametros)

        i = 1
        while i < size:
            columna = self.visit(parametros[i])   # columna indicada por el usr
            columnas.append(columna)

            # mirar si hay un orden asociado a la columna
            if (i + 1) < size and isinstance(parametros[i + 1], pandaQParser.OrdenContext):
                orden = parametros[i + 1].getText().lower()
                ordenes.append(orden == 'asc')  # lista con bools, True si es asc
                i += 3    # mover la i a la siguiente columna

            # no hay escrito el orden
            else:
                ordenes.append(True)  # por defecto ascendiente
                i += 2  # saltar la coma
   
        
        # acutalizar el datafrane, con el orden
        self.df = self.df.sort_values(by=list(columnas), ascending=list(ordenes)) 

    
    # ----------- WHERE -----------

    # solo filtrar con la condicion que se especifica
    def visitWhereSimple(self, ctx):
        llista_condicions = self.visit(ctx.cond())

        self.df = self.df[llista_condicions]  # actualizar el dataframe con las filas que hemos filtrado

    
    # caso que tenemos   where columna in (subconsulta)    hay que guardarse el dataframe original, calcular el df de la subconsulta que modifica el df
    # restaurar el df original, y filtrar las filas que tengan los valores de la columna que se especifica de la subconsulta
    def visitWhereSubquery(self, ctx):
        df_original = self.df

        columna_a_filtrar = self.visit(ctx.columna())
        
        # ejecutar la subquery, retorna el dataframe con una sola columna
        df_resultado_subquery = self.visit(ctx.subquery())

        # restaurar el df como estaba antes de la subquery, ya que este lo modifica
        self.df = df_original

        # extraer el resultado de la subquery a una lista con los valores a filtrar
        valores_filtrados = df_resultado_subquery[columna_a_filtrar].unique()

        self.df = self.df[self.df[columna_a_filtrar].isin(valores_filtrados)]  # el metodo 'isin' se usa para filtrar el dataframe basado en los valores de la subquery



    def visitParentesisCond(self, ctx):
        return self.visit(ctx.cond())

    # mirar que filas hay que filtrar y negarlo teodo
    def visitNotCond(self, ctx):
        filas_filtradas = self.visit(ctx.cond())  

        filas_filtradasNOT = ~filas_filtradas  # negamos todo

        return filas_filtradasNOT


    def visitAndCond(self, ctx):
        condicion_izq = self.visit(ctx.cond(0))
        condicion_der = self.visit(ctx.cond(1))

        return condicion_izq & condicion_der
    

    # una condicion simple, sin not ni and
    def visitSoloCond(self, ctx):
        
        return self.visit(ctx.condSimple())

    # tenemos columna = valor, donde valor puede ser numero string o otra columna  retorna las filas que cumplen
    def visitIgualCond(self, ctx):
       
        columna = self.visit(ctx.columna())
        valor = self.visit(ctx.valor())  

        filas_filtradas = self.df[columna] == valor

        return filas_filtradas
    
    
    # tenemos columna < valor, donde valor puede ser numero string o otra columna  retorna las filas que cumplen
    def visitMenorCond(self, ctx):
        columna = self.visit(ctx.columna())
        valor = self.visit(ctx.valor())  

        filas_filtradas = self.df[columna] < valor

        return filas_filtradas
       

    # leer el numero de la condicion y convertirlo a float o int
    def visitValorNum(self, ctx):
        num_string = self.visit(ctx.numero())  # el numero que esta escrito en la query
        return float(num_string) if '.' in num_string else int(num_string)
        

    def visitValorString(self, ctx):
        return self.visit(ctx.string())

    def visitValorCol(self, ctx):
        return self.visit(ctx.columna())


    # ----------- INNER JOIN -----------

    def visitInnerJoin(self, ctx):
        segunda_tabla = self.visit(ctx.taula())

        cols_condicion = self.visit(ctx.condJoin())

        tabla_juntada = pd.merge(self.df, segunda_tabla, left_on=cols_condicion[0], right_on=cols_condicion[1], how='inner') 

        self.df = tabla_juntada  # actualizar la tabla general

    # retorna el nombre de las dos columna a juntar
    def visitCondJoin(self, ctx):
        col1 = self.visit(ctx.columna(0))
        col2 = self.visit(ctx.columna(1))

        return (col1, col2)


    # ----------- PLOTS -----------

    def visitPlotNormal(self, ctx):
        nombre_variable = self.visit(ctx.var())

        # abrir la tabla, de la consulta de la variable a graficar
        if nombre_variable in st.session_state:
            tabla_var = st.session_state[nombre_variable]

            # filtrar columnas no numericas
            tabla_numerica = tabla_var.select_dtypes(include=['number'])

            if tabla_numerica.empty:
                st.write("error: la tabla no contiene valores numericos")
                return
            else:
            # graficar con streamlit
                st.line_chart(tabla_numerica)

                return tabla_numerica   # tambien muestro la tabla con los datos, esto podria ser prescindible, pero como todas las query devuelven un dataframe, lo pongo

        else:
            st.write("error: introduce una variable que contenga previamente una consulta")

    # un plot con todos los puntos separados
    def visitPlotScatter(self, ctx):
        nombre_variable = self.visit(ctx.var())

        # abrir la tabla, de la consulta de la variable a graficar
        if nombre_variable in st.session_state:
            tabla_var = st.session_state[nombre_variable]

            # filtrar columnas no numericas
            tabla_numerica = tabla_var.select_dtypes(include=['number'])

            if tabla_numerica.empty:
                st.write("error: la tabla no contiene valores numericos")
                return
            else:
            # graficar con streamlit
                st.scatter_chart(tabla_numerica)

                return tabla_numerica   # tambien muestro la tabla con los datos, esto podria ser prescindible, pero como todas las query devuelven un dataframe, lo pongo
        else:
            st.write("error: introduce una variable que contenga previamente una consulta")


    # un plot donde se muestra la area debajo el grafico
    def visitPlotArea(self, ctx):
        nombre_variable = self.visit(ctx.var())

        # abrir la tabla, de la consulta de la variable a graficar
        if nombre_variable in st.session_state:
            tabla_var = st.session_state[nombre_variable]

            # filtrar columnas no numericas
            tabla_numerica = tabla_var.select_dtypes(include=['number'])

            if tabla_numerica.empty:
                st.write("error: la tabla no contiene valores numericos")
                return
            else:
            # graficar con streamlit
                st.area_chart(tabla_numerica)

                return tabla_numerica   # tambien muestro la tabla con los datos, esto podria ser prescindible, pero como todas las query devuelven un dataframe, lo pongo
        else:
            st.write("error: introduce una variable que contenga previamente una consulta")

    # un plot de barras
    def visitPlotBar(self, ctx):
        nombre_variable = self.visit(ctx.var())

        # abrir la tabla, de la consulta de la variable a graficar
        if nombre_variable in st.session_state:
            tabla_var = st.session_state[nombre_variable]

            # filtrar columnas no numericas
            tabla_numerica = tabla_var.select_dtypes(include=['number'])

            if tabla_numerica.empty:
                st.write("error: la tabla no contiene valores numericos")
                return
            else:
            # graficar con streamlit
                st.bar_chart(tabla_numerica)

                return tabla_numerica   # tambien muestro la tabla con los datos, esto podria ser prescindible, pero como todas las query devuelven un dataframe, lo pongo
        else:
            st.write("error: introduce una variable que contenga previamente una consulta")


    # -------------------------------------

    def visitVar(self, ctx):
        return ctx.ID().getText()


    def visitTaula(self, ctx):
        nombre = ctx.ID().getText().lower()  # lower: pasa de mayusculas a minusculas por si el usuario pone el nombre en mayus

        # mirar si es una variable ya guardada, que contiene una tabla como resultado de una query
        if nombre in st.session_state:
            return st.session_state[nombre]

        # es el nombre de una tabla a abrir
        else:
            return pd.read_csv("./data/" + nombre + ".csv")


    def visitColumna(self, ctx):
        return ctx.ID().getText().lower()

    def visitNumero(self, ctx):
        return ctx.NUM().getText()

    def visitString(self, ctx):
        return ctx.ID().getText()
    




# Extra: despues de introducir la query, pulsar ctrl+enter  en vez del boton
# inicializar un session state, para luego registrar la tecla enter y que sea igual que pulsar al boton
if 'query_executed' not in st.session_state:
    st.session_state.query_executed = False

def process_query():
    
    input_stream = InputStream(query)
    lexer = pandaQLexer(input_stream)
   
    token_stream = CommonTokenStream(lexer)
    parser = pandaQParser(token_stream)
    tree = parser.root()

    if parser.getNumberOfSyntaxErrors() == 0:
        visitor = EvalPandaQVisitor()
        df = visitor.visit(tree)
        st.dataframe(df)
    else:
        st.write(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
        st.write(tree.toStringTree(recog=parser))


def update_query_executed():
    st.session_state.query_executed = True


st.title('Intèrpret PandaQ de consultes SQL\n Fet per l\'Arnau Claramunt')
query = st.text_area("Query:", height=60, key="sql_input", on_change=update_query_executed)


if st.button("Submit") or st.session_state.query_executed:  # si se pulsa el boton o enter
    process_query()
    st.session_state.query_executed = False  # resetear el state, para que no modifique cada vez, si no se pulsa boton o enter



# mostrar ejemplos de uso de consultas en SQL para el usuario
st.markdown(""" 
---
#### Ejemplo de consultas en SQL:
- Seleccionar toda la tabla:

`select * from employees;`
- Seleccionar campos especificos:

`select first_name, last_name from employees;`

---
- Seleccionar campos calculados y ponerle alias: 

`select first_name, salary, salary*1.05 as new_salary from employees;` 
- Campos calculados con parentesis:

`SELECT min_salary, max_salary, (max_salary+min_salary)*2 AS calculated_salary FROM JOBS;`

---
- Mostrar los datos ordenados, order by: (por defecto asc)

`select * from countries order by region_id, country_name desc;`

- Order by de columnas especificas:

`SELECT first_name, PHONE_NUMBER from EMPLOYEES order by first_name, phone_number ASC;`

---
- Filtrar con operaciones relacionales y booleanas, where:

`select * from countries where not region_id=1 and not region_id=3;`

---
- Inner join (juntar filas de dos tablas que cumplen la condicion del 'on'):

`select first_name, department_name from employees inner join departments on department_id=department_id;`


`select first_name, last_name, job_title, department_name from employees inner join departments on department_id=department_id inner join jobs on job_id=job_id;`

---
- Asignacion a una variable, guardar en una tabla de simbolos:

`q := select first_name, last_name, job_title, department_name from employees inner join departments on department_id=department_id inner join jobs on job_id=job_id;`

- Una vez tenemos la variable `q` con el resultado de la consulta hacer:

`select first_name, last_name from q;`

---
- Plots, primero crear una variable y luego se puede graficar:

`q := select first_name, last_name, salary, salary*1.05 as new_salary from employees where department_id=5;`

`plot q;`

- Otro ejemplo del salario minimo, maximo y la media entre los dos:

`s := select min_salary, max_salary, (min_salary+max_salary)/2 as media from jobs;`

`plot s;`

- Gráficos extra: 

`scatter s;`

`area s;`

`bar s;`

---
- Hacer subconsultas, despues del where poner in (subquery)

`select employee_id, first_name, last_name from employees where department_id in (select department_id from departments where location_id=1700) order by first_name, last_name;`

- Consulta definitiva y completa:

`select country_id, COUNTRY_NAME, city from COUNTRIES inner join locations ON country_id=country_id where location_id IN (select location_id from locations where not location_id < 1500 order by city) order by country_id ASC, city desc;`

""")