import pandas as pd
from random import random, seed
from math import exp, sqrt, floor
from matplotlib.pyplot import plot, show

def normalizar(r, lb, ub):
    return (r - lb) / (ub - lb)

def desnormalizar(n, lb, ub):
    return n * (ub - lb) + lb

def maxp(V):
    val, pos = V[0], 0
    for i, e in enumerate(V):
        if e > val:
            val, pos = e, i
    return val, pos

def minp(V):
    val, pos = V[0], 0
    for i, e in enumerate(V):
        if e < val:
            val, pos = e, i
    return val, pos

def calcD(V1, V2):
    return sqrt(sum((v1 - v2) ** 2 for v1, v2 in zip(V1, V2)))

def fa(x):
    x = min(20, max(-20, x))
    return 1 / (1 + exp(-x))

def fad(x):
    return fa(x) * (1 - fa(x))

def RandomWeights(TINP, TMID, TOUT):
    seed(0)  # Para reproducibilidad
    m = [[random() - 0.5 for _ in range(TINP)] for _ in range(TMID)]
    o = [[random() - 0.5 for _ in range(TMID)] for _ in range(TOUT)]
    ma = [[random() - 0.5 for _ in range(TINP)] for _ in range(TMID)]
    oa = [[random() - 0.5 for _ in range(TMID)] for _ in range(TOUT)]
    return m, ma, o, oa

def ForwardBKG(VI, m, o):
    TMID, TINP, TOUT = len(m), len(m[0]), len(o)
    netm = [sum(m[y][x] * VI[x] for x in range(TINP)) for y in range(TMID)]
    sm = [fa(netm[y]) for y in range(TMID)]
    neto = [sum(o[z][y] * sm[y] for y in range(TMID)) for z in range(TOUT)]
    so = [fa(neto[z]) for z in range(TOUT)]
    return sm, so, neto, netm

def BackwardBKG(DO, netm, m, o, so, neto):
    TMID, TOUT = len(m), len(o)
    eo = [(DO[z] - so[z]) * fad(neto[z]) for z in range(TOUT)]
    em = [fad(netm[y]) * sum(eo[z] * o[z][y] for z in range(TOUT)) for y in range(TMID)]
    return em, eo

def LearningBKG(VI, m, ma, sm, em, o, oa, eo, ETA, ALPHA):
    TMID, TINP, TOUT = len(m), len(m[0]), len(o)
    for z in range(TOUT):
        for y in range(TMID):
            o[z][y] += ETA * eo[z] * sm[y] + ALPHA * oa[z][y]
            oa[z][y] = ETA * eo[z] * sm[y]
    for y in range(TMID):
        for x in range(TINP):
            m[y][x] += ETA * em[y] * VI[x] + ALPHA * ma[y][x]
            ma[y][x] = ETA * em[y] * VI[x]
    return m, ma, o, oa

def DatabaseRead():
    print("Leyendo el archivo Excel...")
    df = pd.read_excel("C:/Users/ASUS/Desktop/datasetNN.xls")  # Ajusta la ruta según la ubicación real del archivo
    return df.values.tolist()

def NormalData(DataExp):
    Trows, Tcols = len(DataExp), len(DataExp[0])
    V = [0 for _ in range(Trows)]
    MRange = [[0 for _ in range(2)] for _ in range(Tcols)]
    DataNorm = [[0 for _ in range(Tcols)] for _ in range(Trows)]
    for c in range(Tcols):
        for r in range(Trows):
            V[r] = DataExp[r][c]
        valmax, _ = maxp(V)
        valmin, _ = minp(V)
        for r in range(Trows):
            DataNorm[r][c] = normalizar(DataExp[r][c], valmin, valmax)
        MRange[c][0] = valmin
        MRange[c][1] = valmax
    return DataNorm, MRange

def scrambling(DataBase):
    Trows = len(DataBase)
    DataBaseS = DataBase[:]
    for _ in range(Trows * 10):
        pos1, pos2 = floor(random() * Trows), floor(random() * Trows)
        DataBaseS[pos1], DataBaseS[pos2] = DataBaseS[pos2], DataBaseS[pos1]
    return DataBaseS

def GenTrainVal(DataExp, percent):
    DataBaseS = scrambling(DataExp)
    Trows, Tcols = len(DataBaseS), len(DataBaseS[0])
    DataTrain = [DataBaseS[dd] for dd in range(Trows - floor(Trows * percent))]
    DataVal = [DataBaseS[dd] for dd in range(Trows - floor(Trows * percent), Trows)]
    return DataTrain, DataVal

def TrainingNNBKni10(NTEpochs, DataTrain):
    TData, Tcols = len(DataTrain), len(DataTrain[0])
    TINP, TMID, TOUT = Tcols, 5, 1
    ETA, ALPHA = 0.25, 0.125
    m, ma, o, oa = RandomWeights(TINP, TMID, TOUT)
    Errg, emin = [0 for _ in range(NTEpochs)], 1e10
    VI = [0 for _ in range(TINP)]
    print("Entrenando la red neuronal...")
    for epochs in range(NTEpochs):
        DataTrain = scrambling(DataTrain)
        etotal = 0
        for data in range(TData):
            for ii in range(TINP):
                VI[ii] = DataTrain[data][ii]
            VI[TINP - 1] = 1  # Bias
            DO = [DataTrain[data][Tcols - 1]]
            sm, so, neto, netm = ForwardBKG(VI, m, o)
            em, eo = BackwardBKG(DO, netm, m, o, so, neto)
            m, ma, o, oa = LearningBKG(VI, m, ma, sm, em, o, oa, eo, ETA, ALPHA)
            etotal += eo[0] * eo[0]
        errcm = 0.5 * sqrt(etotal)
        if errcm < emin:
            emin = errcm
        Errg[epochs] = emin
        if epochs % 100 == 0:
            print(f"Epoch {epochs}, Error: {errcm}")
    return Errg, m, o

def SetDatabases():
    print("Estableciendo las bases de datos...")
    DataBrute = DatabaseRead()
    DataNorm, MRange = NormalData(DataBrute)
    DataTrain, DataVal = GenTrainVal(DataNorm, 0.2)
    return DataTrain, DataVal

def ValidationNNBKni10(DataVal, m, o):
    TData, Tcols = len(DataVal), len(DataVal[0])
    TINP, TMID, TOUT = len(m[0]), len(m), 1
    Ynn = [[0 for _ in range(2)] for _ in range(TData)]
    VI = [0 for _ in range(TINP)]
    for data in range(TData):
        for ii in range(TINP):
            VI[ii] = DataVal[data][ii]
        VI[TINP - 1] = 1  # Bias
        DO = [DataVal[data][Tcols - 1]]
        sm, so, neto, netm = ForwardBKG(VI, m, o)
        Ynn[data][0] = DO[0]
        Ynn[data][1] = so[0]
    return Ynn

def usennbk(X, MRange, m, o):
    TINP = len(X)
    Xn = [normalizar(X[i], MRange[i][0], MRange[i][1]) for i in range(TINP)] + [1]
    sm, so, neto, netm = ForwardBKG(Xn, m, o)
    R = desnormalizar(so[0], MRange[2][0], MRange[2][1])
    return R

# Entrenamiento y validación de la red neuronal
DataTrain, DataVal = SetDatabases()
Errg, m, o = TrainingNNBKni10(1000, DataTrain)
Ynn = ValidationNNBKni10(DataVal, m, o)

# Gráfica del error de entrenamiento
plot(Errg)
show()

# Resultados de la validación
print("Valores reales vs. valores predichos:")
for real, pred in Ynn:
    print(f"Real: {real}, Predicho: {pred}")

# Imprimir los pesos
print("\nPesos de la capa oculta (m):")
for fila in m:
    print(fila)

print("\nPesos de la capa de salida (o):")
for fila in o:
    print(fila)
