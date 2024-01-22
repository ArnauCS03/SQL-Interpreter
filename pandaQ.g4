grammar pandaQ;

root : query ';'                # querySola
     | var ':=' query ';'       # assig
     | plot ';'                 # plotInstr
     ;  


query : SELECT '*' FROM taula innerJoin* whereInstr? orderBy?          # selectAll 
      | SELECT campos FROM taula innerJoin* whereInstr? orderBy?       # selectCampos
      ;


campos : campo (',' campo)*         
       ;       
      
campo : columna                           # campoNoCalculado        
      | expr ALIAS ID                     # campoCalculado
      ;

expr  : '(' expr ')'                      # parentesis
      | expr '*' expr                     # multiplicacio
      | expr '/' expr                     # divisio
      | expr '+' expr                     # suma
      | expr '-' expr                     # resta
      | numero                            # num
      | columna                           # columnaSola
      ;



orderBy : ORDER_BY columna orden? (',' columna orden?)*
        ; 

orden : ASC | DESC ;


                 
whereInstr : WHERE cond                           # whereSimple
           | WHERE columna IN '(' subquery ')'    # whereSubquery
           ; 


cond : '(' cond ')'                 # parentesisCond 
     | NOT cond                     # notCond
     | cond AND cond                # andCond
     | condSimple                   # soloCond  
     ;
    

condSimple : columna '=' valor      # igualCond
           | columna '<' valor      # menorCond
           ;
            

valor : numero                      # valorNum
      | string                      # valorString 
      | columna                     # valorCol
      ;



innerJoin : INNER_JOIN taula ON condJoin
          ;


condJoin : columna '=' columna
         ;



subquery : query 
         ;



plot : PLOT var       # plotNormal
     | SCATTER var    # plotScatter
     | AREA var       # plotArea
     | BAR var        # plotBar
     ;


var : ID ;

taula :   ID ;
columna : ID ;
numero :  NUM ;
string :  ID ;


SELECT : ('select'|'SELECT') ;
FROM : ('from'|'FROM') ;
ALIAS : ('as'|'AS') ;

ORDER_BY : ('order by'|'ORDER BY') ;
ASC : ('asc'|'ASC') ; 
DESC : ('desc'|'DESC') ;

WHERE : ('where'|'WHERE') ;
NOT : ('not'|'NOT') ;
AND : ('and'|'AND') ;

INNER_JOIN : ('inner join'|'INNER JOIN') ;
ON : ('on'|'ON') ;

PLOT : ('plot'|'PLOT') ;
IN : ('in'|'IN') ;
SCATTER : ('scatter'|'SCATTER') ;
AREA : ('area'|'AREA') ;
BAR : ('bar'|'BAR') ;


ID :  [a-zA-Z_]+ ;
NUM : [0-9]+ ('.' [0-9]+)? ; // int o float
WS  : [ \t\n\r]+ -> skip ;