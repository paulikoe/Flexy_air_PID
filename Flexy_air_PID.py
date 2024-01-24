import serial
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import datetime as dt

ser = serial.Serial('COM7',115200)
time.sleep(5)


ser.write("<P:1>") #turning on the stream of data
ser.write("<L:0>") #simple exponential smoothing filter
#z = ser.write("<F:0>")
#print(x)

'''
Nastavení žádané hodnoty uživatelem
'''
setpoint = 0
while not setpoint in range(100,300):
    set = input("Write number between 100-300: ")
    try:
        setpoint = int(set)
            
        if setpoint < 100:
            print("Write bigger number")
                
        elif setpoint > 300:
            print("Write smaller number")
            
                
    except:  
        pass
t = 0.1
ser.write("<S:10>") #sampling rate (frequency)
u_p = 0

'''
Diskrítní PID regulátor - odchylkový tvar
'''

def PID (KP,KI,KD, setpoint, dist):
    q0 = -KP * (1 + t / (2 * KI) + KD / t) #aby nedocházelo k dělení nulou
    q1 = KP * (1- t  / (2 * KI) + 2 * KD / t)
    q2 = -KP * KD / t
    #print(q0,q1,q2)
    u = u_p - (q0 + q1 + q2) * setpoint + q0 * dist[0] + q1 * dist[-1] + q2 * dist[-2] #TODO podívat se na hodnoty v závorkách
    return u

'''
Vykreslení obrazu
'''
plt.ion()
xs = np.linspace(0, 355, 355) #hodnoty do vykresleného grafu
ys = np.linspace(0, 355, 355)
i = 0    
initialized = False
dist = [0,0] #pro první hodnotu, aby tam byly předchozí dvě hodnoty zadané
fig = plt.figure()
ax = fig.add_subplot(111)
line1, = ax.plot(xs, ys, 'r-') #
y = [0] * len(xs) # nadefinovaných prvních x hodnot jako zeros

'''
# Vybere se posledních n hodnot z posloupnosti y
'''
def vyber (y, n):
    
    return y[-n:]


while True:

    '''
    Získání hodnot výšky "plováku" ze senzoru
    '''
    x = ser.readline()
    str = x.decode('utf-8') #Převede binární řetězec x na řetězec v Unicode s pomocí dekódování UTF-8.
    c = str.split(',') # Rozdělí řetězec str na seznam podřetězců podle čárky
    if len(c) >= 3:
        dist_v = c[2].strip() #Získává třetí část (index 2) ze seznamu c
        #strip - odstranění případných bílých znaků
        dist_va = float(dist_v) # Převede řetězec na desetinné číslo
        dist.append(dist_va) 
        dist = dist[-3:]  # Keep only the last three values
        distance_print = dist[1]

    '''
    Konstanty diskrétního PID regulátoru, odchylkový tvar, (KP, KI a KD) jsou buď nastaveny uživatelským vstupem,
    nebo jsou použity výchozí hodnoty, pokud uživatel nezadává vlastní.
    '''
    if not initialized:
        konst = input("Chcete použít vlastní konstanty? (A)NO or (N)E ")

        if konst == "A":
            KP, KI, KD = map(float, input("Zadej hodnotu KP, KI, KD oddělené mezerou: ").split())
            u = PID(KP = KP,KI = KI, KD = KD,setpoint = setpoint, dist = dist)

        elif konst == "N":
            u = PID(KP = 0.1, KI = 1, KD = 1, setpoint = setpoint, dist = dist) # 3; 3; 2 .. pokud dam KI > 3 - odleti to pryc, mensi naopak nic nedela
            KP = 0.0001
            KI = 0.15
            KD = 0.1
    initialized = True

    u = PID(KP = KP,KI = KI, KD = KD,setpoint = setpoint, dist = dist)
    #print(u)
    u = max(0,u) 
    u = min(1,u)
    k = int(u*255) #max
    #print(k)
    #print(u)
    ser.write(f"<F:{k}>")
    u_p = u #tyto promenne vyhodin ven z funkce a pak je tam zase poslat
    
    '''
    Aktualizace hodnoty výšky 
    '''
    y.append(distance_print)
    
    if i % 15 == 0:
        data_zobrazeni = vyber(y,len(xs)) #vložení posledních xs hodnot z polynomu y
        line1.set_ydata(data_zobrazeni)
        fig.canvas.draw()
        fig.canvas.flush_events()
       
    
    i = i+1
    


#neomezovat akční zásah, ale paměť

        
