"""Práctica 1 Obligatoria PRPA
   Cecilia Sánchez Plaza"""

from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore
from multiprocessing import current_process
from multiprocessing import Array
from time import sleep
import random

NPROD = 4 #Número de productores
N = 4  #Número de números que produce cada productor


def delay(factor = 3):
    sleep(3/factor)    

def add_data(almacen,data,posicion):
    """Esta función añade al almacen un numero en la posicion que queremos"""
    almacen[posicion] = data 
    delay(6)
   

def get_data(almacen):
    
    """Esta función toma el mínimo valor del almacen y devuelve la tupla 
    formada por dicho valor y su posción en la lista """
    
    lista_valores= [ (x ,i) for x in almacen for i in range(len(almacen))
                    if x!=-1 and almacen[i]==x ]
    #crea una lista con los valores del almacén distintos de -1, y sus posiciones
    if lista_valores!=[]:
        data=list(min(lista_valores)) #nos quedamos con el mínimo
    else:
        data = [10*(N+2),0]
    
    return (data) 


def producer(almacen, empty, non_empty, posicion):
    cota = 1
    for i in range(N): 
        numero = random.randint(cota,10*(i+2)) #la cota se va actualizando para que los números que produce cada
                                               # productor sean mayores o iguales que el anterior
        empty.acquire() #Esperar a que se haya cogido el número de ese productor
        add_data(almacen,numero, posicion) #Se añade 'numero' al almacen en la posicion adecuada
        print (f"Productor {current_process().name} almacena el {numero}")
        delay(6)
        non_empty.release() #Avisa de que ya se ha almacenado 
        cota=numero
    
    empty.acquire()
    add_data(almacen,-1, posicion) #Se añade un -1 cuando el productor ya ha producido sus N números
    non_empty.release()
   
def consumer(almacen, empty, non_empty, lista_final):
    for i in range(NPROD): #Esperar a que todos los productores hayan añadido un numero al almacen
        non_empty[i].acquire()
    while (len(lista_final)!=(NPROD*N)): 
       
        dato , pos = get_data(almacen) #nos quedamos con el menor numero del almacen
        lista_final += [dato] #se lo añadimos a la lista final
       
        print (f"{current_process().name} elige entre", almacen[:],"y coge el dato del productor",pos,". Lista actualizada:", lista_final)
        delay(6)
        almacen[pos]=-2 #cuando se retira un numero se escribe un -2 en su lugar
        print("almacen:" , almacen[:])
        empty[pos].release() #Avisamos de que ya puede producir al productor del numero que acabamos de retirar
        
        non_empty[pos].acquire() #y esperamos a que se vuelva a llenar esa posicion
        delay()
    print("Lista final ordenada:",lista_final) 

def main():
    almacen = Array('i', NPROD) 
    for i in range(NPROD):
        almacen[i] = -2  #el almacen inicial es de -2's
    print ("almacen inicial:", almacen[:])
    
    lista_final=[]
    
    non_empty=[Semaphore(0) for i in range(NPROD)]  
    empty=[BoundedSemaphore(1) for i in range(NPROD)]  

    prodlst = [ Process(target=producer,
                        name=f'{i}',
                        args=(almacen, empty[i], non_empty[i],i))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                      name="consumidor",
                      args=(almacen, empty, non_empty,lista_final))]

    for p in  conslst + prodlst:
        p.start()

    for p in prodlst + conslst:
        p.join()


if __name__ == '__main__':
    main()