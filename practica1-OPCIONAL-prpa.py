"""Práctica 1 Parte OPCIONAL PRPA
   Cecilia Sánchez PLaza"""

from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint


NPROD = 4 #Número de Productores
N = 8   #Número de números que produce cada productor
K = 4 #Tamaño del almacen de cada productor

"""La diferencia de esta parte con respecto a la anterior es que antes cada productor producía un solo elemento 
cada vez, y no volvía a producir hasta que su numero hubiera sido consumido por el consumidor. Aquí en cambio
cada productor tiene un almacen propio donde puede acumular hasta K numeros a la vez. Almacena numeros de 
forma creciente de manera que el consumidor cuando vaya a elegir, solo compare los primeros elementos de 
los NPROD almacenes, ya que los primeros serán los mínimos de cada almacen. Cuando un numero es consumido, 
el resto de numeros de ese almacen bajan una posicion, es decir se desplazan hacia la izquierda en el almacen.
Las funciones que usamos son las mismas, add_data, get_data, producer y consumer. En esta parte opcional
añadimos un Lock (mutex) para asegurarnos de que no se quitan o se añaden a la vez dos elementos"""


def delay(factor = 3):
    sleep(3/factor)


def add_data(almacen, data, index, mutex):
    """Esta función añade al almacen un numero en la posicion que queremos"""
    mutex.acquire()
    try:
        almacen[index.value] = data
        index.value = index.value + 1
        delay(15)
    finally:
        mutex.release()


def get_data(almacen, index, mutex):
    """Esta función toma el primer valor del almacen, mueve los restantes valores hacia la izquierda
    y devuelve dicho primer valor"""
    mutex.acquire()
    try:
        data = almacen[0]
        index.value = index.value - 1
        delay()
        for i in range(index.value):
            almacen[i] = almacen[i + 1] #movemos los valores una posicion a la izquierda
        almacen[index.value] = -2 #en la posicion que se ha quedado vacía metemos un -2
    finally:
        mutex.release()
    return data


def producer(almacen, empty, non_empty, index, mutex):
    
    cota=1
    for i in range(N):
        numero=randint(cota,10*(i+2)) #la cota se va actualizando para que los números que produce cada
                                      #productor sean mayores o iguales que el anterior
        empty.acquire()
        add_data(almacen, numero, index, mutex)
        print (f"Productor {current_process().name} almacena el {numero}. Lleva {i+1} veces (le quedan {N-i-1})")
        non_empty.release()
        cota=numero
        
    empty.acquire()
    add_data(almacen, -1 , index, mutex) #Se añade un -1 cuando el productor ya ha producido sus N números
    non_empty.release()
    print (f"¡El productor {current_process().name} ha terminado!")


def consumer(almacen_general, index, empty, non_empty, mutex, lista_final):
    cont=0
    while (cont < N*NPROD):
        for i in range(NPROD):
            non_empty[i].acquire()  #esperamos a que todos los productores hayan producido
            non_empty[i].release()  #al menos una vez, pueden producir más (hasta K)
            
        minimo = almacen_general[0][0] #tomamos el primer elemento del primer almacen
        pos=0
        j=0
        while (minimo==-1) and j<NPROD:  #si es -1 y no es el último almacen, nos pasamos al siguiente almacen
            minimo=almacen_general[j][0]
            pos=j
            j+=1
        if minimo == -1: #si es -1 ya en el útimo almacen hemos terminado
            break
        else:
            for j in range(pos, NPROD):
                if ((almacen_general[j][0]<minimo) and (almacen_general[j][0]!=-1)):
                    minimo=almacen_general[j][0]   #nos quedamos con el menor primer elemento
                    pos=j
            non_empty[pos].acquire() #esperamos a que el almacen correspondiente haya producido
            
            dato =get_data(almacen_general[pos], index[pos], mutex[pos]) 
            
            print (f"\nCONSUMIDOR:: Se consume el dato del productor {pos} que es: {dato} \n")
            delay(15)
            empty[pos].release() #avisamos al productor de que ya hemos cogido el numero
            
            lista_final[cont] = dato #vamos añadiendo los datos que cogemos a la lista final
        cont+=1
    
    print("La lista final ordenada:", [elem for elem in lista_final])
    
       

def main():

    #Creamos un almacén general que contenga el almacen de cada productor:
    almacen_general = [ Array('i', K) for j in range(NPROD)]
    for i in range(NPROD):
        for j in range(K):
            almacen_general[i][j] = -2  #los iniciamos con -2's
    
    for i in range(NPROD):
        print(f"almacen inicial del productor {i}: ",almacen_general[i][:] )
        
    #Creamos una lista de tamaño NPROD que guarde la posicion en la que cada productor debe añadir un nuevo dato
    indices=[Value('i', 0) for j in range(NPROD)]
    
    #La lista que recibiremos al final con todos los valores ordenados:
    lista_final = Array('i', NPROD*N)
    
    
    #Creamos 3 listas, cada una con NPROD semáforos dentro correspondientes a cada productor.
    #La primera es equivalente al non_empty de la parte obligatoria, la segunda equivalente
    #al empty (pero esta vez con BoundedSemaphore(K) en vez de (1) por el tamaño de los almacenes
    #de cada productor), y la tercera es el mutex:
    
    non_empty=[Semaphore(0) for j in range(NPROD)]
    empty=[BoundedSemaphore(K) for j in range(NPROD)]
    mutex=[Lock() for j in range(NPROD)]
    
    
   
    prodlst = [ Process(target=producer,
                        name=f'{i}',
                        args=(almacen_general[i], empty[i], non_empty[i], indices[i], mutex[i]))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                      name="consumidor",
                      args=(almacen_general, indices, empty, non_empty, mutex, lista_final))]
                

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()


if __name__ == '__main__':
    main()
